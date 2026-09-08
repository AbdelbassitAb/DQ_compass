"""
build_reporting_metrics.py -- generate the DQ Compass Reporting metrics reference PDF.

    pip install reportlab
    python docs/build_reporting_metrics.py

Output: docs/DQ_Compass_Reporting_Metrics.pdf

Explains every KPI, panel, chart and download on the /reporting page and the
exact formula behind each, cross-referenced to the source
(rule_authoring/app.py :: reporting_context, reporting/scorecard.py,
rule_authoring/charts.py, controls.py, dq_engine.py).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

OUT = Path(__file__).resolve().parent / "DQ_Compass_Reporting_Metrics.pdf"

INK = colors.HexColor("#14161c")
MUTED = colors.HexColor("#5b6270")
ACCENT = colors.HexColor("#c1122a")
LINE = colors.HexColor("#d3d7df")
HEADBG = colors.HexColor("#f0f1f4")
CODEBG = colors.HexColor("#f5f5f7")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold",
                            fontSize=23, leading=27, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11.5, leading=15,
                               textColor=MUTED, spaceAfter=2),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, leading=19,
                         textColor=ACCENT, spaceBefore=16, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                         textColor=INK, spaceBefore=11, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.3, leading=13,
                           textColor=INK, spaceAfter=5, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.3, leading=12.6,
                             textColor=INK, leftIndent=11, spaceAfter=2),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8, leading=10.8,
                           textColor=INK, backColor=CODEBG, borderPadding=6,
                           spaceBefore=3, spaceAfter=7),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=7.9, leading=10.2, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=7.9, leading=10.2, textColor=INK),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10.5,
                            textColor=MUTED, spaceAfter=4),
}


def _fix(t: str) -> str:
    return (str(t)
            .replace("&le;", "&lt;=").replace("&ge;", "&gt;=")
            .replace("&rarr;", " -&gt; ").replace("&harr;", " &lt;-&gt; ")
            .replace("&times;", " x ").replace("&asymp;", "~")
            .replace("→", " -&gt; ").replace("≤", " &lt;= ").replace("≥", " &gt;= ")
            .replace("×", " x ").replace("Σ", "SUM").replace("∞", "inf")
            .replace("–", "-").replace("—", "-").replace("·", "-"))


def P(t, s="body"):
    return Paragraph(_fix(t), S[s])


def BUL(items):
    return [Paragraph(_fix("&bull;&nbsp;&nbsp;" + it), S["bullet"]) for it in items]


def CODE(t):
    safe = (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>"))
    return Paragraph(safe, S["code"])


def TBL(headers, rows, widths):
    data = [[Paragraph(_fix(h), S["cellb"]) for h in headers]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else Paragraph(_fix(str(c)), S["cell"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADBG),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(2, len(data), 2):
        st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafb")))
    t.setStyle(TableStyle(st))
    return t


story = []
A = story.append


def H1(t): A(P(t, "h1"))
def H2(t): A(P(t, "h2"))
def BODY(t): A(P(t, "body"))
def SMALL(t): A(P(t, "small"))
def SP(n=6): A(Spacer(1, n))
def PB(): A(PageBreak())


# ============================ COVER ============================
A(Spacer(1, 40))
A(P("DQ Compass", "title"))
A(P("Reporting &amp; Analytics &mdash; Metrics Reference", "h1"))
A(Spacer(1, 8))
A(P("MBA-ESG / SG GSC Datathon 2026 &mdash; <i>DQ Compass: a Plug-and-Play Data "
    "Quality Control Layer for EUCs</i>", "subtitle"))
A(P("Working Group 1", "subtitle"))
A(P(f"Generated {date.today().isoformat()}", "subtitle"))
A(Spacer(1, 18))
A(P("Every KPI, panel and chart on the <b>/reporting</b> page, and the exact "
    "calculation behind each. Source of truth:", "body"))
A(TBL(["Concern", "File / function"], [
    ["Page assembly (what each panel receives)", "rule_authoring/app.py :: reporting_context()"],
    ["Score / dataset score / summaries / alerts / trend", "reporting/scorecard.py"],
    ["Per-control metrics (null_count, invalid_count, ...)", "controls.py"],
    ["Threshold flip, exception_pct, ledger counts", "dq_engine.py"],
    ["Chart geometry (score bar, trend line, bars, sparkline)", "rule_authoring/charts.py"],
    ["Page markup / labels", "rule_authoring/templates/reporting.html"],
], [64 * mm, 104 * mm]))
PB()

# ============================ 1. HOW THE PAGE IS FED ============================
H1("1 &nbsp; How the page is fed")
BODY("The page never re-reads the raw datasets. It reads the <b>Evidence Pack</b> that "
     "<font face='Courier'>dq_engine.py</font> wrote for each run under "
     "<font face='Courier'>evidence/&lt;run_id&gt;/</font> (per-rule <font face='Courier'>"
     "*_result.json</font>, <font face='Courier'>*_exceptions.csv</font>, "
     "<font face='Courier'>run_summary.json</font>) plus the append-only "
     "<font face='Courier'>evidence/runs_ledger.jsonl</font>.")
H2("Focus run, previous run, window")
BODY("<font face='Courier'>reporting_context(focus_run_id)</font> lists every run "
     "(<b>newest first</b>) and picks a <b>focus run</b>:")
for x in BUL([
    "<b>focus run</b> = the run chosen in the selector (<font face='Courier'>?run=&lt;id&gt;</font>); "
    "default = the most recent run. Drives <i>every panel</i> except the two below.",
    "<b>previous run</b> = the run immediately older than the focus run "
    "(<font face='Courier'>runs[focus_idx + 1]</font>). Used by the score delta and "
    "&ldquo;What changed&rdquo;.",
    "<b>window</b> = the focus run plus up to 11 older runs "
    "(<font face='Courier'>runs[focus_idx : focus_idx + 12]</font>). Used only by the "
    "<b>Trend</b> chart and the <b>Rule reliability</b> table.",
]):
    A(x)
SMALL("If no run is selected and there is only one run, the delta / previous-run panels show "
      "&ldquo;first run&rdquo;. An unknown ?run id silently falls back to the latest run.")

H2("Vocabulary used throughout")
A(TBL(["Term", "Meaning"], [
    ["status", "PASS / FAIL / ERROR for one rule in one run (from *_result.json)."],
    ["ERROR", "The rule could not execute: unknown control type, or its data source is "
              "missing / retired. The run continues; the rule scores as a total miss."],
    ["exception_count", "Number of rows in that rule's <run>_exceptions.csv = the failing "
                        "records. Kept even when a threshold flips the status to PASS."],
    ["exc_pct", "metrics.exception_pct if the engine recorded it, else "
                "round(100 x exception_count / total_records, 2), else 100 if FAIL else 0."],
    ["W(severity)", "Severity weight: High = 5, Medium = 2, Low = 1."],
    ["counts", "Per-run tally {PASS, FAIL, ERROR} stored in the run ledger by the engine."],
], [30 * mm, 138 * mm]))
PB()

# ============================ 2. SHARED BUILDING BLOCKS ============================
H1("2 &nbsp; Shared building blocks")

H2("2.1  Per-control metrics (controls.py)")
BODY("Each control function returns <font face='Courier'>{status, metrics, exceptions}</font>. "
     "<font face='Courier'>total_records</font> is the row count actually evaluated. "
     "<font face='Courier'>status = FAIL</font> as soon as one exception exists (before any "
     "threshold is applied).")
A(TBL(["Dimension", "Exceptions = rows where...", "Headline metric"], [
    ["Completeness", "field IS NULL or trimmed value is empty",
     "completeness_pct = round(100 x (total - null_count) / total, 2)"],
    ["Validity", "field NOT IN allowed_values  /  NOT full-match of regex  /  outside [min,max]",
     "valid_pct = round(100 x (total - invalid_count) / total, 2)"],
    ["Uniqueness", "row is part of any duplicated group on the key column(s) "
                   "(pandas duplicated(keep=False))",
     "duplicate_pct = round(100 x duplicate_count / total, 2)"],
    ["Consistency", "field value not found in the set of ref_dataset.ref_field values",
     "orphan_pct = round(100 x orphan_count / total, 2)"],
    ["Timeliness", "(reference_date - field_date).days &gt; max_lag_days  "
                   "(exceptions get an added lag_days column)",
     "within_sla_pct = round(100 x (total - sla_breach_count) / total, 2)"],
    ["Reconciliation", "key missing on one side, OR "
                       "abs(src - ref) / ref x 100 &gt; tolerance_pct  "
                       "(total = number of merged/joined rows)",
     "reconciled_pct = round(100 x (total - break_count) / total, 2)"],
], [26 * mm, 92 * mm, 50 * mm]))

H2("2.2  Tolerance threshold (dq_engine.py :: _apply_threshold)")
BODY("If a rule sets <font face='Courier'>threshold_pct</font>, the engine records "
     "<font face='Courier'>exception_pct = round(100 x exception_count / total_records, 2)</font> "
     "and, when the rule FAILED but <font face='Courier'>exception_pct &lt;= threshold_pct</font>, "
     "flips the status to <b>PASS</b> and sets <font face='Courier'>within_threshold = true</font>. "
     "The exception rows are still written and still counted &mdash; only the status changes.")

H2("2.3  Composite DQ score (reporting/scorecard.py :: overall_dq_score)")
BODY("One number for a whole run, 0&ndash;100, higher is better. Severity-weighted so a High "
     "failure hurts 5x a Low one.")
A(CODE(
    "weight  = SUM over every rule in the run of  W(severity)\n"
    "penalty = SUM over every rule of:\n"
    "            PASS               -> 0\n"
    "            ERROR              -> W(severity)              (counted as a total miss)\n"
    "            FAIL               -> W(severity) x min(1, exc_pct / 100)\n"
    "\n"
    "score = 100                                   if weight == 0\n"
    "      = max(0, round(100 x (1 - penalty/weight), 1))   otherwise"))
SMALL("A FAIL with a tiny exception rate barely moves the score; a FAIL at 100% exceptions, or "
      "an ERROR, costs the rule's full weight. build_dataset_score uses the identical formula "
      "restricted to one dataset's rules.")

H2("2.4  Traffic light (used in the CSV / HTML downloads)")
A(TBL(["status / severity", "Light"], [
    ["status == PASS", "GREEN"],
    ["status == ERROR", "GREY"],
    ["status == FAIL  and  severity == High", "RED"],
    ["status == FAIL  and  severity != High", "ORANGE"],
], [70 * mm, 30 * mm]))
PB()

# ============================ 3. KPI STRIP ============================
H1("3 &nbsp; The KPI strip (top of the page)")
BODY("Six tiles, all computed for the <b>focus run</b>.")

H2("3.1  Composite DQ score")
BUL_ITEMS = [
    "<b>Value</b>: <font face='Courier'>overall_dq_score(focus_run)</font> &mdash; section 2.3.",
    "<b>Tile colour</b>: green if score &gt;= 90, amber if &gt;= 70, red otherwise.",
    "<b>Delta</b>: <font face='Courier'>round(score(focus) - score(previous_run), 1)</font>. "
    "Shown as a triangle up (green) or down (red); &ldquo;first run&rdquo; if there is no older run.",
    "<b>Sparkline</b>: <font face='Courier'>score_series</font> = the composite score of each run "
    "in the window, oldest to newest (section 6.1).",
]
for x in BUL(BUL_ITEMS):
    A(x)

H2("3.2  Rules passing")
for x in BUL([
    "<b>Value</b>: <font face='Courier'>pass_rate = round(100 x n_pass / n_rules, 1)</font> %.",
    "<font face='Courier'>n_pass</font> = rules whose status is PASS in the focus run "
    "(a threshold flip counts as PASS). <font face='Courier'>n_rules</font> = number of rule "
    "results in the run.",
    "<b>Foot</b>: &ldquo;n_pass of n_rules controls&rdquo;.",
]):
    A(x)

H2("3.3  Open High-severity issues")
for x in BUL([
    "<b>Value</b>: <font face='Courier'>len(alerts)</font>.",
    "<font face='Courier'>alerts</font> (build_alerts) = every rule in the focus run with "
    "<font face='Courier'>status in {FAIL, ERROR}</font> AND "
    "<font face='Courier'>severity == High</font>.",
    "Tile is red if any exist, green if none.",
]):
    A(x)

H2("3.4  Exception records")
for x in BUL([
    "<b>Value</b>: <font face='Courier'>total_exc = SUM of exception_count</font> over every rule "
    "in the focus run.",
    "This is a count of <i>failing rows</i> across all rules, not a count of rules.",
]):
    A(x)

H2("3.5  Datasets under control")
for x in BUL([
    "<b>Value</b>: <font face='Courier'>covered / datasets_total</font>.",
    "<font face='Courier'>datasets_total</font> = number of registered data sources.",
    "<font face='Courier'>covered</font> = how many of them have at least one <i>active</i> rule "
    "on at least one dimension (from <font face='Courier'>build_coverage</font>: "
    "<font face='Courier'>{source: {dimension: [rule_ids]}}</font>, count sources with a "
    "non-empty cell).",
]):
    A(x)

H2("3.6  Failing / errored")
for x in BUL([
    "<b>Value</b>: <font face='Courier'>n_fail / n_error</font>, read straight from the focus "
    "run's ledger <font face='Courier'>counts</font> (FAIL, ERROR).",
    "&ldquo;errored&rdquo; = a rule whose source or config is broken; investigate before trusting "
    "the rest of the run.",
]):
    A(x)
PB()

# ============================ 4. BUSINESS PANELS ============================
H1("4 &nbsp; &ldquo;For control owners &amp; risk&rdquo;")

H2("4.1  Overall data quality (score bar)")
BODY("Same number as KPI 3.1, drawn as a bar (<font face='Courier'>charts.score_bar</font>): "
     "fill width = score %, colour band at 90 / 70, tick marks at 70 and 90, scale 0-70-90-100. "
     "The delta pill repeats the vs-previous-run change.")

H2("4.2  Trend &mdash; last N runs (charts.trend_chart)")
BODY("Input = <font face='Courier'>ctx.trend</font>: the window runs, oldest to newest, each "
     "<font face='Courier'>{label = MM-DD, pass, fail, error, score}</font> where pass/fail/error "
     "come from that run's ledger counts and score = <font face='Courier'>overall_dq_score</font> "
     "of that run.")
for x in BUL([
    "<b>Line</b> (accent colour): the composite DQ score per run.",
    "<b>Y axis is auto-floored</b> so movement stays visible when scores cluster high: "
    "<font face='Courier'>lo = max(0, min(score) - 8)</font>; then "
    "<font face='Courier'>lo = 0 if lo &lt; 12 else round(lo/5) x 5</font>; the axis runs lo..100.",
    "<b>Composition strip</b> under each run: a small stacked bar split "
    "pass / fail / error (green / red / grey), each segment width proportional to its share of "
    "that run's total.",
    "Hovering a point shows <font face='Courier'>timestamp - nP/nF/nE - score</font>.",
]):
    A(x)

H2("4.3  Dataset health (build_dataset_score)")
BODY("One row per dataset that has rules, <b>sorted worst score first</b>.")
A(CODE(
    "for each dataset (grouped by rule_configuration_snapshot.dataset_scope):\n"
    "  weight  = SUM W(severity) over that dataset's rules\n"
    "  penalty = SUM  PASS 0 | ERROR W | FAIL W x min(1, exc_pct/100)\n"
    "  dq_score = 100 if weight == 0\n"
    "           else max(0, round(100 x (1 - penalty/weight), 1))\n"
    "  n_pass / n_fail / n_error = status tallies ;  n_rules = count"))
SMALL("Bar width = dq_score %. Colour band 90 (green) / 70 (amber) / below (red). The green / red "
      "/ err chips are n_pass / n_fail / n_error.")

H2("4.4  Coverage &amp; status (3-state matrix)")
BODY("Rows = data sources, columns = the 6 DQ dimensions. Each cell:")
A(CODE(
    "ids   = ACTIVE rules with (dataset_scope == row, control_type == column)\n"
    "state = 'none'  if ids is empty                       -> grey, blank\n"
    "      = 'fail'  if any of those rules is FAIL or ERROR -> red,  shows count\n"
    "      = 'pass'  otherwise                              -> green, shows count"))
SMALL("The number in a coloured cell is how many rules sit in that dataset x dimension. "
      "&ldquo;Datasets under control&rdquo; (KPI 3.5) = rows with at least one non-grey cell.")

H2("4.5  Open issues &mdash; failing High-severity controls")
BODY("The <font face='Courier'>alerts</font> list from 3.3, one card each: rule id + name, "
     "<font face='Courier'>exception_count</font> and dataset, owner, and the "
     "<font face='Courier'>remediation_action</font> text looked up from "
     "<font face='Courier'>control_catalogue.csv</font> by rule id.")

H2("4.6  Exceptions by owner (accountability)")
BODY("Horizontal bars (<font face='Courier'>charts.hbars</font>). Input = "
     "<font face='Courier'>build_exception_summary</font> rows for dimension "
     "<font face='Courier'>owner</font>: for each owner, "
     "<font face='Courier'>total_exceptions = SUM exception_count</font> over that owner's rules. "
     "Sorted by total descending; each bar width = value / (largest value) x 100%.")
PB()

# ============================ 5. ENGINEERING PANELS ============================
H1("5 &nbsp; &ldquo;For data engineers&rdquo;")

H2("5.1  Exceptions by DQ dimension")
BODY("Same as 4.6 but grouped by <font face='Courier'>control_type</font> "
     "(Completeness, Validity, ...). Answers &ldquo;which kind of quality problem produces the "
     "most failing rows in this run&rdquo;.")

H2("5.2  Top offending rules (this run)")
BODY("<font face='Courier'>by_rule</font> = every rule in the focus run with "
     "<font face='Courier'>exception_count &gt; 0</font>, sorted descending, top 8, drawn with "
     "<font face='Courier'>hbars</font>. Bar value = that rule's exception_count.")

H2("5.3  Rule reliability (last N runs)")
BODY("Aggregated over the <b>window</b> (focus run + up to 11 older).")
A(CODE(
    "for each rule seen in the window:\n"
    "  runs  = number of window runs that contain the rule\n"
    "  fail  = number of those runs where status == FAIL\n"
    "  error = number where status == ERROR\n"
    "  last  = the rule's status in the focus run\n"
    "\n"
    "fail rate  = (fail + error) / max(1, runs)      -> table is sorted by this, desc; top 12\n"
    "mini-bar width = (fail + error) / runs x 100%"))

H2("5.4  What changed since the previous run")
BODY("Compares each rule present in <b>both</b> the focus run and the previous run:")
A(CODE(
    "status changed              -> flip:  from -> to   (green up if new status is PASS)\n"
    "both FAIL, exception_count changed\n"
    "                            -> delta: (cur - prev) exception(s)   (green if fewer)"))
SMALL("&ldquo;No previous run to compare against&rdquo; on the oldest run; "
      "&ldquo;no control changed&rdquo; when both runs agree.")

H2("5.5  Broken controls (ERROR)")
BODY("<font face='Courier'>error_rules</font> = rules whose status is ERROR in the focus run, "
     "with the recorded reason (e.g. <i>source unavailable</i>). These are excluded from a "
     "meaningful pass rate and cost full weight in the score.")
PB()

# ============================ 6. CHART ENCODINGS ============================
H1("6 &nbsp; Chart encodings (rule_authoring/charts.py)")
BODY("All charts are inline SVG/HTML with no library; colours are CSS variables so they follow "
     "the light/dark theme.")
A(TBL(["Chart", "Encoding"], [
    ["score_bar(value, delta)",
     "Fill width = clamp(value, 0, 100) %. Colour: >=90 ok, >=70 warn, else bad. "
     "Fixed ticks at 70 and 90; scale labels 0 / 70 / 90 / 100."],
    ["sparkline(vals)",
     "Polyline in a 60x16 box. y = 16 - (v - min) / (max - min) x 13 ; x evenly spaced. "
     "Needs >= 2 points, else nothing."],
    ["trend_chart(series)",
     "See 4.2. Score line + faint area; per-run pass/fail/error strip; auto-floored y axis; "
     "gridlines at {lo, midpoint rounded to 5, 100}."],
    ["hbars(items, label, val, tone)",
     "One row per item with val &gt; 0. Bar width = val / max(val) x 100%. Rows keep the input "
     "order (callers pre-sort by value desc)."],
    ["mini_bar(hits, total, tone)",
     "Single inline bar, width = hits / total x 100%."],
    ["donut(p, f, e)",
     "Stacked ring; each arc length proportional to p, f, e over their sum; centre shows p+f+e. "
     "(Defined for reuse; the run-detail page uses it.)"],
], [46 * mm, 122 * mm]))
PB()

# ============================ 7. DOWNLOADS ============================
H1("7 &nbsp; Downloads")
BODY("The links at the bottom of the page serve files that "
     "<font face='Courier'>reporting/scorecard.py</font> writes into "
     "<font face='Courier'>reporting/</font>. They are regenerated by "
     "<font face='Courier'>dqcompass report</font> (or "
     "<font face='Courier'>python reporting/scorecard.py &lt;run_id&gt;</font> for a specific run).")
A(TBL(["File", "Builder", "One row per / contents"], [
    ["scorecard.csv", "build_scorecard",
     "one rule: status, traffic_light, exception_count, and every metric_* value"],
    ["dataset_score.csv", "build_dataset_score", "one dataset: n_pass/fail/error, dq_score (section 4.3)"],
    ["coverage.csv", "build_coverage", "one dataset x dimension pair actually used: rule_ids, n_rules"],
    ["exception_summary.csv", "build_exception_summary",
     "long format: dimension in {severity, owner, control_type, dataset} x key -> "
     "failing_rules, error_rules, total_exceptions"],
    ["trend.csv", "build_trend", "one run from the ledger: rules_executed, pass, fail, error"],
    ["alerts.json", "build_alerts", "failing High-severity rules + remediation_action"],
    ["exceptions_detail.csv", "build_exceptions_detail",
     "every failing row from every rule, prefixed with rule_id + severity"],
    ["scorecard.html", "to_html", "standalone traffic-light table for a quick demo"],
], [40 * mm, 42 * mm, 86 * mm]))
SP(4)
SMALL("Note: the downloadable files reflect whichever run scorecard.py last ran for (the latest "
      "run by default) - they are not re-scoped by the on-page run selector. Pass a run id on the "
      "command line to export a past run.")

SP(10)
A(P("Worked example (current seeded demo, focus = latest run)", "h2"))
A(TBL(["KPI", "Value", "Why"], [
    ["Composite DQ score", "87.2 / 100",
     "14 rules; weights sum = 46; penalty ~ 5.9 (High FAILs at high exc_pct + Medium FAILs); "
     "100 x (1 - 5.9/46) ~ 87.2"],
    ["Rules passing", "57.1 %", "8 PASS of 14"],
    ["Open High-severity issues", "4", "VAL_LIST_FAIL, CON_FAIL, TIM_FAIL, REC_FAIL"],
    ["Exception records", "~74k", "sum of exception_count (CMP_FAIL 17,708 + UNQ_FAIL 27,290 + "
                                  "CON_FAIL 8,997 + CMP_THRESHOLD_PASS 19,969 + ...)"],
    ["Datasets under control", "3 / 6", "finance_data, feed_status, recon_euc_positions have rules; "
                                        "the 3 reference-only sources do not"],
    ["Failing / errored", "6 / 0", "ledger counts for the run"],
], [40 * mm, 22 * mm, 106 * mm]))


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 12 * mm, "DQ Compass - Reporting Metrics Reference")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
    title="DQ Compass - Reporting Metrics Reference", author="Working Group 1")
doc.addPageTemplates([PageTemplate(id="main",
                                   frames=[Frame(doc.leftMargin, doc.bottomMargin,
                                                 doc.width, doc.height, id="main")],
                                   onPage=_page)])
doc.build(story)
print(f"Wrote {OUT}")
