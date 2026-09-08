"""
build_mapping.py -- generate the DQ Compass Supervisory Mapping reference PDF.

    pip install reportlab
    python docs/build_mapping.py

Output: docs/DQ_Compass_Supervisory_Mapping.pdf

Explains the Supervisory Mapping (brief Appendix C): what it is, how
mapping.py generates every row from the catalogue, the C.2 / C.3 / C.4 parts,
the regulatory_ref hook, the surfaces, and a worked example.
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

OUT = Path(__file__).resolve().parent / "DQ_Compass_Supervisory_Mapping.pdf"

INK = colors.HexColor("#14161c")
MUTED = colors.HexColor("#5b6270")
ACCENT = colors.HexColor("#c1122a")
LINE = colors.HexColor("#d3d7df")
HEADBG = colors.HexColor("#f0f1f4")
OKBG = colors.HexColor("#e7f6ec")
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
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7.7, leading=10.4,
                           textColor=INK, backColor=CODEBG, borderPadding=6,
                           spaceBefore=3, spaceAfter=7),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=7.7, leading=10, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=7.7, leading=10, textColor=INK),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10.5,
                            textColor=MUTED, spaceAfter=4),
}


def _fix(t: str) -> str:
    return (str(t)
            .replace("&le;", "&lt;=").replace("&ge;", "&gt;=")
            .replace("&rarr;", " -&gt; ").replace("&harr;", " &lt;-&gt; ")
            .replace("&times;", " x ").replace("→", " -&gt; ")
            .replace("≤", " &lt;= ").replace("≥", " &gt;= ").replace("×", " x ")
            .replace("–", "-").replace("—", "-").replace("·", "-").replace("✓", "YES"))


def P(t, s="body"):
    return Paragraph(_fix(t), S[s])


def BUL(items):
    return [Paragraph(_fix("&bull;&nbsp;&nbsp;" + it), S["bullet"]) for it in items]


def CODE(t):
    safe = (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>"))
    return Paragraph(safe, S["code"])


def TBL(headers, rows, widths, ok_col=None):
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
    if ok_col is not None:
        st += [("BACKGROUND", (ok_col, 1), (ok_col, -1), OKBG),
               ("ALIGN", (ok_col, 0), (ok_col, -1), "CENTER")]
    for i in range(2, len(data), 2):
        st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafb")))
    t.setStyle(TableStyle(st))
    return t


def YES():
    return Paragraph('<font color="#128a4b"><b>YES</b></font>', S["cellb"])


story = []
A = story.append


def H1(t): A(P(t, "h1"))
def H2(t): A(P(t, "h2"))
def BODY(t): A(P(t, "body"))
def SMALL(t): A(P(t, "small"))
def SP(n=6): A(Spacer(1, n))
def PB(): A(PageBreak())


# ============================ COVER ============================
A(Spacer(1, 42))
A(P("DQ Compass", "title"))
A(P("The Supervisory Mapping &mdash; Appendix C", "h1"))
A(Spacer(1, 8))
A(P("MBA-ESG / SG GSC Datathon 2026 &mdash; <i>DQ Compass: a Plug-and-Play Data "
    "Quality Control Layer for EUCs</i>", "subtitle"))
A(P("Working Group 1", "subtitle"))
A(P(f"Generated {date.today().isoformat()}", "subtitle"))
A(Spacer(1, 20))
A(P("The Supervisory Mapping is the bridge between the technical control layer and a "
    "supervisor's language (BCBS 239). For every control it states <b>which supervisory "
    "requirement it satisfies</b>, <b>what evidence it produces</b>, and <b>the hash of the "
    "run that proves it</b>. It is generated entirely from the Control Catalogue &mdash; there "
    "is no separate mapping document to keep in sync.", "body"))
SP(10)
A(TBL(["Item", "Where"], [
    ["Generator", "mapping.py :: build_mapping()  /  mapping_csv()"],
    ["Page", "/mapping  (mapping_view -> templates/mapping.html)"],
    ["Export", "reporting/supervisory_mapping.csv  (python mapping.py  or  dqcompass mapping)"],
    ["Catalogue hook", "regulatory_ref column (canonical schema, rule_authoring/schema.py)"],
], [34 * mm, 134 * mm]))
PB()

# ============================ 1. WHAT / WHY ============================
H1("1 &nbsp; What it is and why")
BODY("Appendix C asks the solution to demonstrate <b>governance and auditability</b> in "
     "supervisory terms: not just &ldquo;we run N checks&rdquo;, but &ldquo;here, control by "
     "control, is the regulatory expectation each one covers, the evidence it leaves, and proof "
     "it was actually executed&rdquo;.")
for x in BUL([
    "<b>Auto-generated from the catalogue</b> &mdash; add / edit / retire a rule and the mapping "
    "follows on the next page load. Nothing to maintain by hand, so it can never drift.",
    "<b>One row per ACTIVE rule</b> (inactive rules are skipped &mdash; they are not a live "
    "control).",
    "<b>Three sub-parts</b> of Appendix C: C.2 (requirement -&gt; control -&gt; evidence -&gt; "
    "output), C.3 (per-rule traceability to a run), C.4 (supervisory principles demonstrated).",
]):
    A(x)

# ============================ 2. HOW A ROW IS BUILT ============================
H1("2 &nbsp; How each row is built &mdash; build_mapping()")
BODY("<font face='Courier'>build_mapping()</font> reads "
     "<font face='Courier'>control_catalogue.csv</font> and, for every active rule, emits a "
     "14-field row:")
A(TBL(["Field", "Source / rule"], [
    ["rule_id", "catalogue"],
    ["requirement", "the rule's regulatory_ref if set; ELSE "
                    "DEFAULT_REQUIREMENT[control_type] (see 3) - so every control is mapped"],
    ["control_implemented", "control_name"],
    ["control_type / severity / owner / kpi", "catalogue"],
    ["logic_definition", "the generated pseudo-SQL of the rule (auditor-readable)"],
    ["evidence_generated", "fixed statement: \"Evidence Pack per run ([output_type]): metrics, "
                           "exception dataset, run_summary.json, system_trace.json, "
                           "run_log.jsonl; verification.json on request\""],
    ["output", "the rule's output_type (Error dataset / Validation report / ...)"],
    ["last_run_id / _timestamp / _status / _hash", "_last_run_for_rule() - see 4"],
], [56 * mm, 112 * mm]))

# ============================ 3. THE REQUIREMENT ============================
H1("3 &nbsp; The supervisory requirement")
BODY("Two ways a control gets a requirement:")
H2("3.1  Explicit &mdash; the regulatory_ref column")
BODY("A free-text column in the catalogue's canonical schema. The authoring form suggests "
     "values (<font face='Courier'>schema.REGULATORY_REF_SUGGESTIONS</font>): BCBS 239 "
     "Principles 3-7, &ldquo;SG internal Data Quality framework&rdquo;, &ldquo;EUC governance "
     "policy&rdquo;. Set it to bind a specific rule to a specific supervisory article.")
H2("3.2  Fallback &mdash; DEFAULT_REQUIREMENT[control_type]")
BODY("If <font face='Courier'>regulatory_ref</font> is blank, a per-dimension default is used, "
     "so the mapping is never empty:")
A(TBL(["Control type", "Default requirement"], [
    ["Completeness", "Data completeness (BCBS 239 - Completeness)"],
    ["Validity", "Accuracy & integrity - conformance to defined formats / domains (BCBS 239 - Accuracy)"],
    ["Uniqueness", "No duplication of records or keys (BCBS 239 - Accuracy & Integrity)"],
    ["Consistency", "Referential integrity across data sets (BCBS 239 - Accuracy & Integrity)"],
    ["Timeliness", "Data timeliness / freshness (BCBS 239 - Timeliness)"],
    ["Reconciliation", "Reconciliation across sources (BCBS 239 - Accuracy & Reconciliation)"],
], [34 * mm, 134 * mm]))

# ============================ 4. TRACEABILITY TO A RUN ============================
H1("4 &nbsp; Traceability to a run &mdash; _last_run_for_rule()")
BODY("This is Appendix C.3: every control must trace to a concrete execution.")
A(CODE(
    "walk runs_ledger.jsonl BACKWARDS (most recent first)\n"
    "for each run: if  evidence/<run_id>/<rule_id>_result.json  exists:\n"
    "     return { run_id, timestamp, status (from that result file), run_hash }\n"
    "if no run ever executed this rule  ->  \"never executed\""))
BODY("So each mapping row carries the <b>run_id</b>, the rule's <b>status</b> in that run, the "
     "run <b>timestamp</b> and the run <b>run_hash</b> &mdash; a tamper-evident pointer into the "
     "Evidence Pack. On the page the run_id links straight to <font face='Courier'>"
     "/runs/&lt;id&gt;</font>.")

# ============================ 5. C.4 PRINCIPLES ============================
H1("5 &nbsp; C.4 &mdash; supervisory principles demonstrated")
BODY("A fixed list (<font face='Courier'>mapping.PRINCIPLES</font>), each tied to a concrete "
     "mechanism of the solution:")
A(TBL(["Principle", "How DQ Compass demonstrates it"], [
    ["Traceability", "Every control links to its rule definition, its dataset (snapshot + "
                     "SHA-256 hash) and its execution run (run_id + run_hash)."],
    ["Repeatability", "Controls produce identical results under identical inputs - proven by "
                      "\"Verify this run\", which re-executes the stored config against the "
                      "stored snapshots."],
    ["Auditability", "An independent party can reconstruct any run from evidence/<run_id>/ "
                     "(config snapshot, dataset snapshots, processing log, system trace) and "
                     "validate the outcome."],
    ["Governance", "Controls are owned (owner), monitored (catalogue + coverage matrix), "
                   "versioned (hash-chained changelogs) and actionable (remediation_action, "
                   "alerts.json)."],
], [30 * mm, 138 * mm]))
PB()

# ============================ 6. SURFACES ============================
H1("6 &nbsp; Surfaces")
A(TBL(["Surface", "Contents"], [
    ["/mapping page", "The C.2 / C.3 table (Rule | Requirement | Control implemented | Evidence "
                      "generated | Output | Last run) followed by the C.4 principles card. The "
                      "Last-run cell links to the run's Evidence Pack."],
    ["supervisory_mapping.csv", "The same rows, all 14 columns, written by "
                                "python mapping.py (or dqcompass mapping) into reporting/. "
                                "Download button on the page. Power BI / audit-pack ready."],
], [40 * mm, 128 * mm]))

# ============================ 7. COMPLIANCE ============================
H1("7 &nbsp; Appendix C compliance")
A(TBL(["Requirement (Appendix C)", "Where satisfied", "Met"], [
    ["C.2 Requirement -> Control -> Evidence -> Output", "build_mapping() row; /mapping table", YES()],
    ["C.3 Per-control traceability to an execution", "_last_run_for_rule(): run_id + status + "
                                                     "run_hash per rule", YES()],
    ["C.4 Supervisory principles demonstrated", "PRINCIPLES (Traceability, Repeatability, "
                                                "Auditability, Governance)", YES()],
    ["Mapping stays in sync with the controls", "generated from the catalogue on every load", YES()],
    ["Machine-readable export", "supervisory_mapping.csv (14 columns)", YES()],
], [78 * mm, 76 * mm, 14 * mm], ok_col=2))

# ============================ 8. WORKED EXAMPLE ============================
H1("8 &nbsp; Worked example (current demo)")
BODY("14 active rules -&gt; 14 mapped rows. Requirement source per rule:")
A(TBL(["Rule", "Requirement (source)", "Last run status / hash"], [
    ["CMP_PASS", "BCBS 239 - Principle 4 (Completeness)  [regulatory_ref]", "PASS - b1c8ba33ffd68f60"],
    ["CMP_FAIL", "Data completeness (BCBS 239 - Completeness)  [default]", "FAIL - b1c8ba33ffd68f60"],
    ["VAL_LIST_FAIL", "Accuracy & integrity - formats / domains  [default]", "FAIL - b1c8ba33ffd68f60"],
    ["UNQ_PASS", "BCBS 239 - Principle 3 (Accuracy and Integrity)  [regulatory_ref]", "PASS - b1c8ba33..."],
    ["CON_FAIL", "BCBS 239 - Principle 3 (Accuracy and Integrity)  [regulatory_ref]", "FAIL - b1c8ba33..."],
    ["TIM_FAIL", "BCBS 239 - Principle 5 (Timeliness)  [regulatory_ref]", "FAIL - b1c8ba33..."],
    ["REC_FAIL", "BCBS 239 - Principle 7 (Accuracy - reporting)  [regulatory_ref]", "FAIL - b1c8ba33..."],
    ["...", "the other 7 rules take the per-dimension default", "..."],
], [30 * mm, 96 * mm, 42 * mm]))
SP(4)
for x in BUL([
    "6 rules carry an explicit <font face='Courier'>regulatory_ref</font>; the other 8 inherit "
    "the dimension default &mdash; every control is still mapped.",
    "All rows point at run <font face='Courier'>0f13237e</font> "
    "(<font face='Courier'>run_hash b1c8ba33ffd68f60</font>) &mdash; the latest execution that "
    "contains each rule's result file.",
    "Regenerate: <font face='Courier'>python mapping.py</font> -&gt; "
    "<font face='Courier'>reporting/supervisory_mapping.csv (14 rules)</font>.",
]):
    A(x)


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 12 * mm, "DQ Compass - The Supervisory Mapping")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
    title="DQ Compass - The Supervisory Mapping", author="Working Group 1")
doc.addPageTemplates([PageTemplate(id="main",
                                   frames=[Frame(doc.leftMargin, doc.bottomMargin,
                                                 doc.width, doc.height, id="main")],
                                   onPage=_page)])
doc.build(story)
print(f"Wrote {OUT}")
