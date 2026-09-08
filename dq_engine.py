"""
dq_engine.py

Central engine that executes the DQ controls (the brief's "Data Quality Engine").

Responsibilities (section 4.1 of the use case):
  - execute multiple control types
  - apply the rules dynamically, whatever the dataset
  - produce structured, reproducible outputs
  - generate a complete Evidence Pack per run (Appendix B)

Per run, evidence/<run_id>/ holds (Appendix B.2):
  - run_summary.json     : run id, timestamps, catalogue/config hashes, per-rule
                           results, and a hash chained from the previous run
  - <rule>_result.json   : per-rule status, metrics, config snapshot, resolved
                           execution parameters, dataset reference (hash)
  - <rule>_exceptions.csv : detailed failing records
  - snapshots/<name>.csv  : an exact copy of every input dataset used
  - system_trace.json     : engine / Python / library versions, host, file
                            hashes, and the control function run per rule
  - run_log.jsonl + run.log : ordered processing steps

evidence/runs_ledger.jsonl chains every run (previous_run_hash -> run_hash),
so the run history is append-only and tamper-evident.

Run:   python dq_engine.py
Verify:python dq_engine.py --verify <run_id>
       (re-executes the stored rule config against the stored dataset
        snapshots and asserts identical results -- Appendix B.3 / section 7.3)
"""
from __future__ import annotations
import ast
import hashlib
import json
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

import controls as _controls_module
from connectors import SourceUnavailable, load_source
from controls import CONTROL_REGISTRY

