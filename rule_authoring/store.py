"""
rule_authoring/store.py

Persistence of the Control Catalogue + catalogue audit log.

- The catalogue is a CSV with canonical columns: the 14 mandatory attributes of
  Appendix A.2 + technical columns (ref_dataset_scope, params JSON, threshold_pct,
  active, timestamps).
- Every create / update / delete / (de)activate is journalled in
  catalogue_changelog.jsonl (append-only), with the before/after and the hash of
  the file before/after: the catalogue state at any past date is reconstructible
  and it is provable who changed what, when (governance / auditability).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# The 14 mandatory attributes (Appendix A.2) ... then the technical columns.
CANONICAL_COLUMNS = [
    "rule_id", "control_name", "control_type", "description", "logic_definition",
    "dataset_scope", "data_element", "threshold", "severity", "frequency",
    "owner", "output_type", "kpi", "remediation_action", "regulatory_ref",
    # --- technical ---
    "ref_dataset_scope", "params", "threshold_pct", "active",
    "created_at", "updated_at",
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slim(rule) -> dict | None:
    if rule is None:
        return None
    return {k: rule.get(k) for k in CANONICAL_COLUMNS if k in rule}


class CatalogueStore:
    def __init__(self, csv_path, changelog_path):
        self.csv_path = Path(csv_path)
        self.changelog_path = Path(changelog_path)

    # -- read --------------------------------------------------------
    def list_rules(self) -> list:
        if not self.csv_path.exists():
            return []
        with self.csv_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return [self._row_to_rule(r) for r in rows]

    def get(self, rule_id):
        for r in self.list_rules():
            if r["rule_id"] == rule_id:
                return r
        return None

    def _row_to_rule(self, row: dict) -> dict:
        rule = {c: (row.get(c) or "") for c in CANONICAL_COLUMNS}
        raw = rule.get("params") or ""
        try:
            rule["params"] = json.loads(raw) if raw else {}
        except ValueError:
            rule["params"] = {}
        tp = str(rule.get("threshold_pct") or "").strip()
        rule["threshold_pct"] = float(tp) if tp not in ("", "nan", "None") else None
        rule["active"] = str(rule.get("active") or "TRUE").strip().upper() not in ("FALSE", "0", "NO", "N")
        return rule

    # -- write -----------------------------------------------------
    def _rule_to_row(self, rule: dict) -> dict:
        row = {}
        for c in CANONICAL_COLUMNS:
            v = rule.get(c, "")
            if c == "params":
                v = json.dumps(rule.get("params") or {}, ensure_ascii=False)
            elif c == "threshold_pct":
                tp = rule.get("threshold_pct")
                v = "" if tp in (None, "") else str(tp)
            elif c == "active":
                v = "TRUE" if rule.get("active", True) else "FALSE"
            row[c] = "" if v is None else str(v)
        return row

    def _write_all(self, rules: list) -> None:
        # atomic write: temporary file then replace.
        fd, tmp = tempfile.mkstemp(dir=str(self.csv_path.parent),
                                   prefix=".catalogue_", suffix=".csv")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
                w.writeheader()
                for r in rules:
                    w.writerow(self._rule_to_row(r))
            os.replace(tmp, self.csv_path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def catalogue_hash(self) -> str:
        if not self.csv_path.exists():
            return ""
        return hashlib.sha256(self.csv_path.read_bytes()).hexdigest()[:16]

    # -- CRUD ----------------------------------------------------
    def upsert(self, rule: dict, *, user: str, note: str = "") -> dict:
        rules = self.list_rules()
        idx = next((i for i, r in enumerate(rules) if r["rule_id"] == rule["rule_id"]), None)
        now = _utcnow()
        hash_before = self.catalogue_hash()
        if idx is None:
            rule.setdefault("created_at", now)
            rule["updated_at"] = now
            before, action = None, "create"
            rules.append(rule)
        else:
            before = rules[idx]
            rule["created_at"] = before.get("created_at") or now
            rule["updated_at"] = now
            rules[idx] = rule
            action = "update"
        self._write_all(rules)
        self._log(action, rule["rule_id"], user, note, before, rule, hash_before)
        return rule

    def delete(self, rule_id: str, *, user: str, note: str = "") -> None:
        rules = self.list_rules()
        before = next((r for r in rules if r["rule_id"] == rule_id), None)
        if before is None:
            raise KeyError(rule_id)
        hash_before = self.catalogue_hash()
        self._write_all([r for r in rules if r["rule_id"] != rule_id])
        self._log("delete", rule_id, user, note, before, None, hash_before)

    def set_active(self, rule_id: str, active: bool, *, user: str, note: str = "") -> None:
        rules = self.list_rules()
        idx = next((i for i, r in enumerate(rules) if r["rule_id"] == rule_id), None)
        if idx is None:
            raise KeyError(rule_id)
        before = dict(rules[idx])
        hash_before = self.catalogue_hash()
        rules[idx]["active"] = active
        rules[idx]["updated_at"] = _utcnow()
        self._write_all(rules)
        self._log("activate" if active else "deactivate", rule_id, user, note,
                  before, rules[idx], hash_before)

    def retarget_dataset(self, old: str, new: str, *, user: str, note: str = "") -> list:
        """Rewrite dataset_scope / ref_dataset_scope from `old` to `new` on every
        rule that uses it (called when a data source is renamed). One changelog
        entry per touched rule."""
        rules = self.list_rules()
        originals = {r["rule_id"]: dict(r) for r in rules}
        hash_before = self.catalogue_hash()
        touched = []
        for r in rules:
            changed = False
            if r["dataset_scope"] == old:
                r["dataset_scope"] = new
                changed = True
            if (r.get("ref_dataset_scope") or "") == old:
                r["ref_dataset_scope"] = new
                changed = True
            if changed:
                r["updated_at"] = _utcnow()
                touched.append(r["rule_id"])
        if touched:
            self._write_all(rules)
            for rid in touched:
                after = next(x for x in rules if x["rule_id"] == rid)
                self._log("update", rid, user, note, originals[rid], after, hash_before)
        return touched

    # -- audit log ---------------------------------------------
    def _log(self, action, rule_id, user, note, before, after, hash_before) -> None:
        entry = {
            "timestamp": _utcnow(),
            "user": (user or "anonymous"),
            "action": action,
            "rule_id": rule_id,
            "note": note or "",
            "catalogue_hash_before": hash_before,
            "catalogue_hash_after": self.catalogue_hash(),
            "before": _slim(before),
            "after": _slim(after),
        }
        with self.changelog_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def history(self, rule_id: str | None = None) -> list:
        if not self.changelog_path.exists():
            return []
        out = []
        with self.changelog_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if rule_id is None or e.get("rule_id") == rule_id:
                    out.append(e)
        return list(reversed(out))
