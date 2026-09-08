"""
Engine-level tests: Evidence Pack structure, reproducibility, run ledger,
independent verification, resilience to a missing source.

    python -m pytest tests/
    python tests/test_engine.py
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dq_engine import DQEngine, verify_run  # noqa: E402
from rule_authoring.store import CANONICAL_COLUMNS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CAT = str(ROOT / "control_catalogue.csv")
CFG = str(ROOT / "datasets_config.yaml")


def _run(evdir):
    return DQEngine(CAT, CFG, evidence_dir=str(evdir)).run()


def test_evidence_pack_structure():
    ev = Path(tempfile.mkdtemp())
    s = _run(ev)
    rd = ev / s["run_id"]
    for f in ("run_summary.json", "system_trace.json", "run_log.jsonl", "run.log"):
        assert (rd / f).exists(), f
    assert (rd / "snapshots" / "orders.csv").exists()
    assert (ev / "runs_ledger.jsonl").exists()
    for r in s["results"]:
        assert (rd / f"{r['rule_id']}_result.json").exists()
    trace = json.loads((rd / "system_trace.json").read_text())
    assert trace["engine_version"] and trace["controls_used"]
    assert trace["controls_module"]["sha256_16"]


def test_reproducibility_and_ledger_chain():
    ev = Path(tempfile.mkdtemp())
    a = _run(ev)
    b = _run(ev)
    key = lambda run: {r["rule_id"]: (r["status"], r["metrics"], r["exception_count"])
                       for r in run["results"]}
    assert key(a) == key(b)
    assert b["previous_run_hash"] == a["run_hash"]
    assert a["run_hash"] != b["run_hash"]


def test_verify_run_reproducible():
    ev = Path(tempfile.mkdtemp())
    s = _run(ev)
    rep = verify_run(str(ev), s["run_id"])
    assert rep["all_match"] is True
    assert (ev / s["run_id"] / "verification.json").exists()


def test_resolved_execution_parameters():
    ev = Path(tempfile.mkdtemp())
    s = _run(ev)
    timeliness = [r for r in s["results"] if r["control_type"] == "Timeliness"]
    assert timeliness and "reference_date_resolved" in timeliness[0]["execution_parameters"]


def test_threshold_turns_fail_into_pass():
    # Completeness on orders.amount = 1 null out of 11 rows (9.09%).
    # Without a threshold -> FAIL; with threshold_pct = 10 -> PASS (within_threshold).
    ev = Path(tempfile.mkdtemp())
    cat = ev / "cat.csv"
    base = {c: "" for c in CANONICAL_COLUMNS}
    common = dict(control_name="amount not null", control_type="Completeness",
                  dataset_scope="orders", severity="Medium", frequency="Daily", owner="x",
                  output_type="Error dataset", kpi="k", remediation_action="y",
                  params='{"field": "amount"}', active="TRUE")
    with cat.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
        w.writeheader()
        w.writerow({**base, **common, "rule_id": "T1", "threshold_pct": ""})
        w.writerow({**base, **common, "rule_id": "T2", "threshold_pct": "10"})
    s = DQEngine(str(cat), CFG, evidence_dir=str(ev)).run()
    by = {r["rule_id"]: r for r in s["results"]}
    assert by["T1"]["status"] == "FAIL"
    assert by["T2"]["status"] == "PASS"
    assert by["T2"]["metrics"].get("within_threshold") is True


def test_missing_source_produces_error_record_not_crash():
    ev = Path(tempfile.mkdtemp())
    cat = ev / "cat.csv"
    base = {c: "" for c in CANONICAL_COLUMNS}
    with cat.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
        w.writeheader()
        w.writerow({**base, "rule_id": "G1", "control_name": "on ghost",
                    "control_type": "Completeness", "dataset_scope": "ghost_dataset",
                    "severity": "High", "frequency": "Daily", "owner": "x",
                    "output_type": "Error dataset", "kpi": "k", "remediation_action": "y",
                    "params": '{"field": "a"}', "active": "TRUE"})
        w.writerow({**base, "rule_id": "G2", "control_name": "on orders",
                    "control_type": "Completeness", "dataset_scope": "orders",
                    "severity": "Low", "frequency": "Daily", "owner": "x",
                    "output_type": "Error dataset", "kpi": "k", "remediation_action": "y",
                    "params": '{"field": "amount"}', "active": "TRUE"})
    s = DQEngine(str(cat), CFG, evidence_dir=str(ev)).run()
    by = {r["rule_id"]: r for r in s["results"]}
    assert by["G1"]["status"] == "ERROR"
    assert by["G2"]["status"] in ("PASS", "FAIL")  # run continued past the error
    rep = verify_run(str(ev), s["run_id"])
    assert [c for c in rep["checks"] if c["rule_id"] == "G1"][0]["match"] is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} tests OK")
    sys.exit(1 if failed else 0)
