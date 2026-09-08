"""
rule_authoring/source_schema.py

The meta-catalogue for data sources: validation applied to a source
registration before it enters datasets_config.yaml, plus a plain-language
summary. Mirrors rule_authoring/schema.py for the Control Catalogue.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from connectors import SourceIssue, describe_connectors, get_connector

SOURCE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,39}$")
CONNECTOR_TYPES = [c["type"] for c in describe_connectors()]


@dataclass
class SourceReport:
    issues: list = field(default_factory=list)

    def add(self, level: str, fld: str, code: str, msg: str) -> None:
        self.issues.append(SourceIssue(level, fld, code, msg))

    @property
    def errors(self) -> list:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def infos(self) -> list:
        return [i for i in self.issues if i.level == "info"]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_source(name: str, type_: str, config: dict, existing_names: list,
                    *, probe_result=None) -> SourceReport:
    r = SourceReport()

    nm = (name or "").strip()
    if not nm:
        r.add("error", "name", "required", "Source name is required.")
    elif not SOURCE_NAME_RE.match(nm):
        r.add("error", "name", "format",
              "Name: 2 to 40 characters (letters, digits, _ or -), starting with a letter.")
    if nm and any((e or "").lower() == nm.lower() for e in existing_names):
        r.add("error", "name", "duplicate", f"A source named '{nm}' already exists.")

    if type_ not in CONNECTOR_TYPES:
        r.add("error", "type", "invalid", f"Unknown connector type '{type_}'.")
        return r

    conn = get_connector(type_)
    for issue in conn.validate(config or {}):
        r.issues.append(issue)

    if not conn.IMPLEMENTED:
        r.add("info", "type", "planned",
              f"The {conn.LABEL} connector is a preview: the source is saved with status "
              f"'planned' and skipped by the engine.")
    elif probe_result is not None and not probe_result.ok:
        err = probe_result.error or ""
        level = "warning" if "not found" in err.lower() else "error"
        r.add(level, "config", "probe_failed", f"Connection test failed: {err}")

    return r


def plain_summary(type_: str, config: dict, probe_result=None) -> str:
    conn = get_connector(type_)
    cfg = config or {}
    if type_ == "csv":
        head = f"CSV file `{cfg.get('path', '?')}`, delimiter '{cfg.get('delimiter', ',')}'"
    elif type_ == "excel":
        head = (f"Excel file `{cfg.get('path', '?')}`, sheet '{cfg.get('sheet', '0')}', "
                f"headers on row {cfg.get('header_row', 1)}")
    elif type_ == "json":
        head = f"JSON file `{cfg.get('path', '?')}` ({cfg.get('orient', 'records')})"
    elif type_ == "sql":
        head = f"{cfg.get('driver', 'sql')}://{cfg.get('host', '?')}/{cfg.get('database', '?')}"
    elif type_ == "url":
        head = f"Remote {cfg.get('format', 'csv')} at {cfg.get('url', '?')}"
    else:
        head = conn.LABEL
    if probe_result is not None and probe_result.ok:
        return f"{head} — {probe_result.row_count} rows, {len(probe_result.columns)} columns."
    if not conn.IMPLEMENTED:
        return f"{head} — preview connector, not executed."
    return head
