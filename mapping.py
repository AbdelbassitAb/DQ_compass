"""
mapping.py

Supervisory Mapping. From the Control Catalogue, generate:
  - requirement -> control implemented -> evidence generated -> output
  - per-rule control-to-evidence traceability (rule -> last run + hash)
  - the key supervisory principles the solution demonstrates

A rule's supervisory requirement is its explicit `regulatory_ref` if set,
otherwise a default derived from the DQ dimension.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOGUE_CSV = ROOT / "control_catalogue.csv"
EVIDENCE_DIR = ROOT / "evidence"

DEFAULT_REQUIREMENT = {
    "Completeness": "Data completeness (BCBS 239 - Completeness)",
    "Validity": "Accuracy & integrity - conformance to defined formats / domains (BCBS 239 - Accuracy)",
    "Uniqueness": "No duplication of records or keys (BCBS 239 - Accuracy & Integrity)",
    "Consistency": "Referential integrity across data sets (BCBS 239 - Accuracy & Integrity)",
    "Timeliness": "Data timeliness / freshness (BCBS 239 - Timeliness)",
    "Reconciliation": "Reconciliation across sources (BCBS 239 - Accuracy & Reconciliation)",
}

PRINCIPLES = [
    ("Traceability",
     "Every control links to its rule definition, its dataset (snapshot + SHA-256 hash) "
     "and its execution run (run_id + run_hash)."),
    ("Repeatability",
     "Controls produce identical results under identical inputs -- proven by \"Verify this run\", "
     "which re-executes the stored config against the stored snapshots."),
    ("Auditability",
     "An independent party can reconstruct any run from evidence/<run_id>/ (config snapshot, "
     "dataset snapshots, processing log, system trace) and validate the outcome."),
    ("Governance",
     "Controls are owned (owner), monitored (catalogue + coverage matrix), versioned "
     "(hash-chained changelogs) and actionable (remediation_action, alerts.json)."),
]


def _load_catalogue() -> list:
    if not CATALOGUE_CSV.exists():
        return []
    with CATALOGUE_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _last_run_for_rule(rule_id: str):
    ledger = EVIDENCE_DIR / "runs_ledger.jsonl"
    if not ledger.exists():
        return None
    runs = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            runs.append(json.loads(line))
        except ValueError:
            pass
    for e in reversed(runs):
        rp = EVIDENCE_DIR / e["run_id"] / f"{rule_id}_result.json"
        if rp.exists():
            try:
                res = json.loads(rp.read_text())
            except ValueError:
                continue
            return {"run_id": e["run_id"], "timestamp": e["timestamp"],
                    "status": res.get("status"), "run_hash": e.get("run_hash")}
    return None


def build_mapping() -> list:
    rows = []
    for r in _load_catalogue():
        if str(r.get("active", "TRUE")).strip().upper() in ("FALSE", "0", "NO", "N"):
            continue
        ctype = r.get("control_type", "")
        req = (r.get("regulatory_ref") or "").strip() or DEFAULT_REQUIREMENT.get(ctype, "Data quality control")
        last = _last_run_for_rule(r["rule_id"]) or {}
        rows.append({
            "rule_id": r["rule_id"],
            "requirement": req,
            "control_implemented": r.get("control_name", ""),
            "control_type": ctype,
            "severity": r.get("severity", ""),
            "owner": r.get("owner", ""),
            "logic_definition": r.get("logic_definition", ""),
            "evidence_generated": (
                f"Evidence Pack per run ({r.get('output_type', '')}): metrics, exception dataset, "
                "run_summary.json, system_trace.json, run_log.jsonl; verification.json on request"
            ),
            "output": r.get("output_type", ""),
            "kpi": r.get("kpi", ""),
            "last_run_id": last.get("run_id", ""),
            "last_run_timestamp": last.get("timestamp", ""),
            "last_run_status": last.get("status", ""),
            "last_run_hash": last.get("run_hash", ""),
        })
    return rows


def mapping_csv() -> str:
    rows = build_mapping()
    if not rows:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


if __name__ == "__main__":
    out = ROOT / "reporting" / "supervisory_mapping.csv"
    text = mapping_csv()
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out} ({len(build_mapping())} rules)")