ENGINE_VERSION = "1.0"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _dataset_hash(df: pd.DataFrame) -> str:
    """Deterministic fingerprint of the dataset content (traceability / evidence)."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()[:16]


def _file_hash(path) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except Exception:
        return ""


def _parse_params(raw) -> dict:
    """Catalogue params column -> dict. JSON first, Python literal as a fallback."""
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        try:
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return {}


def _rule_is_active(rule: pd.Series) -> bool:
    """The catalogue can retire a rule without deleting it (active=FALSE column)."""
    return str(rule.get("active", "TRUE")).strip().upper() not in ("FALSE", "0", "NO", "N")


def _threshold_pct(rule: pd.Series):
    """Tolerance threshold (%): below it, the control passes despite anomalies."""
    raw = rule.get("threshold_pct")
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(val) or val < 0 else val


def _apply_threshold(outcome: dict, threshold_pct) -> dict:
    """Turn a FAIL into a PASS when the anomaly rate stays under threshold_pct.
    Shared by execution and by verification so both compute status identically."""
    try:
        tp = float(threshold_pct)
        if pd.isna(tp) or tp < 0:
            tp = None
    except (TypeError, ValueError):
        tp = None
    if tp is not None:
        total = outcome["metrics"].get("total_records") or 0
        exc_pct = round(100 * len(outcome["exceptions"]) / total, 2) if total else 0.0
        outcome["metrics"]["exception_pct"] = exc_pct
        outcome["metrics"]["threshold_pct"] = tp
        if outcome["status"] == "FAIL" and exc_pct <= tp:
            outcome["status"] = "PASS"
            outcome["metrics"]["within_threshold"] = True
    return outcome


def _resolve_execution_parameters(control_type: str, params: dict, threshold_pct) -> dict:
    """The effective parameters actually applied (Appendix B.2 'Execution Parameters')."""
    resolved = dict(params)
    resolved["threshold_pct"] = threshold_pct
    if control_type == "Timeliness":
        rd = params.get("reference_date", "today")
        resolved["reference_date"] = rd
        if rd == "today":
            resolved["reference_date_resolved"] = pd.Timestamp.today().normalize().date().isoformat()
    if control_type == "Reconciliation":
        resolved["tolerance_pct"] = params.get("tolerance_pct")
    return resolved


def _lib_version(mod_name: str) -> str:
    try:
        return getattr(__import__(mod_name), "__version__", "unknown")
    except Exception:
        return "not installed"


class RunLog:
    """Ordered processing-step log: machine-readable JSONL + a plain-text mirror."""

    def __init__(self, run_dir: Path):
        self._j = (run_dir / "run_log.jsonl").open("w", encoding="utf-8")
        self._t = (run_dir / "run.log").open("w", encoding="utf-8")

    def log(self, event: str, **kw) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        self._j.write(json.dumps({"ts": ts, "event": event, **kw}, default=str) + "\n")
        extra = "  ".join(f"{k}={v}" for k, v in kw.items())
        self._t.write(f"{ts}  {event:16s}  {extra}\n")
        self._j.flush()
        self._t.flush()

    def close(self) -> None:
        self._j.close()
        self._t.close()


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------
class DQEngine:
    def __init__(self, catalogue_path: str, datasets_config_path: str, evidence_dir: str = "evidence"):
        self.catalogue_path = catalogue_path
        self.datasets_config_path = datasets_config_path
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        self.root = Path(datasets_config_path).resolve().parent
        self.catalogue = pd.read_csv(catalogue_path)
        with open(datasets_config_path) as f:
            self.datasets_config = yaml.safe_load(f) or {}

        self._dataset_cache: dict[str, pd.DataFrame] = {}
        self._dataset_hash_cache: dict[str, str] = {}
        self._run_dir: Path | None = None
        self._log: RunLog | None = None

    # -- datasets ---------------------------------------------------------
    def _get_dataset(self, name: str) -> pd.DataFrame:
        if name not in self._dataset_cache:
            df = load_source(name, self.datasets_config, self.root)
            self._dataset_cache[name] = df
            h = _dataset_hash(df)
            self._dataset_hash_cache[name] = h
            if self._run_dir is not None:
                df.to_csv(self._run_dir / "snapshots" / f"{name}.csv", index=False)
                if self._log:
                    self._log.log("dataset_loaded", dataset=name, rows=len(df),
                                  columns=len(df.columns), hash=h,
                                  snapshot=f"snapshots/{name}.csv")
        return self._dataset_cache[name]

    # -- run ------------------------------------------------------------
    def run(self) -> dict:
        run_id = str(uuid.uuid4())
        run_ts = datetime.now(timezone.utc).isoformat()
        run_dir = self.evidence_dir / run_id
        (run_dir / "snapshots").mkdir(parents=True, exist_ok=True)

        self._run_dir = run_dir
        self._log = RunLog(run_dir)
        self._log.log("run_start", run_id=run_id, engine_version=ENGINE_VERSION,
                      catalogue=str(self.catalogue_path))

        rule_results = []
        controls_used: dict[str, str] = {}
        for _, rule in self.catalogue.iterrows():
            if not _rule_is_active(rule):
                self._log.log("rule_skipped", rule_id=rule["rule_id"], reason="inactive")
                continue
            rec = self._execute_rule(rule, run_id, run_ts, run_dir)
            rule_results.append(rec)
            controls_used[rec["rule_id"]] = rec.get("control_function", rec["control_type"])

        trace = self._system_trace(controls_used)
        (run_dir / "system_trace.json").write_text(json.dumps(trace, indent=2, default=str))
        self._log.log("system_trace_written")

        run_summary = {
            "run_id": run_id,
            "run_timestamp_utc": run_ts,
            "engine_version": ENGINE_VERSION,
            "catalogue_source": str(self.catalogue_path),
            "catalogue_version_hash": _file_hash(self.catalogue_path),
            "datasets_config_hash": _file_hash(self.datasets_config_path),
            "rules_executed": len(rule_results),
            "dataset_snapshots": sorted(p.name for p in (run_dir / "snapshots").glob("*.csv")),
            "results": rule_results,
        }
        prev_hash = self._last_ledger_hash()
        run_summary["previous_run_hash"] = prev_hash
        payload = json.dumps({k: v for k, v in run_summary.items() if k != "previous_run_hash"},
                             sort_keys=True, default=str).encode()
        run_summary["run_hash"] = hashlib.sha256(prev_hash.encode() + payload).hexdigest()[:16]

        (run_dir / "run_summary.json").write_text(json.dumps(run_summary, indent=2, default=str))
        self._append_ledger(run_summary)
        self._log.log("run_complete", rules=len(rule_results), run_hash=run_summary["run_hash"])
        self._log.close()
        self._run_dir = None
        self._log = None
        return run_summary

    # -- per-rule -----------------------------------------------------
    def _error_record(self, rule: pd.Series, run_id: str, run_ts: str,
                      run_dir: Path, message: str) -> dict:
        """A rule whose data source / control type is unavailable does not crash the
        run: it produces an ERROR record and execution continues (section 7.3)."""
        record = {
            "run_id": run_id,
            "execution_timestamp_utc": run_ts,
            "rule_id": rule["rule_id"],
            "control_name": rule["control_name"],
            "control_type": rule["control_type"],
            "control_function": None,
            "severity": rule["severity"],
            "owner": rule["owner"],
            "dataset_reference": {},
            "rule_configuration_snapshot": {
                "dataset_scope": rule["dataset_scope"],
                "ref_dataset_scope": rule.get("ref_dataset_scope"),
                "params": _parse_params(rule.get("params")),
                "threshold_pct": _threshold_pct(rule),
            },
            "execution_parameters": {},
            "status": "ERROR",
            "error": message,
            "metrics": {},
            "exception_count": 0,
            "exceptions_evidence_path": None,
        }
        with open(run_dir / f"{rule['rule_id']}_result.json", "w") as f:
            json.dump(record, f, indent=2, default=str)
        if self._log:
            self._log.log("rule_error", rule_id=rule["rule_id"], error=message)
        return record

    def _execute_rule(self, rule: pd.Series, run_id: str, run_ts: str, run_dir: Path) -> dict:
        rule_id = rule["rule_id"]
        control_type = rule["control_type"]
        params = _parse_params(rule["params"])
        if self._log:
            self._log.log("rule_start", rule_id=rule_id, control_type=control_type)

        control_fn = CONTROL_REGISTRY.get(control_type)
        if control_fn is None:
            return self._error_record(rule, run_id, run_ts, run_dir,
                                      f"Unknown control type: {control_type}")

        ref_scope = rule.get("ref_dataset_scope")
        has_ref = isinstance(ref_scope, str) and ref_scope.strip()
        try:
            df = self._get_dataset(rule["dataset_scope"])
            call_kwargs = dict(params)
            if has_ref:
                call_kwargs["ref_df"] = self._get_dataset(ref_scope)
        except SourceUnavailable as exc:
            return self._error_record(rule, run_id, run_ts, run_dir, str(exc))

        outcome = control_fn(df, **call_kwargs)
        threshold_pct = _threshold_pct(rule)
        _apply_threshold(outcome, threshold_pct)

        exceptions_rel = None
        if not outcome["exceptions"].empty:
            exceptions_rel = f"{rule_id}_exceptions.csv"
            outcome["exceptions"].to_csv(run_dir / exceptions_rel, index=False)

        dataset_refs = {rule["dataset_scope"]: self._dataset_hash_cache[rule["dataset_scope"]]}
        if has_ref:
            dataset_refs[ref_scope] = self._dataset_hash_cache[ref_scope]

        result_record = {
            "run_id": run_id,
            "execution_timestamp_utc": run_ts,
            "rule_id": rule_id,
            "control_name": rule["control_name"],
            "control_type": control_type,
            "control_function": control_fn.__name__,
            "severity": rule["severity"],
            "owner": rule["owner"],
            "dataset_reference": dataset_refs,
            "rule_configuration_snapshot": {
                "dataset_scope": rule["dataset_scope"],
                "ref_dataset_scope": ref_scope if has_ref else None,
                "params": params,
                "threshold_pct": threshold_pct,
            },
            "execution_parameters": _resolve_execution_parameters(control_type, params, threshold_pct),
            "status": outcome["status"],
            "metrics": outcome["metrics"],
            "exception_count": int(len(outcome["exceptions"])),
            "exceptions_evidence_path": exceptions_rel,
        }
        with open(run_dir / f"{rule_id}_result.json", "w") as f:
            json.dump(result_record, f, indent=2, default=str)
        if self._log:
            self._log.log("rule_done", rule_id=rule_id, status=outcome["status"],
                          exceptions=result_record["exception_count"])
        return result_record

    # -- trace + ledger --------------------------------------------
    def _system_trace(self, controls_used: dict) -> dict:
        return {
            "engine_version": ENGINE_VERSION,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "host": platform.node(),
            "libraries": {
                "pandas": _lib_version("pandas"),
                "pyyaml": _lib_version("yaml"),
                "openpyxl": _lib_version("openpyxl"),
            },
            "catalogue": {"path": str(self.catalogue_path), "sha256_16": _file_hash(self.catalogue_path)},
            "datasets_config": {"path": str(self.datasets_config_path),
                                "sha256_16": _file_hash(self.datasets_config_path)},
            "controls_module": {"path": _controls_module.__file__,
                                "sha256_16": _file_hash(_controls_module.__file__)},
            "controls_used": controls_used,
            "retention_note": "prototype: local mutable evidence files; production would use "
                              "versioned WORM storage (S3 Object Lock / data lake).",
        }

    def _last_ledger_hash(self) -> str:
        ledger = self.evidence_dir / "runs_ledger.jsonl"
        if not ledger.exists():
            return ""
        lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            return ""
        try:
            return json.loads(lines[-1]).get("run_hash", "")
        except ValueError:
            return ""

    def _append_ledger(self, run_summary: dict) -> None:
        counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
        for r in run_summary["results"]:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        entry = {
            "run_id": run_summary["run_id"],
            "timestamp": run_summary["run_timestamp_utc"],
            "engine_version": run_summary["engine_version"],
            "catalogue_version_hash": run_summary["catalogue_version_hash"],
            "rules_executed": run_summary["rules_executed"],
            "counts": counts,
            "previous_run_hash": run_summary["previous_run_hash"],
            "run_hash": run_summary["run_hash"],
        }
        with (self.evidence_dir / "runs_ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")


# --------------------------------------------------------------------------
# Independent verification (section 7.3 / Appendix B.3)
# --------------------------------------------------------------------------
def verify_run(evidence_dir, run_id: str) -> dict:
    """Re-execute the stored rule configuration of a past run against its stored
    dataset snapshots and assert that status + exception counts still match.
    Writes evidence/<run_id>/verification.json and returns the report."""
    run_dir = Path(evidence_dir) / run_id
    summary = json.loads((run_dir / "run_summary.json").read_text())
    snap_dir = run_dir / "snapshots"
    checks = []

    for res in summary.get("results", []):
        rid = res["rule_id"]
        expected_status = res["status"]
        expected_exc = res.get("exception_count", 0)
        snap = res.get("rule_configuration_snapshot", {})

        if expected_status == "ERROR":
            checks.append({"rule_id": rid, "expected": "ERROR", "recomputed": "ERROR",
                           "match": True, "note": "error record, not re-executed"})
            continue

        fn = CONTROL_REGISTRY.get(res["control_type"])
        ds = snap.get("dataset_scope")
        ds_snap = snap_dir / f"{ds}.csv"
        if fn is None or not ds_snap.exists():
            checks.append({"rule_id": rid, "expected": expected_status, "recomputed": "N/A",
                           "match": False, "note": "control function or dataset snapshot missing"})
            continue

        df = pd.read_csv(ds_snap)
        kwargs = dict(snap.get("params") or {})
        ref = snap.get("ref_dataset_scope")
        if ref and str(ref) not in ("", "nan", "None", "NaN"):
            ref_snap = snap_dir / f"{ref}.csv"
            if ref_snap.exists():
                kwargs["ref_df"] = pd.read_csv(ref_snap)
        try:
            outcome = fn(df, **kwargs)
        except Exception as exc:
            checks.append({"rule_id": rid, "expected": expected_status,
                           "recomputed": f"EXCEPTION: {exc}", "match": False})
            continue

        _apply_threshold(outcome, snap.get("threshold_pct"))
        got_exc = int(len(outcome["exceptions"]))
        checks.append({
            "rule_id": rid,
            "expected": expected_status, "recomputed": outcome["status"],
            "expected_exceptions": expected_exc, "recomputed_exceptions": got_exc,
            "match": outcome["status"] == expected_status and got_exc == expected_exc,
        })

    report = {
        "run_id": run_id,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "method": "re-execute stored rule config against stored dataset snapshots",
        "run_hash": summary.get("run_hash"),
        "all_match": all(c["match"] for c in checks) if checks else False,
        "checks": checks,
    }
    (run_dir / "verification.json").write_text(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--verify":
        rep = verify_run("evidence", sys.argv[2])
        print(f"Verify {sys.argv[2]}: {'REPRODUCIBLE' if rep['all_match'] else 'MISMATCH'}")
        for c in rep["checks"]:
            print(f"  {c['rule_id']:6s} {'ok' if c['match'] else 'XX'}  "
                  f"expected={c.get('expected')} recomputed={c.get('recomputed')}")
        sys.exit(0 if rep["all_match"] else 1)

    engine = DQEngine("control_catalogue.csv", "datasets_config.yaml", evidence_dir="evidence")
    summary = engine.run()
    print(f"Run {summary['run_id']} done - {summary['rules_executed']} rules executed  "
          f"(run_hash {summary['run_hash']})")
    for r in summary["results"]:
        print(f"  {r['rule_id']:6s} [{r['severity']:6s}] {r['status']:5s} - {r['metrics']}")
