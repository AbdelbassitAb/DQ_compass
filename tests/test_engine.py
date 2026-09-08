"""
Engine-level tests: Evidence Pack structure, reproducibility, run ledger,
independent verification, threshold logic, resilience to a missing source.

Self-contained: every test builds its own catalogue + datasets_config + CSV
fixture in a temp dir, so nothing here depends on the repo's (user-editable)
control_catalogue.csv / datasets_config.yaml / sample_data.

    python -m pytest tests/
    python tests/test_engine.py
"""
import csv
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dq_engine import DQEngine, verify_run  # noqa: E402
from rule_authoring.store import CANONICAL_COLUMNS  # noqa: E402

WIDGETS_CSV = textwrap.dedent("""\
    id,status,amount,updated
    1,NEW,100,2026-01-05
    2,NEW,200,2026-01-06
    3,DONE,150,2026-01-07
    4,DONE,175,2026-01-08
    5,NEW,120,2026-01-09
    6,DONE,,2026-01-10
    7,NEW,90,2026-01-11
    8,DONE,210,2026-01-12
    9,NEW,60,2026-01-13
    10,DONE,300,2026-01-14
    11,NEW,80,2026-01-15
""")

# amount: 10 filled + 1 blank  -> 1/11 = 9.09% incomplete.

RULES = [
    # rule_id, control_type, dataset_scope, params(json), threshold_pct
    ("C1", "Completeness", "widgets", '{"field": "amount"}', ""),
    ("C2", "Completeness", "widgets", '{"field": "amount"}', "10"),
    ("T1", "Timeliness", "widgets",
     '{"field": "updated", "max_lag_days": 3650, "reference_date": "today"}', ""),
    ("G1", "Completeness", "ghost_source", '{"field": "amount"}', ""),
]


def _fixture(*, rules=RULES) -> Path:
    d = Path(tempfile.mkdtemp())
    (d / "widgets.csv").write_text(WIDGETS_CSV, encoding="utf-8")
    (d / "datasets_config.yaml").write_text(
        "widgets:\n"
        "  type: csv\n"
        "  status: active\n"
        "  config:\n"
        f"    path: {(d / 'widgets.csv').as_posix()}\n"
        "    delimiter: ','\n"
        "    header_row: '1'\n", encoding="utf-8")
    cat = d / "catalogue.csv"
    base = {c: "" for c in CANONICAL_COLUMNS}
    with cat.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
        w.writeheader()
        for rid, ctype, ds, params, tpct in rules:
            w.writerow({**base, "rule_id": rid, "control_name": f"{rid} check",
                        "control_type": ctype, "dataset_scope": ds, "params": params,
                        "severity": "Medium", "frequency": "Daily", "owner": "x",
                        "output_type": "Error dataset", "kpi": "k",
                        "remediation_action": "y", "active": "TRUE",
                        "threshold_pct": tpct})
    return d, str(cat), str(d / "datasets_config.yaml")


def _run(evdir, cat, cfg):
    return DQEngine(cat, cfg, evidence_dir=str(evdir)).run()


def test_evidence_pack_structure():
    d, cat, cfg = _fixture()
    ev = d / "evidence"
    s = _run(ev, cat, cfg)
    rd = ev / s["run_id"]
    for f in ("run_summary.json", "system_trace.json", "run_log.jsonl", "run.log"):
        assert (rd / f).exists(), f
    assert (rd / "snapshots" / "widgets.csv").exists()
    assert (ev / "runs_ledger.jsonl").exists()
    for r in s["results"]:
        assert (rd / f"{r['rule_id']}_result.json").exists()
    trace = json.loads((rd / "system_trace.json").read_text())
    assert trace["engine_version"] and trace["controls_used"]
    assert trace["controls_module"]["sha256_16"]


def test_reproducibility_and_ledger_chain():
    d, cat, cfg = _fixture()
    ev = d / "evidence"
    a = _run(ev, cat, cfg)
    b = _run(ev, cat, cfg)
    key = lambda run: {r["rule_id"]: (r["status"], r["metrics"], r["exception_count"])
                       for r in run["results"]}
    assert key(a) == key(b)
    assert b["previous_run_hash"] == a["run_hash"]
    assert a["run_hash"] != b["run_hash"]


def test_verify_run_reproducible():
    d, cat, cfg = _fixture()
    ev = d / "evidence"
    s = _run(ev, cat, cfg)
    rep = verify_run(str(ev), s["run_id"])
    assert rep["all_match"] is True
    assert (ev / s["run_id"] / "verification.json").exists()


def test_resolved_execution_parameters():
    d, cat, cfg = _fixture()
    s = _run(d / "evidence", cat, cfg)
    tl = [r for r in s["results"] if r["control_type"] == "Timeliness"]
    assert tl and "reference_date_resolved" in tl[0]["execution_parameters"]


def test_threshold_turns_fail_into_pass():
    # amount: 1 null out of 11 rows (9.09%).
    # C1 (no threshold) -> FAIL ; C2 (threshold_pct = 10) -> PASS (within_threshold).
    d, cat, cfg = _fixture()
    s = _run(d / "evidence", cat, cfg)
    by = {r["rule_id"]: r for r in s["results"]}
    assert by["C1"]["status"] == "FAIL"
    assert by["C2"]["status"] == "PASS"
    assert by["C2"]["metrics"].get("within_threshold") is True


def test_missing_source_produces_error_record_not_crash():
    d, cat, cfg = _fixture()
    ev = d / "evidence"
    s = _run(ev, cat, cfg)
    by = {r["rule_id"]: r for r in s["results"]}
    assert by["G1"]["status"] == "ERROR"                 # ghost_source is not declared
    assert by["C1"]["status"] in ("PASS", "FAIL")        # run continued past the error
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
