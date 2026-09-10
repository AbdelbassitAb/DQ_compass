"""
scorecard.py

Reporting Layer.

Reads the latest run_summary.json from the Audit layer and produces, in
reporting/ :
  - scorecard.csv          traffic-light table (Power BI / Excel)
  - scorecard.html         standalone scorecard for a quick demo
  - exceptions_detail.csv   record-by-record drill-down
  - coverage.csv            datasets x dimensions control coverage view
  - exception_summary.csv   exceptions grouped by severity / owner / type / dataset
  - dataset_score.csv       composite DQ score per dataset (severity-weighted)
  - trend.csv               pass / fail / error per run, from the run ledger
  - alerts.json             actionable alerts for failing High-severity controls,
                            carrying the remediation action from the catalogue

Usage: python reporting/scorecard.py <run_id_or_latest>
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT / "evidence"
CATALOGUE_CSV = ROOT / "control_catalogue.csv"
SEVERITY_WEIGHT = {"High": 5, "Medium": 2, "Low": 1}


def _run_started_at(run_dir: Path) -> str:
    """Recorded run timestamp (ISO). Falls back to directory mtime as a string
    so ordering still works if the summary is unreadable."""
    try:
        with open(run_dir / "run_summary.json") as f:
            ts = json.load(f).get("run_timestamp_utc")
        if ts:
            return str(ts)
    except (OSError, ValueError):
        pass
    return f"~{run_dir.stat().st_mtime:018.0f}"


def _latest_run_dir() -> Path:
    # Order by the run's OWN recorded timestamp, not the directory mtime: writing
    # verification.json / signoff.json into a past run touches its mtime and would
    # otherwise make it look like the newest run.
    runs = sorted(
        (p for p in EVIDENCE_DIR.iterdir() if p.is_dir() and (p / "run_summary.json").exists()),
        key=_run_started_at,
    )
    if not runs:
        raise SystemExit("No run found in evidence/. Run 'python dq_engine.py' first.")
    return runs[-1]


def _traffic_light(status: str, severity: str) -> str:
    if status == "PASS":
        return "GREEN"
    if status == "ERROR":
        return "GREY"
    if severity == "High":
        return "RED"
    return "ORANGE"


def build_scorecard(run_dir: Path) -> pd.DataFrame:
    with open(run_dir / "run_summary.json") as f:
        summary = json.load(f)

    rows = []
    for r in summary["results"]:
        rows.append({
            "run_id": r["run_id"],
            "rule_id": r["rule_id"],
            "control_name": r["control_name"],
            "control_type": r["control_type"],
            "severity": r["severity"],
            "owner": r["owner"],
            "status": r["status"],
            "traffic_light": _traffic_light(r["status"], r["severity"]),
            "exception_count": r["exception_count"],
            **{f"metric_{k}": v for k, v in r["metrics"].items()},
        })
    return pd.DataFrame(rows)


def build_exceptions_detail(run_dir: Path) -> pd.DataFrame:
    with open(run_dir / "run_summary.json") as f:
        summary = json.load(f)

    frames = []
    for r in summary["results"]:
        p = r.get("exceptions_evidence_path")
        if not p:
            continue
        path = Path(p)
        if not path.is_absolute():
            path = run_dir / path
        if not path.exists():
            continue
        df = pd.read_csv(path)
        df.insert(0, "rule_id", r["rule_id"])
        df.insert(1, "severity", r["severity"])
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["rule_id", "severity"])
    return pd.concat(frames, ignore_index=True, sort=False)


def _summary(run_dir: Path) -> dict:
    with open(run_dir / "run_summary.json") as f:
        return json.load(f)


def _exc_pct(r: dict) -> float:
    """Exception rate for a rule result: use the metric if present, else derive."""
    m = r.get("metrics", {})
    if "exception_pct" in m:
        return float(m["exception_pct"])
    total = m.get("total_records") or 0
    return round(100 * r.get("exception_count", 0) / total, 2) if total else (
        100.0 if r["status"] == "FAIL" else 0.0)


def build_coverage(run_dir: Path) -> pd.DataFrame:
    """Control coverage view: which datasets are covered on which dimension (4.3)."""
    rows = []
    for r in _summary(run_dir)["results"]:
        ds = r.get("rule_configuration_snapshot", {}).get("dataset_scope", "")
        rows.append({"dataset_scope": ds, "control_type": r["control_type"], "rule_id": r["rule_id"]})
    if not rows:
        return pd.DataFrame(columns=["dataset_scope", "control_type", "rule_ids", "n_rules"])
    df = pd.DataFrame(rows)
    return (df.groupby(["dataset_scope", "control_type"])["rule_id"]
              .agg(rule_ids=lambda s: "; ".join(sorted(s)), n_rules="count")
              .reset_index())


def build_exception_summary(run_dir: Path) -> pd.DataFrame:
    """Exceptions grouped along four dimensions, long format (Power BI friendly)."""
    results = _summary(run_dir)["results"]
    out = []
    dims = {
        "severity": lambda r: r["severity"],
        "owner": lambda r: r["owner"],
        "control_type": lambda r: r["control_type"],
        "dataset": lambda r: r.get("rule_configuration_snapshot", {}).get("dataset_scope", ""),
    }
    for dim, key_fn in dims.items():
        agg: dict[str, dict] = {}
        for r in results:
            k = key_fn(r)
            b = agg.setdefault(k, {"failing_rules": 0, "error_rules": 0, "total_exceptions": 0})
            b["total_exceptions"] += r.get("exception_count", 0)
            if r["status"] == "FAIL":
                b["failing_rules"] += 1
            elif r["status"] == "ERROR":
                b["error_rules"] += 1
        for k, b in sorted(agg.items()):
            out.append({"dimension": dim, "key": k, **b})
    return pd.DataFrame(out)


def build_dataset_score(run_dir: Path) -> pd.DataFrame:
    """Severity-weighted composite DQ score per dataset (0-100, higher is better)."""
    results = _summary(run_dir)["results"]
    per_ds: dict[str, dict] = {}
    for r in results:
        ds = r.get("rule_configuration_snapshot", {}).get("dataset_scope", "")
        w = SEVERITY_WEIGHT.get(r["severity"], 1)
        b = per_ds.setdefault(ds, {"n_rules": 0, "n_pass": 0, "n_fail": 0, "n_error": 0,
                                   "weight": 0.0, "penalty": 0.0})
        b["n_rules"] += 1
        b["weight"] += w
        if r["status"] == "PASS":
            b["n_pass"] += 1
        elif r["status"] == "ERROR":
            b["n_error"] += 1
            b["penalty"] += w  # unknown = worst case
        else:
            b["n_fail"] += 1
            b["penalty"] += w * min(1.0, _exc_pct(r) / 100)
    rows = []
    for ds, b in sorted(per_ds.items()):
        score = 100.0 if b["weight"] == 0 else max(0.0, round(100 * (1 - b["penalty"] / b["weight"]), 1))
        rows.append({"dataset_scope": ds, "n_rules": b["n_rules"], "n_pass": b["n_pass"],
                     "n_fail": b["n_fail"], "n_error": b["n_error"], "dq_score": score})
    return pd.DataFrame(rows)


def overall_dq_score(run_dir: Path) -> float:
    """Severity-weighted composite DQ score across every rule in a run (0-100)."""
    weight = penalty = 0.0
    for r in _summary(run_dir)["results"]:
        w = SEVERITY_WEIGHT.get(r["severity"], 1)
        weight += w
        if r["status"] == "PASS":
            continue
        if r["status"] == "ERROR":
            penalty += w
        else:
            penalty += w * min(1.0, _exc_pct(r) / 100)
    return 100.0 if weight == 0 else max(0.0, round(100 * (1 - penalty / weight), 1))


def run_result_map(run_dir: Path) -> dict:
    """rule_id -> {status, exception_count, control_name, control_type, severity, owner}."""
    return {
        r["rule_id"]: {
            "status": r["status"], "exception_count": r.get("exception_count", 0),
            "control_name": r["control_name"], "control_type": r["control_type"],
            "severity": r["severity"], "owner": r["owner"],
            "error": r.get("error"),
        }
        for r in _summary(run_dir)["results"]
    }


def build_trend() -> pd.DataFrame:
    ledger = EVIDENCE_DIR / "runs_ledger.jsonl"
    if not ledger.exists():
        return pd.DataFrame(columns=["run_id", "timestamp", "rules_executed", "pass", "fail", "error"])
    rows = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        c = e.get("counts", {})
        rows.append({"run_id": e["run_id"], "timestamp": e["timestamp"],
                     "rules_executed": e.get("rules_executed", 0),
                     "pass": c.get("PASS", 0), "fail": c.get("FAIL", 0), "error": c.get("ERROR", 0)})
    return pd.DataFrame(rows)


def build_alerts(run_dir: Path) -> list:
    """Actionable alerts for failing High-severity controls (closes the loop:
    failures captured, prioritised and actionable)."""
    remediation = {}
    if CATALOGUE_CSV.exists():
        with CATALOGUE_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                remediation[row["rule_id"]] = row.get("remediation_action", "")
    alerts = []
    for r in _summary(run_dir)["results"]:
        if r["status"] in ("FAIL", "ERROR") and r["severity"] == "High":
            alerts.append({
                "rule_id": r["rule_id"], "control_name": r["control_name"],
                "severity": r["severity"], "status": r["status"], "owner": r["owner"],
                "exception_count": r.get("exception_count", 0),
                "dataset_scope": r.get("rule_configuration_snapshot", {}).get("dataset_scope", ""),
                "remediation_action": remediation.get(r["rule_id"], ""),
            })
    return alerts


def to_html(scorecard: pd.DataFrame, run_dir: Path) -> str:
    color_map = {"GREEN": "#1a9850", "ORANGE": "#fdae61", "RED": "#d73027", "GREY": "#6b7280"}
    rows_html = ""
    for _, row in scorecard.iterrows():
        color = color_map[row["traffic_light"]]
        rows_html += (
            f"<tr>"
            f"<td><span style='display:inline-block;width:12px;height:12px;"
            f"border-radius:50%;background:{color}'></span></td>"
            f"<td>{row['rule_id']}</td><td>{row['control_name']}</td>"
            f"<td>{row['control_type']}</td><td>{row['severity']}</td>"
            f"<td>{row['status']}</td><td>{row['exception_count']}</td>"
            f"<td>{row['owner']}</td></tr>"
        )
    n_red = (scorecard["traffic_light"] == "RED").sum()
    n_orange = (scorecard["traffic_light"] == "ORANGE").sum()
    n_green = (scorecard["traffic_light"] == "GREEN").sum()
    n_grey = (scorecard["traffic_light"] == "GREY").sum()
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>DQ Compass - Scorecard</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:24px;color:#222}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left;font-size:14px}}
th{{background:#111;color:#fff}}
.kpi{{display:flex;gap:16px;margin:16px 0}}
.kpi div{{padding:12px 20px;border-radius:6px;color:#fff;font-weight:bold}}
</style></head><body>
<h2>DQ Compass - Data Quality Scorecard</h2>
<p>Run: {run_dir.name}</p>
<div class="kpi">
<div style="background:#d73027">RED: {n_red}</div>
<div style="background:#fdae61">ORANGE: {n_orange}</div>
<div style="background:#1a9850">GREEN: {n_green}</div>
<div style="background:#6b7280">ERROR: {n_grey}</div>
</div>
<table><tr><th></th><th>Rule ID</th><th>Control</th><th>Type</th><th>Severity</th>
<th>Status</th><th>Exceptions</th><th>Owner</th></tr>
{rows_html}
</table>
</body></html>"""


