"""
rule_authoring/source_store.py

Persistence of the data source registry (datasets_config.yaml) + append-only
audit log (data_sources_changelog.jsonl) + the delete policy:

  - retire(name)     : soft delete. status -> retired, dependent rules are
                       auto-deactivated (logged), reversible.
  - reactivate(name) : status -> active, returns the dependent rules that are
                       still inactive so the UI can offer a bulk reactivate.
  - purge(name)      : hard remove from the YAML. Dependent rules are
                       deactivated (never deleted) so control definitions are
                       never lost.
  - rename(old, new) : rewrites the YAML key AND retargets dataset_scope /
                       ref_dataset_scope on every dependent rule, in one
                       transaction, each change logged.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from connectors import normalize_entry


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SourceStore:
    def __init__(self, yaml_path, changelog_path, catalogue_store):
        self.yaml_path = Path(yaml_path)
        self.changelog_path = Path(changelog_path)
        self.catalogue = catalogue_store  # to cascade onto rules

    # -- read --------------------------------------------------------
    def _raw(self) -> dict:
        if not self.yaml_path.exists():
            return {}
        with self.yaml_path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def list_sources(self) -> list:
        out = []
        for name, entry in self._raw().items():
            e = normalize_entry(entry)
            out.append({
                "name": name, "type": e["type"], "status": e.get("status", "active"),
                "config": e.get("config", {}) or {},
                "created_at": e.get("created_at", ""), "updated_at": e.get("updated_at", ""),
            })
        return out

    def get(self, name):
        return next((s for s in self.list_sources() if s["name"] == name), None)

    def names(self) -> list:
        return [s["name"] for s in self.list_sources()]

    def active_names(self) -> list:
        return [s["name"] for s in self.list_sources() if s["status"] == "active"]

    # -- write -----------------------------------------------------
    def _write(self, sources: list) -> None:
        doc = {}
        for s in sources:
            doc[s["name"]] = {
                "type": s["type"],
                "status": s.get("status", "active"),
                "config": s.get("config", {}) or {},
                "created_at": s.get("created_at") or _utcnow(),
                "updated_at": s.get("updated_at") or _utcnow(),
            }
        fd, tmp = tempfile.mkstemp(dir=str(self.yaml_path.parent),
                                   prefix=".sources_", suffix=".yaml")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True)
            os.replace(tmp, self.yaml_path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def hash(self) -> str:
        if not self.yaml_path.exists():
            return ""
        return hashlib.sha256(self.yaml_path.read_bytes()).hexdigest()[:16]

    # -- audit log -----------------------------------------------
    def _log(self, action, name, user, note, hash_before, extra=None) -> None:
        entry = {
            "timestamp": _utcnow(),
            "user": user or "anonymous",
            "action": action,
            "source": name,
            "note": note or "",
            "hash_before": hash_before,
            "hash_after": self.hash(),
        }
        if extra:
            entry.update(extra)
        with self.changelog_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def history(self, name: str | None = None) -> list:
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
                if name is None or e.get("source") == name:
                    out.append(e)
        return list(reversed(out))

    # -- CRUD ---------------------------------------------------
    def upsert(self, name, type_, config, *, user, note="", status="active"):
        sources = self.list_sources()
        idx = next((i for i, s in enumerate(sources) if s["name"] == name), None)
        now = _utcnow()
        hash_before = self.hash()
        rec = {"name": name, "type": type_, "status": status, "config": config or {}}
        if idx is None:
            rec["created_at"] = now
            rec["updated_at"] = now
            sources.append(rec)
            action = "create"
        else:
            rec["created_at"] = sources[idx].get("created_at") or now
            rec["updated_at"] = now
            sources[idx] = rec
            action = "update"
        self._write(sources)
        self._log(action, name, user, note, hash_before)
        return rec

    # -- dependants -------------------------------------------
    def used_by(self, name: str) -> list:
        out = []
        for r in self.catalogue.list_rules():
            if r["dataset_scope"] == name or (r.get("ref_dataset_scope") or "") == name:
                out.append(r["rule_id"])
        return out

    def _deactivate_dependents(self, name: str, user: str, reason: str) -> list:
        affected = []
        for rid in self.used_by(name):
            rule = self.catalogue.get(rid)
            if rule and rule["active"]:
                self.catalogue.set_active(rid, False, user=user, note=f"auto: {reason}")
                affected.append(rid)
        return affected

    def retire(self, name: str, *, user: str, note: str = "") -> list:
        sources = self.list_sources()
        idx = next((i for i, s in enumerate(sources) if s["name"] == name), None)
        if idx is None:
            raise KeyError(name)
        hash_before = self.hash()
        sources[idx]["status"] = "retired"
        sources[idx]["updated_at"] = _utcnow()
        self._write(sources)
        affected = self._deactivate_dependents(name, user, f"source '{name}' retired")
        self._log("retire", name, user, note, hash_before, {"deactivated_rules": affected})
        return affected

    def reactivate(self, name: str, *, user: str, note: str = "") -> list:
        sources = self.list_sources()
        idx = next((i for i, s in enumerate(sources) if s["name"] == name), None)
        if idx is None:
            raise KeyError(name)
        hash_before = self.hash()
        sources[idx]["status"] = "active"
        sources[idx]["updated_at"] = _utcnow()
        self._write(sources)
        inactive = [rid for rid in self.used_by(name)
                    if (self.catalogue.get(rid) or {}).get("active") is False]
        self._log("reactivate", name, user, note, hash_before,
                  {"inactive_dependent_rules": inactive})
        return inactive

    def reactivate_rules(self, rule_ids: list, *, user: str) -> list:
        done = []
        for rid in rule_ids:
            rule = self.catalogue.get(rid)
            if rule and not rule["active"]:
                self.catalogue.set_active(rid, True, user=user, note="reactivated with its source")
                done.append(rid)
        return done

    def purge(self, name: str, *, user: str, note: str = "") -> list:
        sources = self.list_sources()
        if not any(s["name"] == name for s in sources):
            raise KeyError(name)
        hash_before = self.hash()
        affected = self._deactivate_dependents(name, user, f"source '{name}' purged")
        self._write([s for s in sources if s["name"] != name])
        self._log("purge", name, user, note, hash_before, {"deactivated_rules": affected})
        return affected

    def rename(self, old: str, new: str, *, user: str, note: str = "") -> list:
        sources = self.list_sources()
        idx = next((i for i, s in enumerate(sources) if s["name"] == old), None)
        if idx is None:
            raise KeyError(old)
        if any(s["name"] == new for s in sources):
            raise ValueError(f"A source named '{new}' already exists.")
        hash_before = self.hash()
        sources[idx]["name"] = new
        sources[idx]["updated_at"] = _utcnow()
        self._write(sources)
        retargeted = self.catalogue.retarget_dataset(
            old, new, user=user, note=f"source renamed {old} -> {new}")
        self._log("rename", old, user, note, hash_before,
                  {"new_name": new, "retargeted_rules": retargeted})
        return retargeted
