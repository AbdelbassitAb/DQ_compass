"""
migrate_catalogue.py

Brings control_catalogue.csv to the canonical schema of the rule_authoring
module: the 14 Appendix A.2 attributes (logic_definition / data_element /
threshold generated) + technical columns (ref_dataset_scope, params,
threshold_pct, active, created_at, updated_at).

- If the CSV is still in the old 13-column format: converts it (and saves the
  original to .backup.csv).
- If the CSV is already canonical: regenerates the three derived columns
  (logic_definition, data_element, threshold) in place, so they stay in sync
  with the derivation logic.

The engine (dq_engine.py) works before AND after migration: the extra columns
are additive, an empty threshold_pct keeps the binary behaviour unchanged.
"""
from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from rule_authoring import schema
from rule_authoring.store import CANONICAL_COLUMNS

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "control_catalogue.csv"


def _map_freq(v: str) -> str:
    v = (v or "").strip()
    return v if v in schema.FREQUENCIES else "Daily"


def _derive(rule: dict) -> dict:
    """(Re)generate the auditor-readable columns from type + params."""
    try:
        params = rule["params"] if isinstance(rule["params"], dict) else json.loads(rule["params"] or "{}")
    except ValueError:
        params = {}
    ctype = rule.get("control_type", "")
    ds = rule.get("dataset_scope", "")
    ref = (rule.get("ref_dataset_scope") or "").strip()
    tp = str(rule.get("threshold_pct") or "").strip()
    tp = float(tp) if tp not in ("", "nan", "None") else None
    rule["params"] = json.dumps(params, ensure_ascii=False)
    rule["logic_definition"] = schema.derive_logic_definition(ctype, params, ds, ref)
    rule["data_element"] = schema.derive_data_element(ctype, params)
    rule["threshold"] = schema.derive_threshold_text(ctype, params, tp)
    return rule


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    now = datetime.now(timezone.utc).isoformat()
    already_canonical = bool(rows) and set(CANONICAL_COLUMNS).issubset(rows[0].keys())

    if already_canonical:
        out = [_derive({c: (r.get(c) or "") for c in CANONICAL_COLUMNS}) for r in rows]
        action = "regenerated derived columns for"
    else:
        backup = CSV_PATH.with_suffix(".backup.csv")
        shutil.copy(CSV_PATH, backup)
        out = []
        for r in rows:
            rule = {c: "" for c in CANONICAL_COLUMNS}
            rule.update({
                "rule_id": r.get("rule_id", ""),
                "control_name": r.get("control_name", ""),
                "control_type": r.get("control_type", ""),
                "description": r.get("description", ""),
                "dataset_scope": r.get("dataset_scope", ""),
                "severity": r.get("severity", ""),
                "frequency": _map_freq(r.get("frequency", "")),
                "owner": r.get("owner", ""),
                "output_type": r.get("output_type", ""),
                "kpi": r.get("kpi", ""),
                "remediation_action": r.get("remediation_action", ""),
                "ref_dataset_scope": (r.get("ref_dataset_scope") or "").strip(),
                "params": r.get("params") or "{}",
                "threshold_pct": "",
                "active": "TRUE",
                "created_at": now,
                "updated_at": now,
            })
            out.append(_derive(rule))
        action = f"migrated (backup: {backup.name}) and generated derived columns for"

    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
        w.writeheader()
        w.writerows(out)

    print(f"{action} {len(out)} rules -> {CSV_PATH.name}")


if __name__ == "__main__":
    main()
