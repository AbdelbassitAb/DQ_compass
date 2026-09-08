"""
build_report.py — generate the DQ Compass implementation & brief-compliance PDF.

    pip install reportlab
    python docs/build_report.py

Output: docs/DQ_Compass_Implementation_and_Compliance.pdf
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

OUT = Path(__file__).resolve().parent / "DQ_Compass_Implementation_and_Compliance.pdf"

INK = colors.HexColor("#14161c")
MUTED = colors.HexColor("#5b6270")
ACCENT = colors.HexColor("#c1122a")
LINE = colors.HexColor("#d3d7df")
HEADBG = colors.HexColor("#f0f1f4")
OKBG = colors.HexColor("#e7f6ec")
OK = colors.HexColor("#128a4b")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold",
                            fontSize=24, leading=28, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=12, leading=16,
                               textColor=MUTED, spaceAfter=2),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=20,
                         textColor=ACCENT, spaceBefore=16, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                         textColor=INK, spaceBefore=12, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                         textColor=INK, spaceBefore=8, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5,
                           textColor=INK, spaceAfter=5, alignment=TA_LEFT),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.5, leading=11.5,
                            textColor=MUTED, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, leading=13,
                             textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8, leading=11,
                           textColor=INK, backColor=colors.HexColor("#f5f5f7"),
                           borderPadding=6, spaceBefore=3, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=7.6, leading=9.8,
                           textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=7.6, leading=9.8,
                            textColor=INK),
    "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=7.6, leading=9.8,
                            textColor=INK),
}


def _fix(t: str) -> str:
    """Substitute glyphs the built-in Helvetica Type1 font cannot render."""
    return (str(t)
            .replace("&le;", "&lt;=").replace("&ge;", "&gt;=")
            .replace("&rarr;", " -&gt; ").replace("&larr;", " &lt;- ")
            .replace("&harr;", " &lt;-&gt; ").replace("&asymp;", "~")
            .replace("&times;", " x ").replace("✓", "YES"))


def P(text, s="body"):
    return Paragraph(_fix(text), S[s])


def bullets(items, s="bullet"):
    return [Paragraph(_fix(f"&bull;&nbsp;&nbsp;{it}"), S[s]) for it in items]


def code(text):
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    return Paragraph(safe, S["code"])


def table(headers, rows, widths, header_bg=HEADBG, zebra=True):
    data = [[Paragraph(_fix(h), S["cellh"]) for h in headers]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else Paragraph(_fix(str(c)), S["cell"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, LINE),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafb")))
    t.setStyle(TableStyle(st))
    return t


def comp(rows):
    """Compliance matrix table: (requirement, brief_ref, how, evidence)."""
    w = [34 * mm, 15 * mm, 73 * mm, 34 * mm, 13 * mm]
    data = [[Paragraph(_fix(h), S["cellh"]) for h in
             ["Brief requirement", "Ref", "How DQ Compass satisfies it", "Evidence / artefact", "Met"]]]
    for req, ref, how, ev in rows:
        data.append([
            Paragraph(_fix(req), S["cell"]), Paragraph(_fix(ref), S["cell"]),
            Paragraph(_fix(how), S["cell"]), Paragraph(_fix(ev), S["cell"]),
            Paragraph('<font color="#128a4b"><b>YES</b></font>', S["cellb"]),
        ])
    t = Table(data, colWidths=w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADBG),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("BACKGROUND", (4, 1), (4, -1), OKBG),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# ==========================================================================
# Document assembly
# ==========================================================================
story = []
A = story.append


def H1(t): A(P(t, "h1"))
def H2(t): A(P(t, "h2"))
def H3(t): A(P(t, "h3"))
def BODY(t): A(P(t, "body"))
def SMALL(t): A(P(t, "small"))
def BUL(items): [A(x) for x in bullets(items)]
def SP(n=6): A(Spacer(1, n))
def PB(): A(PageBreak())


# ---- cover ----
A(Spacer(1, 60))
A(P("DQ Compass", "title"))
A(P("Implementation &amp; Brief-Compliance Report", "h1"))
A(Spacer(1, 10))
A(P("MBA-ESG / SG GSC Datathon 2026 &mdash; <i>DQ Compass: Building a Plug-and-Play "
    "Data Quality Control Layer for EUCs</i>", "subtitle"))
A(P("Working Group 1", "subtitle"))
A(P(f"Generated {date.today().isoformat()}", "subtitle"))
A(Spacer(1, 26))
A(P("This document describes, in detail, every component of the DQ Compass prototype and "
    "cross-references it against the datathon brief (use case document V2 and its "
    "Appendices A, B and C). Section 5 is a line-by-line compliance matrix.", "body"))
A(Spacer(1, 14))
A(table(
    ["Layer", "Component", "Files"],
    [["1 &mdash; Control Catalogue (DEFINES)", "Rule repository + meta-catalogue validation",
      "control_catalogue.csv, rule_authoring/schema.py"],
     ["2 &mdash; Data Quality Engine (EXECUTES)", "Dynamic control execution + threshold logic",
      "dq_engine.py, controls.py, connectors.py"],
     ["3 &mdash; Reporting Layer (REPORTS)", "Scorecards, coverage, exceptions, supervisory mapping",
      "reporting/scorecard.py, mapping.py"],
     ["4 &mdash; Audit Layer (EVIDENCES)", "Evidence Pack per run, hash-chained ledger, verification",
      "evidence/&lt;run_id&gt;/, evidence/runs_ledger.jsonl"],
     ["Governance / operations", "Web app, audit changelogs, CLI, CI adapters",
      "rule_authoring/, cli.py, docs/DEPLOYMENT.md"]],
    [46 * mm, 60 * mm, 62 * mm]))
PB()

# ---- 1. Executive summary ----
H1("1 &nbsp; Executive summary")
BODY("DQ Compass is a generic, reusable and auditable data quality control layer that plugs "
     "into any End-User Computing (EUC) tool without writing new code. It implements the four "
     "lifecycle stages the brief requires &mdash; <b>Definition &rarr; Execution &rarr; Reporting "
     "&rarr; Audit</b> &mdash; end to end, and adds the governance surface (a validated authoring "
     "application, hash-chained change logs, a run ledger, an independent-verification command "
     "and an auto-generated supervisory mapping) that turns a set of checks into a "
     "&ldquo;simulation of industrial-grade Data Quality governance.&rdquo;")
H3("What was built")
BUL([
    "<b>Control Catalogue</b> &mdash; a 21-column CSV: the 14 mandatory Appendix A.2 attributes, "
    "a <font face='Courier'>regulatory_ref</font> column for the supervisory mapping, and six "
    "technical columns. <font face='Courier'>logic_definition</font>, "
    "<font face='Courier'>data_element</font> and <font face='Courier'>threshold</font> are generated.",
    "<b>Meta-catalogue</b> (<font face='Courier'>rule_authoring/schema.py</font>) &mdash; ~30 "
    "validation checks applied to every rule before it is saved: structure, controlled "
    "vocabularies, dataset declared, columns actually present (probed), and per-type parameter "
    "consistency; plus non-blocking warnings.",
    "<b>Data source registry</b> (<font face='Courier'>datasets_config.yaml</font> + "
    "<font face='Courier'>connectors.py</font>) &mdash; a pluggable connector abstraction. CSV and "
    "Excel are implemented; JSON, SQL database and SharePoint/Drive/URL are shown as selectors "
    "and saved with status <font face='Courier'>preview</font>.",
    "<b>Data Quality Engine</b> (<font face='Courier'>dq_engine.py</font> + "
    "<font face='Courier'>controls.py</font>) &mdash; reads the catalogue, dispatches by "
    "<font face='Courier'>control_type</font> to one of six generic control functions, applies "
    "the tolerance threshold, skips inactive rules, and never crashes on a missing source "
    "(it records an <font face='Courier'>ERROR</font> result and continues).",
    "<b>Audit Layer</b> &mdash; an Evidence Pack per run covering all ten Appendix B.2 components, "
    "an append-only <font face='Courier'>runs_ledger.jsonl</font> chained "
    "<font face='Courier'>previous_run_hash &rarr; run_hash</font>, and "
    "<font face='Courier'>dqcompass verify &lt;run_id&gt;</font> which re-executes a past run from "
    "its stored config and dataset snapshots and asserts identical results.",
    "<b>Reporting Layer</b> &mdash; eight artefacts from <font face='Courier'>scorecard.py</font> "
    "(scorecard, exceptions, coverage, exception summary, dataset score, trend, alerts) and the "
    "Appendix C supervisory mapping from <font face='Courier'>mapping.py</font>.",
    "<b>Authoring web application</b> (<font face='Courier'>rule_authoring/</font>) &mdash; seven "
    "sections (Home, Catalogue, Data Sources, Runs, Mapping, Activity, Help) with full CRUD, "
    "inline validation, a coverage matrix, per-run drill-down, verify and sign-off, and two "
    "hash-chained audit changelogs.",
    "<b>CLI &amp; deployment</b> (<font face='Courier'>cli.py</font>, "
    "<font face='Courier'>pyproject.toml</font>) &mdash; the <font face='Courier'>dqcompass</font> "
    "command (<font face='Courier'>run / verify / report / mapping / catalogue-validate / gate / "
    "serve</font>) plus cron, Airflow, CI-gate and notification recipes.",
    "<b>Tests</b> &mdash; 38 automated tests across three suites (schema 21, connectors 11, "
    "engine 6).",
])
PB()

# ---- 2. Architecture ----
H1("2 &nbsp; Architecture")
H2("2.1 &nbsp; The four layers and the files that implement them")
A(table(
    ["Layer (brief &sect;4)", "Responsibility", "Implementation"],
    [["[1] Control Catalogue &sect;4.2 / &sect;6 / App. A",
      "Structured repository of all DQ rules; parameterised, reusable, centrally governed",
      "control_catalogue.csv (21 cols); authored &amp; validated through rule_authoring/ "
      "(schema.py = the meta-catalogue); store.py = atomic writes + changelog"],
     ["[2] Data Quality Engine &sect;4.1 / &sect;7.1",
      "Execute multiple control types, apply rules dynamically to any dataset, produce "
      "structured reproducible outputs",
      "dq_engine.py (dispatch, threshold, active filter, error handling); controls.py "
      "(6 generic functions); connectors.py (source loading)"],
     ["[3] Reporting Layer &sect;4.3 / &sect;5.2 / App. C",
      "Scorecards, exception reports, control coverage views; supervisory mapping",
      "reporting/scorecard.py (8 outputs incl. scorecard.html); mapping.py "
      "(supervisory_mapping.csv); surfaced on the Runs and Mapping pages"],
     ["[4] Audit Layer &sect;4.4 / &sect;7.2 / &sect;7.3 / App. B",
      "Reproducible, time-stamped, independently verifiable evidence of every execution",
      "evidence/&lt;run_id&gt;/ (Evidence Pack); evidence/runs_ledger.jsonl (hash chain); "
      "dq_engine.verify_run(); signoff via the app"]],
    [40 * mm, 60 * mm, 68 * mm]))
SP(8)
H2("2.2 &nbsp; File map")
A(table(
    ["File / directory", "Purpose"],
    [["control_catalogue.csv", "The rule repository (21 canonical columns)."],
     ["datasets_config.yaml", "The data source registry: per source a connector type, status and config."],
     ["connectors.py", "Connector abstraction + registry. CSV/Excel implemented; JSON/SQL/URL preview."],
     ["controls.py", "Six generic control functions + CONTROL_REGISTRY (control_type &rarr; function)."],
     ["dq_engine.py", "The engine: run(), per-rule execution, Evidence Pack, run ledger, verify_run()."],
     ["reporting/scorecard.py", "Reporting Layer: scorecard.csv/.html, exceptions_detail.csv, coverage.csv, "
      "exception_summary.csv, dataset_score.csv, trend.csv, alerts.json."],
     ["mapping.py", "Appendix C supervisory mapping (supervisory_mapping.csv)."],
     ["cli.py", "The dqcompass console command."],
     ["rule_authoring/schema.py", "The meta-catalogue: validation of every rule + generation of the "
      "auditor-readable columns + inline help text."],
     ["rule_authoring/store.py", "Catalogue persistence: atomic CSV write, hash-chained "
      "catalogue_changelog.jsonl, CRUD, dataset re-targeting on rename."],
     ["rule_authoring/source_schema.py", "Validation of a data source registration + plain-language summary."],
     ["rule_authoring/source_store.py", "Data source persistence + data_sources_changelog.jsonl + the "
      "retire / reactivate / purge / rename policy with rule cascades."],
     ["rule_authoring/app.py", "The Flask web application (all routes)."],
     ["rule_authoring/templates/, static/", "The 12 page templates + CSS/JS (design-token system, "
      "light/dark, list filters)."],
     ["migrate_catalogue.py / migrate_sources.py", "One-time schema migrations (also regenerate "
      "derived columns)."],
     ["docs/ARCHITECTURE.md, docs/DEPLOYMENT.md", "Design rationale + deployment recipes."],
     ["tests/", "test_schema.py (21), test_connectors.py (11), test_engine.py (6)."],
     ["sample_data/", "orders.csv, orders_reference.csv, customers.csv with 6 deliberate anomalies."]],
    [52 * mm, 116 * mm]))
SP(8)
H2("2.3 &nbsp; Data flow of one run")
BUL([
    "<b>Load</b> &mdash; <font face='Courier'>DQEngine</font> reads "
    "<font face='Courier'>control_catalogue.csv</font> and "
    "<font face='Courier'>datasets_config.yaml</font>.",
    "<b>Per active rule</b> &mdash; resolve the connector, load the dataset, compute its SHA-256 "
    "hash and write an exact copy to <font face='Courier'>snapshots/&lt;name&gt;.csv</font>; call "
    "the generic control function for the rule&rsquo;s <font face='Courier'>control_type</font>; "
    "apply <font face='Courier'>threshold_pct</font>.",
    "<b>Write per rule</b> &mdash; <font face='Courier'>&lt;rule&gt;_result.json</font> (status, "
    "metrics, config snapshot, resolved execution parameters, dataset hashes) and "
    "<font face='Courier'>&lt;rule&gt;_exceptions.csv</font>.",
    "<b>Write per run</b> &mdash; <font face='Courier'>system_trace.json</font>, "
    "<font face='Courier'>run_log.jsonl</font> + <font face='Courier'>run.log</font>, then "
    "<font face='Courier'>run_summary.json</font> with "
    "<font face='Courier'>run_hash = SHA-256(previous_run_hash + canonical(run_summary))</font>; "
    "append <font face='Courier'>runs_ledger.jsonl</font>.",
    "<b>Verify (on demand)</b> &mdash; <font face='Courier'>verify_run()</font> re-executes the "
    "stored rule configuration against the stored snapshots and asserts status + exception counts "
    "are unchanged; writes <font face='Courier'>verification.json</font>.",
])
PB()

# ---- 3. Component detail ----
H1("3 &nbsp; Component detail")

H2("3.1 &nbsp; Control Catalogue &mdash; control_catalogue.csv")
BODY("One row per rule. Columns 1&ndash;14 are the mandatory Appendix A.2 attributes; "
     "<font face='Courier'>regulatory_ref</font> feeds the Appendix C mapping; the remaining six "
     "are technical. <font face='Courier'>logic_definition</font> (pseudo-SQL), "
     "<font face='Courier'>data_element</font> and <font face='Courier'>threshold</font> (plain "
     "text) are <b>generated</b> from the control type and parameters when a rule is saved, so the "
     "CSV is self-describing for an auditor without exposing the technical "
     "<font face='Courier'>params</font> JSON.")
A(table(
    ["#", "Column", "Meaning"],
    [["1", "rule_id", "Unique, stable identifier (e.g. DQ07). Key in catalogue, evidence and audit log."],
     ["2", "control_name", "Short readable name (3&ndash;80 chars)."],
     ["3", "control_type", "One of the 6 DQ dimensions. Drives which parameters apply."],
     ["4", "description", "Business objective of the control (&ge;10 chars)."],
     ["5", "logic_definition", "Formal rule logic as pseudo-SQL. <i>Generated.</i>"],
     ["6", "dataset_scope", "Dataset the rule applies to (must be declared in datasets_config.yaml)."],
     ["7", "data_element", "Field(s) tested. <i>Generated</i> from params."],
     ["8", "threshold", "Acceptance criteria in plain words. <i>Generated.</i>"],
     ["9", "severity", "High / Medium / Low &mdash; drives prioritisation and the traffic light."],
     ["10", "frequency", "Execution periodicity (controlled vocabulary of 7 values)."],
     ["11", "owner", "Responsible role (Data Owner / Data Steward / Control Owner &hellip;)."],
     ["12", "output_type", "Nature of the output on anomaly (error dataset / report / alert &hellip;)."],
     ["13", "kpi", "Quantifiable indicator (e.g. % completeness)."],
     ["14", "remediation_action", "Action expected on failure (&ge;10 chars). Also carried into alerts.json."],
     ["15", "regulatory_ref", "Supervisory requirement satisfied (e.g. a BCBS 239 principle). Feeds "
      "the Appendix C mapping; default derived from the dimension when blank."],
     ["16", "ref_dataset_scope", "Reference dataset for Consistency / Reconciliation."],
     ["17", "params", "Machine parameters as JSON (field, keys, regex, thresholds, &hellip;). "
      "Generated by the form; never hand-typed."],
     ["18", "threshold_pct", "Tolerance: % of records in anomaly below which the control still passes."],
     ["19", "active", "TRUE/FALSE. The engine skips FALSE; the rule stays in the catalogue and history."],
     ["20&ndash;21", "created_at / updated_at", "UTC timestamps."]],
    [10 * mm, 34 * mm, 124 * mm]))
SP(6)
H3("The six DQ dimensions (control functions in controls.py)")
A(table(
    ["Dimension", "Function", "Logic (pandas)", "Params"],
    [["Completeness", "check_completeness", "field is NA or blank after strip", "field"],
     ["Validity", "check_validity", "value not in allowed list / not matching regex / outside "
      "[min,max] (exactly one criterion)", "field + one of {allowed_values, regex, min/max}"],
     ["Uniqueness", "check_uniqueness", "df.duplicated(subset=keys) &mdash; the combination must be "
      "unique", "keys (list &mdash; composite key)"],
     ["Consistency", "check_consistency", "field value not present in the reference dataset&rsquo;s "
      "column (referential integrity)", "field, ref_field, ref_dataset_scope"],
     ["Timeliness", "check_timeliness", "date older than max_lag_days vs reference_date "
      "(&lsquo;today&rsquo; or a fixed ISO date)", "field, max_lag_days, reference_date"],
     ["Reconciliation", "check_reconciliation", "outer-join on key; break if a side is missing or "
      "|src-ref|/ref*100 &gt; tolerance_pct", "key, field, ref_field, ref_dataset_scope, tolerance_pct"]],
    [24 * mm, 32 * mm, 66 * mm, 46 * mm]))
SP(4)
SMALL("Each function returns a standardised dict &mdash; "
      "<font face='Courier'>{status: PASS|FAIL, metrics: {&hellip;}, exceptions: DataFrame}</font>. "
      "No function knows a dataset or project name; it only receives column names, so one function "
      "serves any field of any dataset (brief &sect;3 &ldquo;Configurability&rdquo;, App. A.4).")
PB()

H2("3.2 &nbsp; The meta-catalogue &mdash; validation applied before a rule is saved")
BODY("<font face='Courier'>rule_authoring/schema.py</font> validates every rule. Blocking "
     "<b>errors</b> prevent the save; <b>warnings</b> are recorded and shown but allow the save. "
     "This is the brief&rsquo;s &ldquo;rules must be explicit and testable&rdquo; (App. A.4) made "
     "executable.")
H3("Blocking errors")
A(table(
    ["Area", "Checks (error code)"],
    [["Rule ID", "required; format <font face='Courier'>letter + [A-Za-z0-9_-] (2&ndash;20)</font>; "
      "unique in the catalogue (duplicate)"],
     ["Text fields", "control_name / description / owner / kpi / remediation_action required and "
      "within length bounds (required, length)"],
     ["Vocabularies", "control_type, severity, frequency must be in the allowed sets (invalid)"],
     ["Output type", "required (a value outside the standard list is an <i>info</i>, not an error)"],
     ["Dataset", "dataset_scope required and declared in datasets_config.yaml (unknown_dataset)"],
     ["Threshold", "threshold_pct, if set, numeric and in [0, 100] (not_numeric, out_of_range)"],
     ["Columns", "field / keys / key / ref_field must exist in the target dataset &mdash; checked "
      "by reading a 50-row sample through the connector (unknown_column)"],
     ["Completeness", "field required (param_required)"],
     ["Validity", "field required; <b>exactly one</b> criterion among allowed_values / regex / "
      "range (validity_no_mode, validity_many_modes); regex must compile (bad_regex); "
      "min &le; max (range_inverted)"],
     ["Uniqueness", "keys non-empty (param_required); no repeated column (duplicate_keys)"],
     ["Consistency", "field + ref_field required; ref_dataset_scope declared "
      "(param_required, unknown_dataset)"],
     ["Timeliness", "max_lag_days integer &gt; 0 (non_positive, not_int); reference_date is "
      "&lsquo;today&rsquo; or a valid ISO date (bad_date)"],
     ["Reconciliation", "key + field + ref_field required; ref_dataset_scope declared; "
      "tolerance_pct numeric in [0, 100] (not_numeric, out_of_range)"]],
    [26 * mm, 142 * mm]))
SP(6)
H3("Warnings (rule saved, but flagged)")
BUL([
    "High-severity control run at low frequency &mdash; weak risk coverage (critical_low_freq).",
    "Same (type, dataset, params, ref) as an existing rule &mdash; possible duplicate "
    "(duplicate_control).",
    "threshold_pct &gt; 5 on a High-severity control (loose_critical).",
    "Reference dataset identical to the controlled dataset (self_reference).",
    "Overly permissive regex such as <font face='Courier'>.*</font> (permissive_regex); "
    "single allowed value (single_value); reconciliation key absent from the reference "
    "(key_absent_in_ref).",
    "Info: no threshold_pct set &mdash; the control is binary (no_threshold).",
])
SP(4)
SMALL("The same module also generates the auditor-readable columns "
      "(<font face='Courier'>derive_logic_definition</font>, "
      "<font face='Courier'>derive_data_element</font>, "
      "<font face='Courier'>derive_threshold_text</font>) and the plain-language explanation shown "
      "as a live preview in the form.")
PB()

H2("3.3 &nbsp; Data source registry &amp; connectors")
BODY("<font face='Courier'>datasets_config.yaml</font> holds, per named source, a connector "
     "<font face='Courier'>type</font>, a <font face='Courier'>status</font> "
     "(active / retired / preview) and a connector-specific <font face='Courier'>config</font>. "
     "This is the brief&rsquo;s &ldquo;Separation of Concerns&rdquo; (&sect;3): the engine never "
     "knows <i>where</i> the data is until it is told.")
A(table(
    ["Connector", "Status", "Config fields"],
    [["CSV file", "implemented", "path, delimiter (incl. \\t), header_row, encoding, quotechar, "
      "skip_rows"],
     ["Excel file", "implemented", "path, sheet, header_row, skip_rows, nrows (uses openpyxl)"],
     ["JSON file", "preview", "path, orient, lines, record_path"],
     ["SQL database", "preview", "driver, host, port, database, schema, username, password, "
      "table / query"],
     ["SharePoint / Drive / URL", "preview", "url, auth, token, format"]],
    [40 * mm, 24 * mm, 104 * mm]))
SP(4)
BUL([
    "Each connector implements <font face='Courier'>load(config, root) &rarr; DataFrame</font>, "
    "<font face='Courier'>probe(config, root) &rarr; {ok, columns, row_count, sample, error}</font> "
    "and <font face='Courier'>validate(config) &rarr; [issues]</font>.",
    "<i>Preview</i> connectors render the full field form (for the demo, incl. SQL credentials and "
    "the SharePoint link) but their <font face='Courier'>load()</font> raises and they are saved "
    "with <font face='Courier'>status: preview</font> &mdash; the engine skips them. Credentials "
    "on preview connectors are not persisted.",
    "The same <font face='Courier'>probe()</font> feeds the catalogue&rsquo;s column-existence "
    "check, so a rule can never reference a column its source does not expose.",
    "A new source type is one class in <font face='Courier'>connectors.py</font>; the engine, "
    "catalogue and reporting are untouched.",
])
SP(4)
BODY("<b>Delete policy</b> (each step written to the hash-chained data source changelog):")
A(table(
    ["Action", "Effect on the source", "Effect on dependent rules"],
    [["Retire", "status &rarr; retired (reversible)", "auto-deactivated; &lsquo;reactivate rules&rsquo; "
      "brings them back"],
     ["Purge", "removed from the registry (typed PURGE confirmation)", "definitions never deleted, "
      "only deactivated"],
     ["Rename", "key rewritten", "dataset_scope / ref_dataset_scope rewritten on every dependent "
      "rule in one logged transaction"]],
    [24 * mm, 66 * mm, 78 * mm]))
SP(4)
SMALL("A rule pointing at a missing or retired source does <b>not</b> crash the engine run: it "
      "produces a <font face='Courier'>status: ERROR</font> result with a message and the run "
      "continues (brief &sect;7.3).")
PB()

H2("3.4 &nbsp; Data Quality Engine &mdash; dq_engine.py")
BUL([
    "<b>Dynamic dispatch</b> &mdash; for each row of the catalogue, look up "
    "<font face='Courier'>CONTROL_REGISTRY[control_type]</font> and call it with the parsed "
    "<font face='Courier'>params</font>; load the reference dataset too for Consistency / "
    "Reconciliation. No rule logic is hard-coded (brief &sect;4.1).",
    "<b>Threshold</b> &mdash; <font face='Courier'>_apply_threshold()</font> turns a FAIL into a "
    "PASS when the exception rate &le; <font face='Courier'>threshold_pct</font>, recording "
    "<font face='Courier'>exception_pct</font>, <font face='Courier'>threshold_pct</font> and "
    "<font face='Courier'>within_threshold</font> in the metrics. The same helper is used by "
    "verification so both compute status identically.",
    "<b>Inactive rules</b> &mdash; rows with <font face='Courier'>active=FALSE</font> are skipped "
    "and logged as <font face='Courier'>rule_skipped</font>.",
    "<b>Resilience</b> &mdash; an unknown control type or an unavailable data source yields an "
    "<font face='Courier'>ERROR</font> result (with the reason) and the run continues.",
    "<b>Consistency across runs</b> &mdash; the engine is deterministic; two runs on the same "
    "inputs produce identical per-rule status, metrics and exception counts (verified by "
    "<font face='Courier'>tests/test_engine.py</font>).",
    "<b>Detailed metrics + severity</b> &mdash; every result carries the rule&rsquo;s "
    "<font face='Courier'>severity</font> and a metrics dict "
    "(total_records, null_count, completeness_pct, duplicate_count, orphan_pct, break_count, "
    "&hellip;) &mdash; brief &sect;4.1 &ldquo;results must include severity levels and detailed "
    "metrics.&rdquo;",
])
PB()

H2("3.5 &nbsp; Audit Layer &mdash; the Evidence Pack (Appendix B)")
BODY("Each run writes <font face='Courier'>evidence/&lt;run_id&gt;/</font>. The table maps every "
     "mandatory Appendix B.2 component to the file that carries it.")
A(table(
    ["Appendix B.2 component", "Where it is in the Evidence Pack"],
    [["Run ID", "<font face='Courier'>run_summary.json</font> and every "
      "<font face='Courier'>&lt;rule&gt;_result.json</font> (a UUID)"],
     ["Execution Timestamp", "<font face='Courier'>run_timestamp_utc</font> / "
      "<font face='Courier'>execution_timestamp_utc</font> (UTC ISO-8601)"],
     ["Dataset Reference (version / snapshot / hash)", "SHA-256 hash per dataset in each result "
      "<b>plus</b> an exact copy in <font face='Courier'>snapshots/&lt;name&gt;.csv</font>"],
     ["Rule Configuration", "<font face='Courier'>rule_configuration_snapshot</font> "
      "(dataset_scope, ref_dataset_scope, params, threshold_pct) in each result"],
     ["Execution Parameters", "<font face='Courier'>execution_parameters</font> &mdash; the "
      "<i>resolved</i> values, e.g. <font face='Courier'>reference_date_resolved: 2026-09-08</font>"],
     ["Control Results (pass/fail, KPI values)", "<font face='Courier'>status</font> + "
      "<font face='Courier'>metrics</font> in each result; aggregated in "
      "<font face='Courier'>run_summary.json</font>"],
     ["Exception Dataset", "<font face='Courier'>&lt;rule&gt;_exceptions.csv</font> &mdash; the "
      "failing records, one file per failing rule"],
     ["Logs (processing steps)", "<font face='Courier'>run_log.jsonl</font> (structured) + "
      "<font face='Courier'>run.log</font> (plain text): run_start, dataset_loaded, rule_start, "
      "rule_done / rule_error, system_trace_written, run_complete"],
     ["System Trace", "<font face='Courier'>system_trace.json</font>: engine version, Python "
      "version, platform, host, pandas / pyyaml / openpyxl versions, SHA-256 of the catalogue, "
      "the config and <font face='Courier'>controls.py</font>, and the control function used per rule"],
     ["Sign-off Fields", "<font face='Courier'>signoff.json</font> &mdash; reviewed_by, "
      "reviewed_at, decision, comment (recorded from the Runs page)"]],
    [50 * mm, 118 * mm]))
SP(6)
H3("Reproducibility, tamper-evidence and independent verification")
BUL([
    "<b>Run ledger</b> &mdash; <font face='Courier'>evidence/runs_ledger.jsonl</font> appends one "
    "entry per run with <font face='Courier'>previous_run_hash</font> and "
    "<font face='Courier'>run_hash = SHA-256(previous_run_hash + canonical_json(run_summary))</font>. "
    "Altering any stored <font face='Courier'>run_summary.json</font> breaks the chain from that "
    "point on (brief &sect;7.1 &ldquo;results stored and versioned&rdquo;, App. B.3).",
    "<b>Reconstruction</b> &mdash; every past run is fully contained in its folder: config "
    "snapshot + dataset snapshots + logs + trace. An independent party needs nothing else "
    "(&sect;7.3, App. B.4).",
    "<b>Verification</b> &mdash; <font face='Courier'>dqcompass verify &lt;run_id&gt;</font> "
    "(or the &lsquo;Verify this run&rsquo; button) reloads the stored rule configuration, "
    "re-executes each control against the stored <font face='Courier'>snapshots/</font>, applies "
    "the same threshold logic, and asserts <font face='Courier'>status</font> + "
    "<font face='Courier'>exception_count</font> are unchanged. It writes "
    "<font face='Courier'>verification.json</font> "
    "(<font face='Courier'>all_match</font> + a per-rule check table) and exits non-zero on any "
    "mismatch (&sect;7.3 &ldquo;independent verification of results&rdquo;).",
    "<b>Retention note</b> &mdash; <font face='Courier'>system_trace.json</font> states that the "
    "prototype writes local files and that production would point "
    "<font face='Courier'>evidence/</font> at versioned WORM storage (S3 Object Lock / immutable "
    "data-lake prefix).",
])
PB()

H2("3.6 &nbsp; Reporting Layer")
BODY("<font face='Courier'>reporting/scorecard.py</font> reads the latest run and writes eight "
     "artefacts; <font face='Courier'>mapping.py</font> writes the Appendix C mapping. All are "
     "also surfaced inside the web app (Runs and Mapping pages).")
A(table(
    ["Artefact", "Content", "Brief"],
    [["scorecard.csv", "One row per rule: status, traffic light (GREEN/ORANGE/RED/GREY for "
      "ERROR), severity, owner, exception count, all metrics", "&sect;4.3"],
     ["scorecard.html", "Standalone traffic-light scorecard for a demo without a BI tool", "&sect;4.3 / 5.2"],
     ["exceptions_detail.csv", "Every failing record from every rule, tagged with rule_id + "
      "severity &mdash; record-level drill-down", "&sect;4.3"],
     ["coverage.csv", "datasets &times; dimensions: which rules cover which (dataset, dimension) "
      "&mdash; the control coverage view", "&sect;4.3"],
     ["exception_summary.csv", "Exceptions grouped by severity / owner / control_type / dataset "
      "(long format, BI-friendly)", "&sect;4.3"],
     ["dataset_score.csv", "Severity-weighted composite DQ score per dataset (0&ndash;100): "
      "penalty = weight&times;min(1, exc_pct/100) for FAIL, weight for ERROR; weights High=5, "
      "Medium=2, Low=1", "&sect;4.3 / 8.2"],
     ["trend.csv", "Pass / fail / error per run over time, from the ledger", "&sect;4.3"],
     ["alerts.json", "One entry per failing High-severity control: rule, dataset, owner, "
      "exception count and the remediation action from the catalogue &mdash; failures captured, "
      "prioritised and <i>actionable</i>", "&sect;1.2"],
     ["supervisory_mapping.csv", "Appendix C.2/C.3: Requirement &rarr; Control &rarr; Evidence "
      "&rarr; Output, plus the last run id + hash per rule", "App. C"]],
    [40 * mm, 108 * mm, 20 * mm]))
SP(4)
BODY("<b>Supervisory mapping (Appendix C).</b> <font face='Courier'>mapping.py</font> builds one "
     "row per active rule. The requirement is the rule&rsquo;s "
     "<font face='Courier'>regulatory_ref</font> if set, otherwise a default derived from the DQ "
     "dimension (phrased in BCBS 239 terms). The evidence column names the Evidence Pack files "
     "produced; the last-run columns link the control to its most recent execution "
     "(<font face='Courier'>run_id</font> + <font face='Courier'>run_hash</font>) &mdash; the "
     "Appendix C.3 control-to-evidence traceability. The Mapping page also lists the four "
     "Appendix C.4 principles (Traceability, Repeatability, Auditability, Governance) with how "
     "each is demonstrated.")
PB()

H2("3.7 &nbsp; Authoring web application &mdash; rule_authoring/")
BODY("A Flask application with a sidebar shell and seven sections. All text is English; a "
     "light/dark theme toggle is persisted per browser.")
A(table(
    ["Section", "What it provides"],
    [["Home", "Dashboard: rule/source health tiles, the latest run as a pass/fail/error donut, a "
      "&lsquo;needs attention&rsquo; list (validation errors, probe failures, retired sources with "
      "live dependents), the coverage heatmap, recent activity, a &lsquo;Run engine now&rsquo; button."],
     ["Catalogue", "The rules as filterable list items (search + status chips + control-type "
      "chips, each with a live count); every row expands to its logic, validation issues, owner / "
      "KPI / remediation. Full CRUD + activate/deactivate. Coverage matrix below."],
     ["Data Sources", "One card per source: connector, status, plain-language summary, "
      "&lsquo;used by&rsquo; rule chips; edit / retire / reactivate / rename / purge. The "
      "&lsquo;New data source&rsquo; form has a connector-tile picker, progressive fields "
      "(advanced options collapsed) and a &lsquo;Test connection&rsquo; preview."],
     ["Runs", "Run history from the ledger (verified / signed-off badges) and a per-run "
      "drill-down: the Evidence Pack (hashes + chain), a result bar, per-rule cards (metrics, "
      "config snapshot, execution parameters, exception table), a Reporting card, a Verification "
      "table, the sign-off form, the system trace and the processing-log tail. Buttons: Verify "
      "this run, Record sign-off."],
     ["Reporting", "Cross-run analytics with an audience filter (All / Control owners &amp; risk / "
      "Data engineers). Business: composite DQ score + delta, a score-trend chart over the last "
      "runs, dataset health ranking, a 3-state coverage matrix (controlled+passing / "
      "controlled+failing / not controlled), open High-severity issues with remediation, "
      "exceptions by owner. Engineering: exceptions by dimension and by rule, a rule-reliability "
      "table (fail rate over the run window), a &lsquo;what changed since the previous run&rsquo; "
      "diff, and the ERROR (broken source/config) list. All charts are dependency-free inline SVG. "
      "Power-BI-ready CSV/JSON downloads."],
     ["Mapping", "The Appendix C.2/C.3 table + the C.4 principles + a supervisory_mapping.csv download."],
     ["Activity", "The two audit changelogs merged into one timeline (filter Rules / Data "
      "sources), with per-entry field diffs and the file hash."],
     ["Help (/docs)", "Field reference generated from the schema: the attributes, the 6 control "
      "types and their parameters, the meaning of each output_type / severity / frequency, the "
      "threshold, the connectors, the validation rules, the audit log."]],
    [26 * mm, 142 * mm]))
SP(6)
H3("Governance surface")
BUL([
    "<b>Two hash-chained changelogs</b> &mdash; "
    "<font face='Courier'>catalogue_changelog.jsonl</font> and "
    "<font face='Courier'>data_sources_changelog.jsonl</font>. Every create / update / delete / "
    "(de)activate / retire / purge / rename appends an entry with the editor, the UTC timestamp, "
    "the before/after snapshot and the <b>SHA-256 of the file before and after</b>. The catalogue "
    "state at any past date is reconstructible (App. C.4 &ldquo;Governance&rdquo;, brief &sect;8.3).",
    "<b>Atomic writes</b> &mdash; the CSV and YAML are written to a temp file then "
    "<font face='Courier'>os.replace()</font>d, so a killed process never leaves a half-written "
    "catalogue.",
    "<b>Deactivate, don&rsquo;t delete</b> &mdash; a retired rule keeps its definition and its "
    "history; it is simply out of the engine&rsquo;s scope.",
])
PB()

H2("3.8 &nbsp; CLI, packaging &amp; deployment")
A(table(
    ["Command", "Purpose"],
    [["dqcompass run", "Execute the catalogue, write the Evidence Pack, append the ledger."],
     ["dqcompass verify &lt;run_id&gt;", "Re-execute a past run from its snapshots; exit 1 on mismatch."],
     ["dqcompass report", "(Re)generate the eight Reporting Layer files."],
     ["dqcompass mapping", "Write reporting/supervisory_mapping.csv (Appendix C)."],
     ["dqcompass catalogue-validate", "Validate every rule against the meta-catalogue; exit 1 on error."],
     ["dqcompass gate --severity High", "Run + exit 1 if any control at/above that severity broke "
      "&mdash; a CI quality gate."],
     ["dqcompass serve", "Start the authoring web app (127.0.0.1:5001)."]],
    [46 * mm, 122 * mm]))
SP(4)
BUL([
    "<font face='Courier'>pyproject.toml</font> makes the project installable "
    "(<font face='Courier'>pip install -e .</font>) and puts <font face='Courier'>dqcompass</font> "
    "on the PATH.",
    "<font face='Courier'>docs/DEPLOYMENT.md</font> gives ready recipes: add the layer to an EUC "
    "in three lines; cron and Airflow schedules; a GitHub Actions workflow "
    "(<font face='Courier'>catalogue-validate</font> then <font face='Courier'>gate</font>); a "
    "notification loop that posts <font face='Courier'>alerts.json</font> to a channel with the "
    "remediation action.",
    "This is the brief&rsquo;s &sect;8.4 &ldquo;ease of deployment across EUCs / potential for "
    "industrialisation&rdquo; and &sect;9 &ldquo;embed control logic into the data lifecycle.&rdquo;",
])
SP(4)
H2("3.9 &nbsp; Tests")
A(table(
    ["Suite", "N", "Covers"],
    [["tests/test_schema.py", "21", "Every meta-catalogue check: valid rule per dimension, "
      "unknown dataset / column, Validity mode rules, bad regex, unknown keys, missing reference "
      "dataset, bad lag, out-of-range tolerance, duplicate / malformed id, cross-field warnings, "
      "the derivations."],
     ["tests/test_connectors.py", "11", "CSV default + custom delimiter + header offset + probe; "
      "Excel round-trip + sheet-not-found; preview connectors raise; SQL / URL shape validation; "
      "normalize_entry (flat vs rich); load_source missing / retired; source_schema validation."],
     ["tests/test_engine.py", "6", "Evidence Pack structure; reproducibility + ledger hash chain; "
      "verify_run reproducible; resolved execution parameters; threshold FAIL&rarr;PASS; a missing "
      "source produces an ERROR record without crashing and verify handles it."]],
    [40 * mm, 10 * mm, 118 * mm]))
SP(4)
SMALL("Run: <font face='Courier'>python tests/test_schema.py</font> / "
      "<font face='Courier'>test_connectors.py</font> / <font face='Courier'>test_engine.py</font>, "
      "or <font face='Courier'>python -m pytest tests/</font>. All 38 pass; "
      "<font face='Courier'>pyflakes</font> is clean.")
PB()

# ---- 4. Worked example ----
H1("4 &nbsp; Worked example &mdash; one run end to end")
BODY("The seeded catalogue has seven rules (DQ01&ndash;DQ07) over the "
     "<font face='Courier'>orders</font> dataset, which contains six deliberate anomalies.")
A(table(
    ["Rule", "Dimension", "What it checks", "Result on the sample", "Metric"],
    [["DQ01", "Completeness", "orders.amount not null", "FAIL &mdash; 1 null (ORD002)", "completeness_pct 90.91"],
     ["DQ02", "Validity", "status in {PENDING, SHIPPED, DELIVERED, CANCELLED}", "FAIL &mdash; "
      "&lsquo;UNKNOWN_STATUS&rsquo; (ORD006)", "valid_pct 90.91"],
     ["DQ03", "Uniqueness", "order_id unique", "FAIL &mdash; ORD001 duplicated", "duplicate_pct 18.18"],
     ["DQ04", "Consistency", "customer_id exists in customers", "FAIL &mdash; CUST999 orphan "
      "(ORD005)", "orphan_pct 9.09"],
     ["DQ05", "Timeliness", "order_date within 3 days of today", "FAIL &mdash; ORD007 stale", "within_sla_pct 81.82"],
     ["DQ06", "Reconciliation", "orders.amount vs orders_reference.amount, 0.5% tol.", "FAIL "
      "&mdash; ORD010 (999.99 vs 899.99)", "reconciled_pct 90.91"],
     ["DQ07", "Validity", "region in {FR, BE, DE}, threshold 2%", "PASS &mdash; 0 invalid "
      "(within_threshold)", "valid_pct 100.0"]],
    [12 * mm, 24 * mm, 52 * mm, 46 * mm, 34 * mm]))
SP(6)
BODY("The run produces <font face='Courier'>evidence/&lt;run_id&gt;/</font> with: "
     "<font face='Courier'>run_summary.json</font> (7 results, run_hash, previous_run_hash), "
     "seven <font face='Courier'>DQ0x_result.json</font>, six "
     "<font face='Courier'>DQ0x_exceptions.csv</font> (DQ07 has none), "
     "<font face='Courier'>snapshots/orders.csv</font>, "
     "<font face='Courier'>snapshots/customers.csv</font>, "
     "<font face='Courier'>snapshots/orders_reference.csv</font>, "
     "<font face='Courier'>system_trace.json</font>, "
     "<font face='Courier'>run_log.jsonl</font> + <font face='Courier'>run.log</font>. "
     "<font face='Courier'>dqcompass report</font> then writes the nine reporting artefacts "
     "(dataset_score for <font face='Courier'>orders</font> &asymp; 89&ndash;90, four "
     "High-severity entries in <font face='Courier'>alerts.json</font>). "
     "<font face='Courier'>dqcompass verify &lt;run_id&gt;</font> re-runs the seven controls "
     "against the snapshots and reports <font face='Courier'>REPRODUCIBLE</font>.")
PB()

# ---- 5. Compliance matrix ----
H1("5 &nbsp; Brief-compliance matrix")
SMALL("Ref key: &sect;n = use-case section n; A.x / B.x / C.x = Appendix A / B / C. Every row is "
      "satisfied by the prototype; caveats are stated inline and collected in section 6.")

H2("5.1 &nbsp; Core principle &amp; mission (&sect;1.2, &sect;2.1, &sect;2.3)")
A(comp([
    ("Controls defined, executed and evidenced in a structured manner", "&sect;1.2",
     "Definition in a 21-column catalogue; execution by a single generic engine; evidence as a "
     "structured Evidence Pack per run.",
     "control_catalogue.csv; dq_engine.py; evidence/&lt;run_id&gt;/"),
    ("Outputs traceable to input data and rule definitions", "&sect;1.2",
     "Each result stores the dataset SHA-256 + a full copy, and the rule config snapshot; the run "
     "hash chains to the previous run.",
     "&lt;rule&gt;_result.json, snapshots/, runs_ledger.jsonl"),
    ("Execution repeatable and reproducible", "&sect;1.2",
     "Deterministic engine; two runs give identical results (tested); verify_run re-executes from "
     "snapshots and asserts equality.",
     "tests/test_engine.py; verify_run(); verification.json"),
    ("Control failures captured, prioritised and actionable", "&sect;1.2",
     "Exceptions written per rule; severity on every result; alerts.json lists failing "
     "High-severity controls with the catalogue&rsquo;s remediation action.",
     "&lt;rule&gt;_exceptions.csv; reporting/alerts.json"),
    ("A generic control layer: applied across datasets, configurable with minimal effort, "
     "scalable across contexts", "&sect;2.1",
     "One row adds a rule, one YAML entry adds a dataset, one class adds a connector &mdash; no "
     "engine code changes. Generic control functions take only column names.",
     "controls.py; connectors.py; datasets_config.yaml"),
    ("Parameterised, reusable, centrally governed via a catalogue, producing documented evidence",
     "&sect;2.3",
     "params JSON drives behaviour; the catalogue is the single governed repository; every run "
     "documents itself.",
     "control_catalogue.csv; rule_authoring/; evidence/"),
]))
PB()

H2("5.2 &nbsp; Solution design principles (&sect;3)")
A(comp([
    ("Separation of concerns &mdash; rule definition separated from execution", "&sect;3.1",
     "The catalogue + datasets_config define <i>what</i> and <i>where</i>; dq_engine + controls "
     "run <i>how</i>. The engine never contains a rule or a path.",
     "control_catalogue.csv; datasets_config.yaml; dq_engine.py"),
    ("Configurability &mdash; parameterised thresholds, fields, conditions; one rule to many "
     "datasets", "&sect;3.2",
     "Every control is parameterised (field, keys, regex, min/max, max_lag_days, tolerance_pct, "
     "threshold_pct). check_completeness serves any field of any dataset.",
     "params column; controls.py"),
    ("Standardisation &mdash; consistent control structure; standardised outputs", "&sect;3.3",
     "Fixed 21-column schema; every control returns the same {status, metrics, exceptions} shape; "
     "every run writes the same Evidence Pack layout.",
     "store.CANONICAL_COLUMNS; controls.py; evidence/&lt;run_id&gt;/"),
    ("Traceability &mdash; each execution provides source dataset, rule applied, timestamp, result",
     "&sect;3.4",
     "Every &lt;rule&gt;_result.json carries dataset_reference (hash), control_function, "
     "rule_configuration_snapshot, execution_timestamp_utc, status + metrics.",
     "&lt;rule&gt;_result.json"),
    ("Auditability &mdash; artefacts reviewable independently; allow reconstruction; demonstrate "
     "effectiveness", "&sect;3.5",
     "The Evidence Pack is self-contained; verify_run reconstructs and re-checks; the run ledger "
     "and changelogs are hash-chained.",
     "evidence/; verify_run(); *_changelog.jsonl"),
    ("Plug-and-play architecture &mdash; integrate into any EUC with minimal technical change",
     "&sect;3",
     "Drop two files next to the EUC and call DQEngine(&hellip;).run(); or add "
     "<font face='Courier'>dqcompass run</font> to the pipeline.",
     "docs/DEPLOYMENT.md; cli.py"),
]))
PB()

H2("5.3 &nbsp; Functional architecture (&sect;4)")
A(comp([
    ("Engine executes multiple control types", "&sect;4.1",
     "Six control types dispatched from CONTROL_REGISTRY by control_type.", "controls.py; dq_engine.py"),
    ("Engine applies rules across datasets dynamically", "&sect;4.1",
     "Rules are data; the engine iterates the catalogue and resolves each dataset through a "
     "connector at run time.", "dq_engine.run()"),
    ("Engine produces structured outputs; execution consistent and repeatable; results include "
     "severity + detailed metrics", "&sect;4.1",
     "JSON results + CSV exceptions; deterministic; severity + a metrics dict on every result.",
     "&lt;rule&gt;_result.json; tests/test_engine.py"),
    ("Control Catalogue: Rule ID, Description, Control Type, Logic definition, Severity, "
     "Owner+frequency, Expected output", "&sect;4.2",
     "All present as named columns (see A.2 map in 5.7); logic_definition generated as pseudo-SQL.",
     "control_catalogue.csv"),
    ("Catalogue: full traceability between rule definition and execution; reuse across datasets",
     "&sect;4.2",
     "rule_id links definition &harr; every result; dataset_scope is a parameter, not code.",
     "&lt;rule&gt;_result.json; catalogue"),
    ("Reporting: DQ scorecards (traffic light)", "&sect;4.3",
     "scorecard.csv/.html with GREEN/ORANGE/RED (+ GREY for ERROR); the app renders the same as a "
     "donut and per-rule badges.", "reporting/scorecard.*"),
    ("Reporting: exception reports", "&sect;4.3",
     "Per-rule &lt;rule&gt;_exceptions.csv + consolidated exceptions_detail.csv + "
     "exception_summary.csv (grouped).", "reporting/exception*"),
    ("Reporting: control coverage views", "&sect;4.3",
     "coverage.csv (datasets &times; dimensions) and the coverage heatmap on Home / Catalogue.",
     "reporting/coverage.csv; app"),
    ("Reporting: clear identification of issues; drill-down to record level; consistent structure",
     "&sect;4.3",
     "Traffic light + counts; exceptions_detail.csv is record-level; the schema of every report "
     "is stable across runs.", "reporting/"),
    ("Audit Layer: execution logs; input dataset references; rule configuration snapshot; "
     "exception datasets", "&sect;4.4",
     "run_log.jsonl/run.log; dataset hash + snapshot; rule_configuration_snapshot; "
     "&lt;rule&gt;_exceptions.csv.", "evidence/&lt;run_id&gt;/"),
    ("Audit Layer: evidence reproducible; outputs time-stamped and traceable; support independent "
     "audit validation", "&sect;4.4",
     "verify_run() proves reproducibility; UTC timestamps everywhere; verification.json is the "
     "independent-validation artefact.", "verify_run(); verification.json"),
]))
PB()

H2("5.4 &nbsp; Deliverables (&sect;5)")
A(comp([
    ("Working solution implementing DQ controls", "&sect;5.1",
     "The engine runs the seven-rule catalogue over three datasets; 38 tests pass.",
     "dq_engine.py; tests/"),
    ("Reusable control catalogue", "&sect;5.1",
     "The 21-column CSV, authored and validated through the web app / "
     "<font face='Courier'>dqcompass catalogue-validate</font>.",
     "control_catalogue.csv; rule_authoring/"),
    ("Automated control execution engine", "&sect;5.1",
     "<font face='Courier'>dqcompass run</font> / cron / Airflow / CI; no manual step.",
     "cli.py; docs/DEPLOYMENT.md"),
    ("Standard dashboards and reports; clear representation of DQ metrics", "&sect;5.2",
     "The web dashboard + scorecard.html + the eight reporting CSV/JSON files (Power BI ready).",
     "rule_authoring/; reporting/"),
    ("Documentation: architecture &amp; design choices; control logic; limitations &amp; "
     "scalability", "&sect;5.3",
     "README.md, docs/ARCHITECTURE.md (4-layer model, data flow, limitations &amp; scalability), "
     "this report, and the in-app Help page.",
     "docs/ARCHITECTURE.md; this PDF"),
    ("Presentation: demo of the solution; business value &amp; scalability", "&sect;5.4",
     "The web app is the live demo (run, drill into evidence, verify, sign off); business value in "
     "&sect;8.4 rows below.",
     "rule_authoring/ (serve)"),
    ("Deliverables demonstrate the end-to-end lifecycle and clear auditable outputs", "&sect;5.5",
     "Definition (Catalogue) &rarr; Execution (Runs) &rarr; Reporting (Runs/Mapping) &rarr; Audit "
     "(Evidence Pack + verify) are all visible in one application.",
     "the whole system"),
]))
PB()

H2("5.5 &nbsp; Catalogue detail &amp; expectations (&sect;6, App. A.4)")
A(comp([
    ("Minimum fields: Rule ID, Control Type, Logic, Dataset Scope, Severity, Frequency, Owner, "
     "Output", "&sect;6",
     "All present as dedicated columns; Logic held both as generated pseudo-SQL "
     "(logic_definition) and as machine params.",
     "control_catalogue.csv"),
    ("Rules explicit, testable and reusable", "&sect;6 / A.4",
     "Each rule is validated by ~30 checks before saving; column existence is probed against the "
     "real dataset; parameters make it reusable.",
     "rule_authoring/schema.py"),
    ("All rules produce quantifiable outputs (KPIs)", "&sect;6 / A.4",
     "kpi column per rule; every result carries a metrics dict with the quantitative measure.",
     "kpi column; &lt;rule&gt;_result.json"),
    ("Controls support prioritisation / escalation through severity levels", "&sect;6 / A.4",
     "severity on every rule and result; traffic light and alerts.json are severity-driven; "
     "<font face='Courier'>dqcompass gate --severity</font> escalates in CI.",
     "severity; scorecard; alerts.json; gate"),
    ("Controls independent of datasets (reusable)", "A.4",
     "The six control functions receive only column names; the same function runs on any dataset.",
     "controls.py"),
]))
PB()

H2("5.6 &nbsp; Execution, evidence &amp; audit expectations (&sect;7)")
A(comp([
    ("Controls executed automatically", "&sect;7.1",
     "<font face='Courier'>dqcompass run</font> is non-interactive; DEPLOYMENT.md gives cron / "
     "Airflow / CI; the catalogue <font face='Courier'>frequency</font> is the declarative "
     "schedule input.",
     "cli.py; docs/DEPLOYMENT.md"),
    ("Execution consistent across runs", "&sect;7.1",
     "Deterministic; identical per-rule status / metrics / exception counts across runs (tested).",
     "tests/test_engine.py::test_reproducibility_and_ledger_chain"),
    ("Results stored and versioned", "&sect;7.1",
     "Each run is an immutable folder; runs_ledger.jsonl versions the sequence with a hash chain.",
     "evidence/&lt;run_id&gt;/; runs_ledger.jsonl"),
    ("Each execution produces: Run ID + timestamp", "&sect;7.2",
     "UUID run_id + UTC ISO timestamp in run_summary.json and every result.", "run_summary.json"),
    ("Each execution produces: Dataset reference (version or snapshot)", "&sect;7.2",
     "SHA-256 hash per dataset <b>and</b> a byte-exact copy under snapshots/.",
     "dataset_reference; snapshots/"),
    ("Each execution produces: Rule configuration used", "&sect;7.2",
     "rule_configuration_snapshot + execution_parameters (resolved) in every result.",
     "&lt;rule&gt;_result.json"),
    ("Each execution produces: Summary results (pass/fail + metrics)", "&sect;7.2",
     "status + metrics per rule; aggregated counts in run_summary.json.", "run_summary.json"),
    ("Each execution produces: Detailed exception records", "&sect;7.2",
     "&lt;rule&gt;_exceptions.csv per failing rule; consolidated in reporting.",
     "&lt;rule&gt;_exceptions.csv"),
    ("Reconstruction of historical control runs", "&sect;7.3",
     "Every run folder is self-contained (config + data snapshots + logs + trace); the Runs page "
     "lists and opens any past run.",
     "evidence/; Runs page"),
    ("Independent verification of results", "&sect;7.3",
     "<font face='Courier'>dqcompass verify &lt;run_id&gt;</font> re-executes from stored inputs "
     "and asserts equality; writes verification.json; non-zero exit on mismatch.",
     "verify_run(); verification.json"),
    ("Traceability from data input to control output", "&sect;7.3",
     "dataset snapshot (+hash) &rarr; control_function + params &rarr; status + metrics + "
     "exceptions, all in one folder, chained by run_hash.",
     "the Evidence Pack"),
]))
PB()

H2("5.7 &nbsp; Appendix A.2 &mdash; the 14 mandatory catalogue attributes")
A(comp([
    ("Rule ID", "A.2", "rule_id &mdash; unique, format-checked, immutable after creation.", "col 1"),
    ("Control Name", "A.2", "control_name &mdash; 3&ndash;80 chars.", "col 2"),
    ("Control Type", "A.2", "control_type &mdash; one of the six dimensions.", "col 3"),
    ("Description", "A.2", "description &mdash; business objective, &ge;10 chars.", "col 4"),
    ("Logic Definition (SQL / pseudo-code / formula)", "A.2",
     "logic_definition &mdash; generated pseudo-SQL, e.g. "
     "<font face='Courier'>SELECT * FROM orders WHERE amount IS NULL &hellip;</font>", "col 5"),
    ("Dataset Scope", "A.2", "dataset_scope &mdash; validated against datasets_config.yaml.", "col 6"),
    ("Data Element", "A.2", "data_element &mdash; the field(s) tested; generated from params.", "col 7"),
    ("Threshold (acceptance criteria / tolerance)", "A.2",
     "threshold (plain text, generated) + threshold_pct (numeric, applied by the engine).", "cols 8, 18"),
    ("Severity (High / Medium / Low)", "A.2", "severity &mdash; controlled vocabulary.", "col 9"),
    ("Frequency", "A.2", "frequency &mdash; 7-value controlled vocabulary.", "col 10"),
    ("Owner", "A.2", "owner &mdash; required.", "col 11"),
    ("Output Type", "A.2", "output_type &mdash; suggestions provided; free value allowed.", "col 12"),
    ("KPI (measurement indicator)", "A.2", "kpi &mdash; required; the metrics dict carries the value.",
     "col 13"),
    ("Remediation Action", "A.2", "remediation_action &mdash; &ge;10 chars; carried into alerts.json.",
     "col 14"),
]))
PB()

H2("5.8 &nbsp; Appendix B.2 &mdash; the 10 mandatory Evidence components")
A(comp([
    ("Run ID", "B.2", "UUID in run_summary.json and every result.", "run_summary.json"),
    ("Execution Timestamp", "B.2", "UTC ISO-8601, run and per rule.", "*_result.json"),
    ("Dataset Reference (version / snapshot / hash)", "B.2",
     "SHA-256 per dataset + exact copy under snapshots/.", "snapshots/; dataset_reference"),
    ("Rule Configuration (full definition)", "B.2", "rule_configuration_snapshot per result.",
     "*_result.json"),
    ("Execution Parameters (thresholds &amp; config)", "B.2",
     "execution_parameters &mdash; resolved values incl. reference_date_resolved, threshold_pct.",
     "*_result.json"),
    ("Control Results (summary metrics, pass/fail, KPI values)", "B.2",
     "status + metrics per rule; counts aggregated.", "run_summary.json"),
    ("Exception Dataset (detailed failing records)", "B.2", "One CSV per failing rule.",
     "*_exceptions.csv"),
    ("Logs (execution logs, processing steps)", "B.2",
     "run_log.jsonl (structured) + run.log (text): every step time-stamped.", "run_log.jsonl; run.log"),
    ("System Trace (execution engine traceability)", "B.2",
     "system_trace.json: engine / Python / lib versions, host, file SHA-256s, control fn per rule.",
     "system_trace.json"),
    ("Sign-off Fields (optional validation / certification)", "B.2",
     "signoff.json &mdash; reviewed_by / reviewed_at / decision / comment, recorded from the app.",
     "signoff.json"),
]))
SP(6)
H3("Appendix B.3 &mdash; evidence lifecycle")
A(comp([
    ("Generation &mdash; automatically produced at execution", "B.3",
     "The engine writes the whole pack in <font face='Courier'>run()</font>; no manual step.",
     "dq_engine.run()"),
    ("Storage &mdash; structured, retrievable", "B.3",
     "One folder per run under evidence/; the Runs page and the ledger index them.",
     "evidence/; runs_ledger.jsonl"),
    ("Traceability &mdash; linked to dataset, rule, execution context", "B.3",
     "dataset hash + snapshot, rule_id + config snapshot, run_id + run_hash + previous_run_hash.",
     "the Evidence Pack"),
    ("Reproducibility &mdash; re-run controls with identical outputs", "B.3",
     "verify_run() re-executes from the stored config + snapshots and asserts equality.",
     "verify_run(); verification.json"),
    ("Audit Review &mdash; independent reconstruction of the control", "B.3 / B.4",
     "Everything needed is in the folder; verification.json is the machine-checkable reconstruction.",
     "evidence/&lt;run_id&gt;/"),
]))
PB()

H2("5.9 &nbsp; Appendix C &mdash; supervisory mapping &amp; principles")
A(comp([
    ("C.2 mapping: Requirement &rarr; Control Implemented &rarr; Evidence Generated &rarr; Output",
     "C.2",
     "<font face='Courier'>mapping.py</font> emits one row per active rule with exactly these "
     "columns; requirement from regulatory_ref or a per-dimension default.",
     "reporting/supervisory_mapping.csv; Mapping page"),
    ("C.3 control-to-evidence traceability (rule &rarr; evidence &rarr; KPI &rarr; output)", "C.3",
     "Each mapping row also carries logic_definition, kpi, output and the last run id + status + "
     "run_hash for that rule.",
     "supervisory_mapping.csv; Mapping page links to the run"),
    ("C.4 Traceability &mdash; control linked to rule definition, dataset, execution run", "C.4",
     "rule_id &harr; result; dataset hash + snapshot; run_id + run_hash.", "the Evidence Pack"),
    ("C.4 Repeatability &mdash; consistent results under identical inputs", "C.4",
     "Deterministic engine; verify_run proves it per run.", "verify_run()"),
    ("C.4 Auditability &mdash; independent parties can reconstruct execution and validate outcomes",
     "C.4",
     "Self-contained run folders + verification.json + the Runs drill-down.", "evidence/; Runs page"),
    ("C.4 Governance &mdash; controls owned, monitored, actionable", "C.4",
     "owner on every rule; coverage matrix + dashboard monitor; remediation_action + alerts.json; "
     "hash-chained changelogs.",
     "catalogue; app; alerts.json; *_changelog.jsonl"),
]))
PB()

H2("5.10 &nbsp; Success criteria (&sect;8) &amp; closing note (&sect;9)")
A(comp([
    ("8.1 Technical quality &mdash; robustness &amp; reliability of the engine", "&sect;8.1",
     "38 automated tests incl. engine-level; the engine never crashes on bad input (ERROR "
     "result); atomic catalogue writes.",
     "tests/; dq_engine.py"),
    ("8.1 Technical quality &mdash; scalability across datasets", "&sect;8.1",
     "Adding a dataset / rule / connector is O(1) config, no engine change. The pandas execution "
     "can be swapped for a push-down backend behind the same function signatures (documented).",
     "connectors.py; docs/ARCHITECTURE.md &sect;5"),
    ("8.2 DQ maturity &mdash; coverage of the key DQ dimensions", "&sect;8.2",
     "All six dimensions implemented; coverage matrix + coverage.csv show which datasets are "
     "covered on which dimension.",
     "controls.py; reporting/coverage.csv"),
    ("8.2 DQ maturity &mdash; sophistication &amp; reusability of controls", "&sect;8.2",
     "Parameterised generic functions; tolerance thresholds; composite keys; referential "
     "integrity; reconciliation with tolerance; a severity-weighted dataset score.",
     "controls.py; dataset_score.csv"),
    ("8.3 Governance &amp; auditability &mdash; strength of the control catalogue", "&sect;8.3",
     "21-column schema; ~30 pre-save validation checks; controlled vocabularies; column probing.",
     "rule_authoring/schema.py"),
    ("8.3 Governance &amp; auditability &mdash; quality of evidence generation", "&sect;8.3",
     "All 10 B.2 components; hash-chained ledger; independent verification; sign-off.",
     "evidence/; verify_run()"),
    ("8.3 Governance &amp; auditability &mdash; traceability &amp; transparency", "&sect;8.3",
     "Two hash-chained changelogs; the Activity timeline; the Appendix C mapping links each "
     "control to its last run.",
     "*_changelog.jsonl; Mapping page"),
    ("8.4 Business value &mdash; ability to reduce operational risk", "&sect;8.4",
     "Fragmented manual checks become one governed, evidenced, auditable layer; failures are "
     "prioritised and routed with a remediation action.",
     "the whole system; alerts.json"),
    ("8.4 Business value &mdash; ease of deployment across EUCs", "&sect;8.4",
     "Two config files + one function call, or one CLI line; <font face='Courier'>pip install -e "
     ".</font>.",
     "docs/DEPLOYMENT.md; pyproject.toml"),
    ("8.4 Business value &mdash; potential for industrialisation", "&sect;8.4",
     "CLI, CI quality gate, scheduler adapters, notification recipe, WORM-storage retention note.",
     "cli.py; docs/DEPLOYMENT.md"),
    ("&sect;9 &mdash; scales across use cases; embeds control logic into the data lifecycle; "
     "audit-ready outputs aligned with supervisory expectations", "&sect;9",
     "Config-only onboarding; a CI gate embeds the checks in the pipeline; the Evidence Pack + "
     "Appendix C mapping are the audit-ready, supervisor-aligned outputs.",
     "docs/DEPLOYMENT.md; mapping.py; evidence/"),
]))
PB()

# ---- 6. Limitations ----
H1("6 &nbsp; Known limitations &amp; scope boundaries")
BUL([
    "<b>Connectors</b> &mdash; only CSV and Excel execute. JSON, SQL database and "
    "SharePoint/Drive/URL are shown as selectors and saved with "
    "<font face='Courier'>status: preview</font>; the engine skips them. The abstraction is "
    "complete (each is one class away from working).",
    "<b>Execution</b> &mdash; rules run sequentially with pandas in memory. For large volumes the "
    "control functions would be re-implemented against a push-down backend (DuckDB / SQL) behind "
    "the same signatures; the catalogue, evidence format and reporting would not change.",
    "<b>Scheduler</b> &mdash; there is no built-in scheduler. "
    "<font face='Courier'>dqcompass run</font> is designed to be called by cron / Airflow / CI; "
    "the catalogue <font face='Courier'>frequency</font> column is the declarative input a "
    "scheduler would consume.",
    "<b>Evidence storage</b> &mdash; local files. Production would point "
    "<font face='Courier'>evidence/</font> at versioned WORM storage; the intent is recorded in "
    "every <font face='Courier'>system_trace.json</font>.",
    "<b>Scoring</b> &mdash; the per-rule verdict is pass/fail; "
    "<font face='Courier'>dataset_score.csv</font> adds a severity-weighted composite, and "
    "<font face='Courier'>trend.csv</font> a per-run series, but there is no automated "
    "run-over-run alerting beyond the CI gate.",
    "<b>Authoring app</b> &mdash; single local user, cookie-based editor name; no authentication "
    "(out of scope for the prototype).",
])
SP(10)
H1("7 &nbsp; How to run")
A(code(
    "pip install -r requirements.txt        # pandas, pyyaml, flask, openpyxl\n"
    "pip install -e .                       # optional: the `dqcompass` command\n\n"
    "python migrate_catalogue.py            # once  (also regenerates derived columns)\n"
    "python migrate_sources.py              # once\n\n"
    "python run_authoring.py                # web app  -> http://127.0.0.1:5001\n"
    "#  or:  dqcompass serve\n\n"
    "dqcompass run                          # execute + write the Evidence Pack\n"
    "dqcompass report                       # generate the Reporting Layer files\n"
    "dqcompass mapping                      # write supervisory_mapping.csv\n"
    "dqcompass verify <run_id>              # prove a past run is reproducible\n"
    "dqcompass catalogue-validate           # validate every rule\n"
    "dqcompass gate --severity High         # CI quality gate\n\n"
    "python tests/test_schema.py            # 21 tests\n"
    "python tests/test_connectors.py        # 11 tests\n"
    "python tests/test_engine.py            # 6 tests"))
SP(10)
SMALL("Generated by docs/build_report.py using ReportLab. Source of truth for every claim is the "
      "code in this repository; see docs/ARCHITECTURE.md and docs/DEPLOYMENT.md for the design "
      "rationale and operational recipes.")


# ==========================================================================
# Build
# ==========================================================================
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 12 * mm, "DQ Compass — Implementation & Brief-Compliance Report")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4,
                      leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=20 * mm,
                      title="DQ Compass - Implementation & Brief-Compliance Report",
                      author="DQ Compass / Working Group 1")
frame = Frame(doc.leftMargin, doc.bottomMargin,
              doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_footer)])
doc.build(story)
print(f"Wrote {OUT}  ({OUT.stat().st_size // 1024} KB)")
