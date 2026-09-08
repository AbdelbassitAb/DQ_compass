"""
migrate_sources.py

Bring datasets_config.yaml to the rich per-source schema used by the Data
Sources UI:

    orders:
      type: csv
      status: active
      config: {path: ..., delimiter: ",", encoding: utf-8, header_row: 1}
      created_at: ...
      updated_at: ...

Idempotent. Saves the original to .backup.yaml. The engine reads both the old
flat shape and the new one, so nothing breaks if you skip this.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from connectors import normalize_entry

ROOT = Path(__file__).resolve().parent
YAML_PATH = ROOT / "datasets_config.yaml"


def main() -> None:
    raw = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8")) or {}
    if raw and all(isinstance(v, dict) and "config" in v for v in raw.values()):
        print("datasets_config.yaml already in rich format - nothing to do.")
        return
    shutil.copy(YAML_PATH, YAML_PATH.with_suffix(".backup.yaml"))
    now = datetime.now(timezone.utc).isoformat()
    doc = {}
    for name, entry in raw.items():
        e = normalize_entry(entry)
        doc[name] = {
            "type": e["type"],
            "status": e.get("status", "active"),
            "config": e.get("config", {}),
            "created_at": now,
            "updated_at": now,
        }
    YAML_PATH.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
                         encoding="utf-8")
    print(f"Migrated {len(doc)} sources -> {YAML_PATH.name} "
          f"(backup: {YAML_PATH.with_suffix('.backup.yaml').name})")


if __name__ == "__main__":
    main()