def main(run_arg: str | None = None):
    if run_arg is None:
        run_arg = sys.argv[1] if len(sys.argv) > 1 else "latest"
    run_dir = _latest_run_dir() if run_arg == "latest" else EVIDENCE_DIR / run_arg

    out_dir = Path(__file__).resolve().parent
    scorecard = build_scorecard(run_dir)

    outputs = {
        "scorecard.csv": scorecard,
        "exceptions_detail.csv": build_exceptions_detail(run_dir),
        "coverage.csv": build_coverage(run_dir),
        "exception_summary.csv": build_exception_summary(run_dir),
        "dataset_score.csv": build_dataset_score(run_dir),
        "trend.csv": build_trend(),
    }
    for name, df in outputs.items():
        df.to_csv(out_dir / name, index=False)
    (out_dir / "scorecard.html").write_text(to_html(scorecard, run_dir))
    alerts = build_alerts(run_dir)
    (out_dir / "alerts.json").write_text(json.dumps(alerts, indent=2))

    print(scorecard[["rule_id", "control_name", "severity", "status",
                      "traffic_light", "exception_count"]].to_string(index=False))
    print(f"\nFiles generated in {out_dir}:")
    for name in list(outputs) + ["scorecard.html", "alerts.json"]:
        print(f"  {name}")
    if alerts:
        print(f"\n{len(alerts)} High-severity alert(s) -> alerts.json")


if __name__ == "__main__":
    main()
