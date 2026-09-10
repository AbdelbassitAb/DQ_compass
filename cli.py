"""
cli.py — the `dqcompass` command line.

    dqcompass run                    execute the catalogue, write an Evidence Pack
    dqcompass verify <run_id>        re-execute a past run from its snapshots and
                                     assert identical results
    dqcompass report                 (re)generate the Reporting Layer outputs
    dqcompass mapping                write reporting/supervisory_mapping.csv
    dqcompass catalogue-validate     validate every rule against the meta-catalogue
    dqcompass gate [--severity High] run + fail (exit 1) if any control at/above
                                     that severity broke -- for CI pipelines
    dqcompass serve                  start the authoring web app (127.0.0.1:5001)

Run from the project root. Installed as a console script via pyproject.toml.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from connectors import get_connector, normalize_entry
from rule_authoring import schema
from rule_authoring.store import CatalogueStore

ROOT = Path(__file__).resolve().parent
_SEV_ORDER = {"Low": 1, "Medium": 2, "High": 3}


def _active_sources() -> tuple[dict, dict]:
    raw = yaml.safe_load((ROOT / "datasets_config.yaml").read_text(encoding="utf-8")) or {}
    idx, cols = {}, {}
    for name, entry in raw.items():
        e = normalize_entry(entry)
        if e.get("status") != "active":
            continue
        idx[name] = e
        try:
            pr = get_connector(e["type"]).probe(e.get("config", {}), ROOT)
            cols[name] = pr.columns if pr.ok else None
        except Exception:
            cols[name] = None
    return idx, cols


def _catalogue_validate() -> int:
    store = CatalogueStore(ROOT / "control_catalogue.csv", ROOT / "catalogue_changelog.jsonl")
    idx, cols = _active_sources()
    rules = store.list_rules()
    n_err = n_warn = 0
    for r in rules:
        others = [x for x in rules if x["rule_id"] != r["rule_id"]]
        rep = schema.validate_rule(r, others, idx, cols)
        for i in rep.errors:
            n_err += 1
            print(f"  ERROR  {r['rule_id']:6s} [{i.field}] {i.message}")
        for i in rep.warnings:
            n_warn += 1
            print(f"  warn   {r['rule_id']:6s} [{i.field}] {i.message}")
    print(f"{len(rules)} rules · {n_err} error(s) · {n_warn} warning(s)")
    return 1 if n_err else 0


def _gate(min_severity: str) -> int:
    from dq_engine import DQEngine
    thr = _SEV_ORDER.get(min_severity, 3)
    summary = DQEngine("control_catalogue.csv", "datasets_config.yaml", "evidence").run()
    breaks = [r for r in summary["results"]
              if r["status"] in ("FAIL", "ERROR") and _SEV_ORDER.get(r["severity"], 1) >= thr]
    for r in breaks:
        print(f"  {r['status']:5s} {r['rule_id']:6s} [{r['severity']}] {r['control_name']}")
    if breaks:
        print(f"GATE FAILED — {len(breaks)} control(s) at severity >= {min_severity} broke "
              f"(run {summary['run_id'][:8]}, hash {summary['run_hash']}).")
        return 1
    print(f"GATE PASSED — no control at severity >= {min_severity} broke "
          f"(run {summary['run_id'][:8]}).")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "help"

    if cmd == "run":
        from dq_engine import DQEngine
        s = DQEngine("control_catalogue.csv", "datasets_config.yaml", "evidence").run()
        print(f"run {s['run_id']}  hash {s['run_hash']}  {s['rules_executed']} rules executed")
        return 0

    if cmd == "verify":
        if len(argv) < 2:
            print("usage: dqcompass verify <run_id>")
            return 2
        from dq_engine import verify_run
        rep = verify_run("evidence", argv[1])
        print("REPRODUCIBLE" if rep["all_match"] else "MISMATCH")
        return 0 if rep["all_match"] else 1

    if cmd == "report":
        from reporting import scorecard
        scorecard.main("latest")
        return 0

    if cmd == "mapping":
        import mapping
        out = ROOT / "reporting" / "supervisory_mapping.csv"
        out.write_text(mapping.mapping_csv(), encoding="utf-8")
        print(f"wrote {out}")
        return 0

    if cmd == "catalogue-validate":
        return _catalogue_validate()

    if cmd == "gate":
        sev = argv[argv.index("--severity") + 1] if "--severity" in argv else "High"
        return _gate(sev)

    if cmd == "serve":
        from rule_authoring.app import app
        app.run(host="127.0.0.1", port=5001, debug=True)
        return 0

    print(__doc__)
    return 0 if cmd in ("help", "-h", "--help") else 2


if __name__ == "__main__":
    raise SystemExit(main())
