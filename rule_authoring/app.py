"""
rule_authoring/app.py

Web interface to manage the DQ Compass Control Catalogue and its data sources.

Run (from the project root):
    pip install -r requirements.txt
    python run_authoring.py
Then open http://127.0.0.1:5001

Sections:
  /            Home        -- dashboard: health, latest run, coverage, attention
  /catalogue   Catalogue   -- rule list + filters + inline validation
  /rule/...    rule forms
  /sources     Data Sources-- connector registry as cards
  /sources/... source forms
  /activity    Activity    -- unified catalogue + data source audit timeline
  /docs        Help        -- field reference
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from flask import (Flask, Response, flash, redirect, render_template, request,
                   send_file, url_for)

from connectors import describe_connectors, get_connector
from dq_engine import verify_run
from mapping import PRINCIPLES, build_mapping, mapping_csv
from reporting.scorecard import build_alerts as report_alerts
from reporting.scorecard import build_coverage as report_coverage
from reporting.scorecard import build_dataset_score as report_dataset_score
from reporting.scorecard import build_exception_summary as report_exception_summary
from reporting.scorecard import overall_dq_score, run_result_map
from rule_authoring import charts
from rule_authoring import schema, source_schema
from rule_authoring.source_store import SourceStore
from rule_authoring.store import CANONICAL_COLUMNS, CatalogueStore

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_CSV = ROOT / "control_catalogue.csv"
CHANGELOG = ROOT / "catalogue_changelog.jsonl"
DATASETS_CONFIG = ROOT / "datasets_config.yaml"
SOURCES_CHANGELOG = ROOT / "data_sources_changelog.jsonl"
EVIDENCE_DIR = ROOT / "evidence"

app = Flask(__name__)
app.secret_key = "dq-compass-authoring"  # local tool, no sensitive data
store = CatalogueStore(CATALOGUE_CSV, CHANGELOG)
source_store = SourceStore(DATASETS_CONFIG, SOURCES_CHANGELOG, store)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def current_user() -> str:
    return request.cookies.get("dq_editor", "").strip() or "anonymous"


def sources_index() -> dict:
    """name -> source dict, ACTIVE only (feeds rule validation + dropdowns)."""
    return {s["name"]: s for s in source_store.list_sources() if s["status"] == "active"}


def dataset_columns(idx: dict) -> dict:
    """name -> list of columns (probe), or None if unreadable / preview connector."""
    out = {}
    for name, s in idx.items():
        try:
            pr = get_connector(s["type"]).probe(s["config"], ROOT)
            out[name] = pr.columns if pr.ok else None
        except Exception:
            out[name] = None
    return out


def rule_reports(rules: list, idx: dict, cols: dict) -> dict:
    out = {}
    for r in rules:
        others = [x for x in rules if x["rule_id"] != r["rule_id"]]
        out[r["rule_id"]] = schema.validate_rule(r, others, idx, cols)
    return out


def build_coverage(rules: list, idx: dict) -> dict:
    cov = {name: {t: [] for t in schema.CONTROL_TYPES} for name in idx}
    for r in rules:
        if r["active"] and r["dataset_scope"] in cov:
            cov[r["dataset_scope"]][r["control_type"]].append(r["rule_id"])
    return cov


def latest_run() -> dict | None:
    if not EVIDENCE_DIR.exists():
        return None
    dirs = [d for d in EVIDENCE_DIR.iterdir() if d.is_dir() and (d / "run_summary.json").exists()]
    if not dirs:
        return None
    newest = max(dirs, key=lambda d: d.stat().st_mtime)
    try:
        data = json.loads((newest / "run_summary.json").read_text())
    except Exception:
        return None
    counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
    for r in data.get("results", []):
        counts[r.get("status", "FAIL")] = counts.get(r.get("status", "FAIL"), 0) + 1
    return {
        "run_id": data.get("run_id", newest.name),
        "timestamp": data.get("run_timestamp_utc", ""),
        "total": len(data.get("results", [])),
        "counts": counts,
        "results": data.get("results", []),
    }


def merged_activity(limit: int | None = None) -> list:
    cat = [{**e, "scope": "rule", "ref": e.get("rule_id")} for e in store.history()]
    src = [{**e, "scope": "source", "ref": e.get("source")} for e in source_store.history()]
    entries = sorted(cat + src, key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit] if limit else entries


def list_runs() -> list:
    ledger = EVIDENCE_DIR / "runs_ledger.jsonl"
    if not ledger.exists():
        return []
    out = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        rd = EVIDENCE_DIR / e["run_id"]
        e["exists"] = (rd / "run_summary.json").exists()
        e["signed_off"] = (rd / "signoff.json").exists()
        e["verified"] = None
        vp = rd / "verification.json"
        if vp.exists():
            try:
                e["verified"] = json.loads(vp.read_text()).get("all_match")
            except ValueError:
                pass
        out.append(e)
    return list(reversed(out))


# Generic "how to fix" advice per dimension, used when the catalogue rule has no
# remediation_action of its own. Kept short and plain.
_FIX_HINTS = {
    "Completeness": "Populate the missing values at the source, or make the field "
                    "mandatory in the feeding system. If a blank is legitimate, add a "
                    "tolerance threshold to the rule.",
    "Validity": "Correct the offending values at the source, or — if they are "
                "legitimate — extend the rule's allowed list / pattern / range so it "
                "recognises them.",
    "Uniqueness": "De-duplicate the records at the source and investigate why the key "
                  "repeats. If the key is meant to be composite, add the missing "
                  "column(s) to the rule.",
    "Consistency": "Load the missing reference records, fix the mismatched key, or "
                   "re-sync the reference dataset before this feed runs.",
    "Timeliness": "Investigate the delay in the upstream feed. If the lag is expected, "
                  "raise max_lag_days or change the rule's reference date.",
    "Reconciliation": "Escalate the gap to the owning team; check for missing rows on "
                      "either side and unit/scale differences. Widen tolerance_pct only "
                      "if the residual difference is genuinely acceptable.",
}


def _exception_focus(control_type: str, params: dict) -> list:
    """The column(s) the rule actually tests — shown first and highlighted in the
    exception table so the failing values are obvious in a wide dataset."""
    p = params or {}
    cols = []
    for k in ("field", "key"):
        if p.get(k):
            cols.append(str(p[k]))
    for k in p.get("keys", []) or []:
        cols.append(str(k))
    if p.get("ref_field") and str(p["ref_field"]) not in cols:
        cols.append(str(p["ref_field"]))
    # engine-added helper columns on the exception frame
    cols += [c for c in ("lag_days", "delta", "delta_pct", "_merge",
                         "_source_value", "_target_value") ]
    return cols


def _exception_note(control_type: str, params: dict) -> str:
    p = params or {}
    f = p.get("field") or p.get("key") or ", ".join(p.get("keys", []) or []) or "the field"
    if control_type == "Completeness":
        return f"Rows where {f} is null or blank."
    if control_type == "Validity":
        if p.get("allowed_values"):
            return f"Rows where {f} is not in the allowed set " \
                   f"({', '.join(map(str, p['allowed_values']))})."
        if p.get("regex"):
            return f"Rows where {f} does not match the pattern {p['regex']!r}."
        lo, hi = p.get("min_val", "-∞"), p.get("max_val", "+∞")
        return f"Rows where {f} is outside [{lo}, {hi}]."
    if control_type == "Uniqueness":
        return f"Rows that share a duplicated value of ({f})."
    if control_type == "Consistency":
        return f"Rows where {f} has no match in {p.get('ref_field', 'the reference')}."
    if control_type == "Timeliness":
        return f"Rows where {f} is older than {p.get('max_lag_days', '?')} day(s) " \
               f"(see lag_days)."
    if control_type == "Reconciliation":
        return "Rows missing on one side, or whose value gap exceeds tolerance " \
               "(see delta_pct)."
    return "Records that failed the control."


def load_run(run_id: str):
    rd = EVIDENCE_DIR / run_id
    sf = rd / "run_summary.json"
    if not sf.exists():
        return None
    summary = json.loads(sf.read_text())

    def _read_json(name):
        p = rd / name
        try:
            return json.loads(p.read_text()) if p.exists() else None
        except ValueError:
            return None

    cat_by_id = {x["rule_id"]: x for x in store.list_rules()}
    _MAX_OTHER_COLS = 8

    for r in summary.get("results", []):
        cat = cat_by_id.get(r["rule_id"], {})
        params = (r.get("rule_configuration_snapshot") or {}).get("params") or {}
        # per-rule "how to fix" advice
        rem = (cat.get("remediation_action") or "").strip()
        r["fix_advice"] = rem or _FIX_HINTS.get(r["control_type"], "")
        r["fix_advice_source"] = "catalogue" if rem else "generic"
        r["remediation_action"] = rem
        r["kpi"] = cat.get("kpi", "")
        r["threshold_text"] = cat.get("threshold", "")

        r["exceptions_preview"] = None
        p = r.get("exceptions_evidence_path")
        if p and (rd / p).exists():
            try:
                edf = pd.read_csv(rd / p, low_memory=False)
                all_cols = [str(c) for c in edf.columns]
                focus = [c for c in _exception_focus(r["control_type"], params)
                         if c in all_cols]
                others = [c for c in all_cols if c not in focus]
                shown = focus + others[:_MAX_OTHER_COLS]
                r["exceptions_preview"] = {
                    "columns": shown,
                    "focus": focus,
                    "rows": edf[shown].head(25).astype(str).to_dict("records"),
                    "total": int(len(edf)),
                    "more_cols": max(0, len(others) - _MAX_OTHER_COLS),
                    "note": _exception_note(r["control_type"], params),
                    "download": p,
                }
            except Exception as exc:  # never let a preview problem hide the failure
                app.logger.warning("exception preview failed for %s: %r", r["rule_id"], exc)
                r["exceptions_preview"] = {
                    "columns": [], "focus": [], "rows": [],
                    "total": r.get("exception_count", 0), "more_cols": 0,
                    "note": _exception_note(r["control_type"], params),
                    "download": p, "unavailable": True,
                }

    counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
    for r in summary.get("results", []):
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    log_tail = []
    lp = rd / "run.log"
    if lp.exists():
        log_tail = lp.read_text(encoding="utf-8").splitlines()[-45:]

    try:
        coverage = report_coverage(rd).to_dict("records")
        dataset_score = report_dataset_score(rd).to_dict("records")
        exc_summary = report_exception_summary(rd).to_dict("records")
        alerts = report_alerts(rd)
    except Exception as exc:
        app.logger.warning("run report builders failed for %s: %r", run_id, exc)
        coverage, dataset_score, exc_summary, alerts = [], [], [], []

    return {
        "summary": summary,
        "counts": counts,
        "system_trace": _read_json("system_trace.json"),
        "verification": _read_json("verification.json"),
        "signoff": _read_json("signoff.json"),
        "log_tail": log_tail,
        "coverage": coverage,
        "dataset_score": dataset_score,
        "exception_summary": exc_summary,
        "alerts": alerts,
    }


# ---- rule form <-> dict --------------------------------------------------
def _maybe_num(s):
    try:
        f = float(s)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return s


def build_params(ctype: str, form) -> dict:
    g = lambda k: (form.get(k) or "").strip()
    if ctype == "Completeness":
        return {"field": g("p_field")}
    if ctype == "Validity":
        mode = g("p_validity_mode")
        p = {"field": g("p_field")}
        if mode == "allowed_values":
            p["allowed_values"] = schema.parse_list(g("p_allowed_values"))
        elif mode == "regex":
            p["regex"] = g("p_regex")
        elif mode == "range":
            if g("p_min_val"):
                p["min_val"] = _maybe_num(g("p_min_val"))
            if g("p_max_val"):
                p["max_val"] = _maybe_num(g("p_max_val"))
        return p
    if ctype == "Uniqueness":
        return {"keys": schema.parse_list(g("p_keys"))}
    if ctype == "Consistency":
        return {"field": g("p_field"), "ref_field": g("p_ref_field")}
    if ctype == "Timeliness":
        p = {"field": g("p_field")}
        if g("p_max_lag_days"):
            try:
                p["max_lag_days"] = int(g("p_max_lag_days"))
            except ValueError:
                p["max_lag_days"] = g("p_max_lag_days")
        p["reference_date"] = g("p_reference_date") or "today"
        return p
    if ctype == "Reconciliation":
        p = {"key": g("p_key"), "field": g("p_field"), "ref_field": g("p_ref_field")}
        if g("p_tolerance_pct"):
            p["tolerance_pct"] = _maybe_num(g("p_tolerance_pct"))
        return p
    return {}


def form_to_rule(form) -> dict:
    ctype = (form.get("control_type") or "").strip()
    params = build_params(ctype, form)
    ref_ds = (form.get("ref_dataset_scope") or "").strip()
    ds = (form.get("dataset_scope") or "").strip()
    tp = (form.get("threshold_pct") or "").strip()
    rule = {
        "rule_id": (form.get("rule_id") or "").strip(),
        "control_name": (form.get("control_name") or "").strip(),
        "control_type": ctype,
        "description": (form.get("description") or "").strip(),
        "dataset_scope": ds,
        "ref_dataset_scope": ref_ds,
        "severity": (form.get("severity") or "").strip(),
        "frequency": (form.get("frequency") or "").strip(),
        "owner": (form.get("owner") or "").strip(),
        "output_type": (form.get("output_type") or "").strip(),
        "kpi": (form.get("kpi") or "").strip(),
        "remediation_action": (form.get("remediation_action") or "").strip(),
        "regulatory_ref": (form.get("regulatory_ref") or "").strip(),
        "params": params,
        "threshold_pct": float(tp) if tp else None,
        "active": ("active" in form),
    }
    rule["data_element"] = schema.derive_data_element(ctype, params)
    rule["threshold"] = schema.derive_threshold_text(ctype, params, rule["threshold_pct"])
    rule["logic_definition"] = schema.derive_logic_definition(ctype, params, ds, ref_ds)
    return rule


def validate_rule(rule: dict) -> schema.ValidationReport:
    idx = sources_index()
    cols = dataset_columns(idx)
    others = [r for r in store.list_rules() if r["rule_id"] != rule["rule_id"]]
    return schema.validate_rule(rule, others, idx, cols)


# ---- source form <-> dict ---------------------------------------------
def form_to_source(form):
    type_ = (form.get("type") or "csv").strip()
    conn = get_connector(type_)
    config = {}
    for f in conn.FIELDS:
        key = f"cfg_{type_}__{f.name}"
        if f.kind == "bool":
            config[f.name] = bool(form.get(key))
        else:
            v = form.get(key)
            if v is not None and str(v).strip() != "":
                config[f.name] = str(v).strip()
    return (form.get("name") or "").strip(), type_, config


# --------------------------------------------------------------------------
# Home / dashboard
# --------------------------------------------------------------------------
@app.route("/")
def index():
    idx = sources_index()
    cols = dataset_columns(idx)
    rules = store.list_rules()
    reports = rule_reports(rules, idx, cols)
    coverage = build_coverage(rules, idx)
    all_src = source_store.list_sources()

    attention = []
    for r in rules:
        rep = reports[r["rule_id"]]
        if not rep.ok:
            attention.append({"kind": "rule", "ref": r["rule_id"], "text": rep.errors[0].message,
                              "href": url_for("rule_edit", rule_id=r["rule_id"])})
    for s in all_src:
        conn = get_connector(s["type"])
        if conn.IMPLEMENTED and s["status"] == "active":
            pr = conn.probe(s["config"], ROOT)
            if not pr.ok:
                attention.append({"kind": "source", "ref": s["name"], "text": pr.error,
                                  "href": url_for("source_edit", name=s["name"])})
        if s["status"] != "active":
            live = [rid for rid in source_store.used_by(s["name"]) if (store.get(rid) or {}).get("active")]
            if live:
                attention.append({"kind": "source", "ref": s["name"],
                                  "text": f"retired but {len(live)} active rule(s) depend on it",
                                  "href": url_for("sources")})

    health = {
        "rules_total": len(rules),
        "rules_active": sum(1 for r in rules if r["active"]),
        "rules_errors": sum(1 for rid in reports if not reports[rid].ok),
        "rules_warnings": sum(1 for rid in reports if reports[rid].ok and reports[rid].warnings),
        "sources_total": len(all_src),
        "sources_active": sum(1 for s in all_src if s["status"] == "active"),
        "sources_preview": sum(1 for s in all_src if s["status"] != "active"),
        "datasets": len(idx),
        "datasets_covered": sum(1 for n in coverage if any(coverage[n].values())),
        "connectors_impl": sum(1 for c in describe_connectors() if c["implemented"]),
        "connectors_total": len(describe_connectors()),
    }
    return render_template("dashboard.html", health=health, coverage=coverage,
                           control_types=schema.CONTROL_TYPES, latest=latest_run(),
                           attention=attention, recent=merged_activity(6),
                           active_nav="home", user=current_user())


# --------------------------------------------------------------------------
# Catalogue (rules)
# --------------------------------------------------------------------------
@app.route("/catalogue")
def catalogue():
    idx = sources_index()
    cols = dataset_columns(idx)
    rules = store.list_rules()
    reports = rule_reports(rules, idx, cols)
    coverage = build_coverage(rules, idx)
    enriched = [{"rule": r, "report": reports[r["rule_id"]]} for r in rules]
    health = {
        "total": len(rules),
        "active": sum(1 for r in rules if r["active"]),
        "with_errors": sum(1 for rid in reports if not reports[rid].ok),
        "with_warnings": sum(1 for rid in reports if reports[rid].ok and reports[rid].warnings),
        "datasets_covered": sum(1 for n in coverage if any(coverage[n].values())),
        "datasets": len(idx),
    }
    return render_template("catalogue.html", enriched=enriched, coverage=coverage,
                           control_types=schema.CONTROL_TYPES, severities=schema.SEVERITIES,
                           health=health, active_nav="catalogue", user=current_user())


@app.route("/rule/new")
def rule_new():
    idx = sources_index()
    blank = {c: "" for c in CANONICAL_COLUMNS}
    blank.update({
        "rule_id": schema.next_rule_id(store.list_rules()),
        "params": {}, "threshold_pct": None, "active": True,
        "severity": "Medium", "frequency": "Daily", "control_type": "Completeness",
    })
    return render_template("form.html", rule=blank, mode="new", report=None,
                           datasets=list(idx), dataset_columns=dataset_columns(idx),
                           schema=schema, active_nav="catalogue", user=current_user())


@app.route("/rule/<rule_id>/edit")
def rule_edit(rule_id):
    rule = store.get(rule_id)
    if rule is None:
        flash(f"Rule {rule_id} not found.", "error")
        return redirect(url_for("catalogue"))
    idx = sources_index()
    return render_template("form.html", rule=rule, mode="edit", report=None,
                           datasets=list(idx), dataset_columns=dataset_columns(idx),
                           schema=schema, active_nav="catalogue", user=current_user())


@app.route("/rule", methods=["POST"])
@app.route("/rule/<rule_id>", methods=["POST"])
def rule_save(rule_id=None):
    is_new = rule_id is None
    rule = form_to_rule(request.form)
    if not is_new:
        rule["rule_id"] = rule_id
    report = validate_rule(rule)
    if not report.ok:
        idx = sources_index()
        return render_template("form.html", rule=rule,
                               mode="new" if is_new else "edit", report=report,
                               datasets=list(idx), dataset_columns=dataset_columns(idx),
                               schema=schema, active_nav="catalogue", user=current_user()), 400
    store.upsert(rule, user=current_user(), note=(request.form.get("note") or "").strip())
    if report.warnings:
        flash(f"Rule {rule['rule_id']} saved with {len(report.warnings)} warning(s).", "warning")
    else:
        flash(f"Rule {rule['rule_id']} saved.", "success")
    return redirect(url_for("catalogue"))


@app.route("/rule/<rule_id>/delete", methods=["POST"])
def rule_delete(rule_id):
    try:
        store.delete(rule_id, user=current_user(), note=(request.form.get("note") or "").strip())
        flash(f"Rule {rule_id} deleted.", "success")
    except KeyError:
        flash(f"Rule {rule_id} not found.", "error")
    return redirect(url_for("catalogue"))


@app.route("/rule/<rule_id>/toggle", methods=["POST"])
def rule_toggle(rule_id):
    rule = store.get(rule_id)
    if rule is None:
        flash(f"Rule {rule_id} not found.", "error")
    else:
        store.set_active(rule_id, not rule["active"], user=current_user())
        flash(f"Rule {rule_id} {'deactivated' if rule['active'] else 'activated'}.", "success")
    return redirect(url_for("catalogue"))


# --------------------------------------------------------------------------
# Data sources
# --------------------------------------------------------------------------
@app.route("/sources")
def sources():
    all_src = source_store.list_sources()
    conns = {c["type"]: c for c in describe_connectors()}
    enriched = []
    for s in all_src:
        conn = get_connector(s["type"])
        probe = conn.probe(s["config"], ROOT) if (conn.IMPLEMENTED and s["status"] == "active") else None
        rep = source_schema.validate_source(
            s["name"], s["type"], s["config"],
            [x["name"] for x in all_src if x["name"] != s["name"]],
            probe_result=probe)
        enriched.append({
            "src": s, "conn": conns.get(s["type"], {"label": s["type"], "icon": "?"}),
            "probe": probe, "report": rep,
            "summary": source_schema.plain_summary(s["type"], s["config"], probe),
            "used_by": source_store.used_by(s["name"]),
        })
    health = {
        "total": len(all_src),
        "active": sum(1 for s in all_src if s["status"] == "active"),
        "retired": sum(1 for s in all_src if s["status"] == "retired"),
        "planned": sum(1 for s in all_src if s["status"] == "planned"),
        "implemented": sum(1 for c in describe_connectors() if c["implemented"]),
        "connectors": len(describe_connectors()),
    }
    return render_template("sources.html", enriched=enriched, health=health,
                           active_nav="sources", user=current_user())


@app.route("/sources/new")
def source_new():
    return render_template("source_form.html", mode="new",
                           src={"name": "", "type": "csv", "status": "active", "config": {}},
                           connectors=describe_connectors(), report=None,
                           active_nav="sources", user=current_user())


@app.route("/sources/<name>/edit")
def source_edit(name):
    s = source_store.get(name)
    if s is None:
        flash(f"Source {name} not found.", "error")
        return redirect(url_for("sources"))
    return render_template("source_form.html", mode="edit", src=s,
                           connectors=describe_connectors(), report=None,
                           active_nav="sources", user=current_user())


@app.route("/sources", methods=["POST"])
@app.route("/sources/<name>", methods=["POST"])
def source_save(name=None):
    is_new = name is None
    form_name, type_, config = form_to_source(request.form)
    if not is_new:
        form_name = name
    conn = get_connector(type_)
    probe = conn.probe(config, ROOT) if conn.IMPLEMENTED else None
    existing = [s["name"] for s in source_store.list_sources() if s["name"] != form_name]
    report = source_schema.validate_source(form_name, type_, config, existing,
                                           probe_result=probe)
    if not report.ok:
        return render_template("source_form.html",
                               mode="new" if is_new else "edit",
                               src={"name": form_name, "type": type_,
                                    "status": "active", "config": config},
                               connectors=describe_connectors(), report=report,
                               active_nav="sources", user=current_user()), 400

    prev = source_store.get(form_name)
    if prev and prev["status"] == "retired":
        status = "retired"
    elif not conn.IMPLEMENTED:
        status = "planned"
    else:
        status = "active"
    source_store.upsert(form_name, type_, config, user=current_user(),
                        note=(request.form.get("note") or "").strip(), status=status)
    flash(f"Source {form_name} saved.", "success")
    return redirect(url_for("sources"))


@app.route("/sources/probe", methods=["POST"])
def source_probe():
    _, type_, config = form_to_source(request.form)
    conn = get_connector(type_)
    pr = conn.probe(config, ROOT)
    return {
        "ok": pr.ok, "error": pr.error, "columns": pr.columns,
        "row_count": pr.row_count, "sample": pr.sample,
        "summary": source_schema.plain_summary(type_, config, pr),
        "implemented": conn.IMPLEMENTED,
    }


@app.route("/sources/<name>/retire", methods=["POST"])
def source_retire(name):
    try:
        affected = source_store.retire(name, user=current_user(),
                                       note=(request.form.get("note") or "").strip())
        if affected:
            flash(f"Source {name} retired. {len(affected)} rule(s) deactivated: "
                  f"{', '.join(affected)}.", "warning")
        else:
            flash(f"Source {name} retired.", "success")
    except KeyError:
        flash(f"Source {name} not found.", "error")
    return redirect(url_for("sources"))


@app.route("/sources/<name>/reactivate", methods=["POST"])
def source_reactivate(name):
    try:
        inactive = source_store.reactivate(name, user=current_user())
        if inactive:
            flash(f"Source {name} reactivated. {len(inactive)} dependent rule(s) still "
                  f"inactive: {', '.join(inactive)} — use \"reactivate rules\".", "warning")
        else:
            flash(f"Source {name} reactivated.", "success")
    except KeyError:
        flash(f"Source {name} not found.", "error")
    return redirect(url_for("sources"))


@app.route("/sources/<name>/reactivate-rules", methods=["POST"])
def source_reactivate_rules(name):
    done = source_store.reactivate_rules(source_store.used_by(name), user=current_user())
    flash(f"Reactivated {len(done)} rule(s): {', '.join(done) or '—'}.", "success")
    return redirect(url_for("sources"))


@app.route("/sources/<name>/purge", methods=["POST"])
def source_purge(name):
    if (request.form.get("confirm") or "").strip() != "PURGE":
        flash("Purge cancelled: confirmation text did not match.", "error")
        return redirect(url_for("sources"))
    try:
        affected = source_store.purge(name, user=current_user(),
                                      note=(request.form.get("note") or "").strip())
        flash(f"Source {name} purged. {len(affected)} rule(s) deactivated: "
              f"{', '.join(affected) or '—'}.", "warning")
    except KeyError:
        flash(f"Source {name} not found.", "error")
    return redirect(url_for("sources"))


@app.route("/sources/<name>/rename", methods=["POST"])
def source_rename(name):
    new = (request.form.get("new_name") or "").strip()
    if not source_schema.SOURCE_NAME_RE.match(new):
        flash("Invalid new name (2-40 chars, letters/digits/_/-, start with a letter).", "error")
        return redirect(url_for("sources"))
    try:
        touched = source_store.rename(name, new, user=current_user())
        flash(f"Source renamed to {new}. {len(touched)} rule(s) retargeted: "
              f"{', '.join(touched) or '—'}.", "success")
    except (KeyError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("sources"))


# --------------------------------------------------------------------------
# Runs (execution evidence + reporting)
# --------------------------------------------------------------------------
@app.route("/runs")
def runs():
    return render_template("runs.html", runs=list_runs(), latest=latest_run(),
                           active_nav="runs", user=current_user())


@app.route("/runs/<run_id>")
def run_detail(run_id):
    data = load_run(run_id)
    if data is None:
        flash(f"Run {run_id} not found.", "error")
        return redirect(url_for("runs"))
    return render_template("run_detail.html", run_id=run_id, active_nav="runs",
                           user=current_user(), **data)


@app.route("/runs/<run_id>/verify", methods=["POST"])
def run_verify(run_id):
    if not (EVIDENCE_DIR / run_id / "run_summary.json").exists():
        flash(f"Run {run_id} not found.", "error")
        return redirect(url_for("runs"))
    rep = verify_run(str(EVIDENCE_DIR), run_id)
    if rep["all_match"]:
        flash(f"Run {run_id[:8]} verified — reproducible, all {len(rep['checks'])} controls match.",
              "success")
    else:
        bad = [c["rule_id"] for c in rep["checks"] if not c["match"]]
        flash(f"Run {run_id[:8]} verification MISMATCH on: {', '.join(bad)}.", "error")
    return redirect(url_for("run_detail", run_id=run_id))


@app.route("/runs/<run_id>/signoff", methods=["POST"])
def run_signoff(run_id):
    rd = EVIDENCE_DIR / run_id
    if not (rd / "run_summary.json").exists():
        flash(f"Run {run_id} not found.", "error")
        return redirect(url_for("runs"))
    record = {
        "reviewed_by": current_user(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": (request.form.get("decision") or "acknowledged").strip(),
        "comment": (request.form.get("comment") or "").strip(),
    }
    (rd / "signoff.json").write_text(json.dumps(record, indent=2))
    flash(f"Run {run_id[:8]} signed off ({record['decision']}).", "success")
    return redirect(url_for("run_detail", run_id=run_id))


@app.route("/runs/<run_id>/file/<name>")
def download_run_file(run_id, name):
    p = EVIDENCE_DIR / run_id / Path(name).name
    if not (p.exists() and p.is_file()):
        flash("File not found.", "error")
        return redirect(url_for("run_detail", run_id=run_id))
    return send_file(p, as_attachment=True, download_name=Path(name).name)


def reporting_context(focus_run_id: str | None = None):
    """Assemble everything the Reporting page needs from the evidence runs.

    Every panel except the trend chart and the rule-reliability table is computed
    for ONE run -- the most recent by default, or `focus_run_id` when the user
    picks another from the run selector. The trend / reliability window is that
    run plus the 11 older ones; "previous run" is the run immediately before it.
    """
    runs = [r for r in list_runs() if r.get("exists")]
    if not runs:
        return None
    focus_idx = 0
    if focus_run_id:
        focus_idx = next((i for i, r in enumerate(runs) if r["run_id"] == focus_run_id), 0)
    latest = runs[focus_idx]
    prev = runs[focus_idx + 1] if focus_idx + 1 < len(runs) else None
    ld = EVIDENCE_DIR / latest["run_id"]
    pd_ = EVIDENCE_DIR / prev["run_id"] if prev else None

    score = overall_dq_score(ld)
    delta = round(score - overall_dq_score(pd_), 1) if pd_ else None

    latest_map = run_result_map(ld)
    n_rules = len(latest_map)
    n_pass = sum(1 for r in latest_map.values() if r["status"] == "PASS")
    total_exc = sum(r["exception_count"] for r in latest_map.values())

    window = runs[focus_idx:focus_idx + 12]
    trend = []
    for m in reversed(window):
        d = EVIDENCE_DIR / m["run_id"]
        c = m["counts"]
        trend.append({"label": m["timestamp"][5:10], "ts": m["timestamp"][:19],
                      "pass": c.get("PASS", 0), "fail": c.get("FAIL", 0), "error": c.get("ERROR", 0),
                      "score": overall_dq_score(d)})

    # exceptions grouped by owner (accountability) -- business audience
    exc = report_exception_summary(ld).to_dict("records")
    by_owner = sorted((e for e in exc if e["dimension"] == "owner"),
                      key=lambda e: -e["total_exceptions"])

    # 3-state coverage (controlled+passing / controlled+failing / not controlled)
    grid = build_coverage(store.list_rules(), sources_index())
    cov3 = {}
    for ds, cells in grid.items():
        cov3[ds] = {}
        for dim, ids in cells.items():
            if not ids:
                cov3[ds][dim] = {"state": "none", "ids": []}
            else:
                statuses = [latest_map.get(i, {}).get("status", "?") for i in ids]
                state = "fail" if any(s in ("FAIL", "ERROR") for s in statuses) else "pass"
                cov3[ds][dim] = {"state": state, "ids": ids}
    covered = sum(1 for ds in cov3 if any(c["state"] != "none" for c in cov3[ds].values()))

    age_h = None
    try:
        t = datetime.fromisoformat(latest["timestamp"])
        age_h = (datetime.now(timezone.utc) - t).total_seconds() / 3600
    except Exception:
        pass

    return dict(
        latest=latest, prev=prev,
        runs=runs, focus_id=latest["run_id"], is_latest=(focus_idx == 0),
        score=score, delta=delta,
        pass_rate=round(100 * n_pass / n_rules, 1) if n_rules else 0.0,
        n_rules=n_rules, n_pass=n_pass, n_fail=latest["counts"].get("FAIL", 0),
        n_error=latest["counts"].get("ERROR", 0), total_exc=total_exc,
        alerts=report_alerts(ld), age_h=age_h,
        ds_scores=report_dataset_score(ld).to_dict("records"),
        cov3=cov3, covered=covered, datasets_total=len(cov3),
        control_types=schema.CONTROL_TYPES,
        trend=trend, by_owner=by_owner,
        score_series=[t["score"] for t in trend],
    )


@app.route("/reporting")
def reporting():
    return render_template("reporting.html",
                           ctx=reporting_context(request.args.get("run")), charts=charts,
                           active_nav="reporting", user=current_user())


@app.route("/run-now", methods=["POST"])
def run_now():
    try:
        r1 = subprocess.run([sys.executable, "dq_engine.py"], cwd=str(ROOT),
                            capture_output=True, text=True, timeout=180)
        subprocess.run([sys.executable, "reporting/scorecard.py"], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=90)
        if r1.returncode == 0:
            first = (r1.stdout.strip().splitlines() or [""])[0]
            flash(f"Engine run complete. {first}", "success")
        else:
            flash(f"Engine run failed: {r1.stderr.strip()[-300:]}", "error")
    except Exception as exc:
        flash(f"Could not run the engine: {exc}", "error")
    return redirect(url_for("runs"))


# --------------------------------------------------------------------------
# Activity / docs / misc
# --------------------------------------------------------------------------
@app.route("/activity")
def activity():
    scope = request.args.get("scope", "all")
    entries = merged_activity()
    if scope in ("rule", "source"):
        entries = [e for e in entries if e["scope"] == scope]
    return render_template("activity.html", entries=entries, scope=scope,
                           active_nav="activity", user=current_user())


@app.route("/mapping")
def mapping_view():
    return render_template("mapping.html", rows=build_mapping(), principles=PRINCIPLES,
                           active_nav="mapping", user=current_user())


@app.route("/download/mapping")
def download_mapping():
    text = mapping_csv()
    if not text:
        flash("No active rule to map.", "error")
        return redirect(url_for("mapping_view"))
    return Response(text, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=supervisory_mapping.csv"})


@app.route("/docs")
def docs():
    return render_template("docs.html", schema=schema, param_spec=schema.PARAM_SPEC,
                           connectors=describe_connectors(), active_nav="docs",
                           user=current_user())


@app.route("/preview", methods=["POST"])
def preview():
    rule = form_to_rule(request.form)
    return {
        "plain": schema.explain_plain_language(rule["control_type"], rule["params"],
                                               rule["dataset_scope"], rule["ref_dataset_scope"]),
        "logic": rule["logic_definition"],
        "data_element": rule["data_element"],
        "threshold": rule["threshold"],
    }


@app.route("/set-editor", methods=["POST"])
def set_editor():
    resp = redirect(request.referrer or url_for("index"))
    resp.set_cookie("dq_editor", (request.form.get("editor") or "").strip(),
                    max_age=60 * 60 * 24 * 30)
    return resp


@app.route("/download/catalogue")
def download_catalogue():
    return send_file(CATALOGUE_CSV, as_attachment=True, download_name="control_catalogue.csv")


@app.route("/download/changelog")
def download_changelog():
    if not CHANGELOG.exists():
        return Response("", mimetype="text/plain")
    return send_file(CHANGELOG, as_attachment=True, download_name="catalogue_changelog.jsonl")


@app.route("/download/sources")
def download_sources():
    return send_file(DATASETS_CONFIG, as_attachment=True, download_name="datasets_config.yaml")


@app.route("/download/sources-changelog")
def download_sources_changelog():
    if not SOURCES_CHANGELOG.exists():
        return Response("", mimetype="text/plain")
    return send_file(SOURCES_CHANGELOG, as_attachment=True,
                     download_name="data_sources_changelog.jsonl")


@app.route("/download/report/<name>")
def download_report(name):
    allowed = {"scorecard.csv", "scorecard.html", "exceptions_detail.csv", "coverage.csv",
               "exception_summary.csv", "dataset_score.csv", "trend.csv", "alerts.json"}
    if name not in allowed:
        flash("Unknown report file.", "error")
        return redirect(url_for("runs"))
    p = ROOT / "reporting" / name
    if not p.exists():
        flash(f"{name} not generated yet — run the engine + scorecard.", "error")
        return redirect(url_for("runs"))
    return send_file(p, as_attachment=True, download_name=name)
