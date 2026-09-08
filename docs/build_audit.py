"""
build_audit.py -- generate the DQ Compass Audit Layer reference PDF.

    pip install reportlab
    python docs/build_audit.py

Output: docs/DQ_Compass_Audit_Layer.pdf

Explains, in detail, everything implemented for the "Audit" part of the brief
(section 4.4 / Appendix B): the per-run Evidence Pack, the hash-chained run
ledger, independent verification, human sign-off, the two change logs, and the
audit surfaces in the web app.
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

OUT = Path(__file__).resolve().parent / "DQ_Compass_Audit_Layer.pdf"

INK = colors.HexColor("#14161c")
MUTED = colors.HexColor("#5b6270")
ACCENT = colors.HexColor("#c1122a")
LINE = colors.HexColor("#d3d7df")
HEADBG = colors.HexColor("#f0f1f4")
OKBG = colors.HexColor("#e7f6ec")
OK = colors.HexColor("#128a4b")
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
A(P("The Audit Layer &mdash; what we implemented", "h1"))
A(Spacer(1, 8))
A(P("MBA-ESG / SG GSC Datathon 2026 &mdash; <i>DQ Compass: a Plug-and-Play Data "
    "Quality Control Layer for EUCs</i>", "subtitle"))
A(P("Working Group 1", "subtitle"))
A(P(f"Generated {date.today().isoformat()}", "subtitle"))
A(Spacer(1, 20))
A(P("The Audit Layer is the brief's fourth stage &mdash; <b>DEFINE &rarr; EXECUTE &rarr; "
    "REPORT &rarr; EVIDENCE</b> (section 4.4, Appendix B). Its job: make every run "
    "<b>traceable</b>, <b>reproducible</b> and <b>tamper-evident</b>, and record who "
    "reviewed it. This document lists each mechanism and the exact artefact it produces.", "body"))
SP(10)
A(TBL(["Mechanism", "Produced by", "Artefact"], [
    ["Evidence Pack (per run)", "dq_engine.py :: DQEngine.run()", "evidence/<run_id>/ (13+ files)"],
    ["Hash-chained run ledger", "dq_engine.py :: _append_ledger()", "evidence/runs_ledger.jsonl"],
    ["Independent verification", "dq_engine.py :: verify_run()", "evidence/<run_id>/verification.json"],
    ["Human sign-off", "app.py :: run_signoff()", "evidence/<run_id>/signoff.json"],
    ["Catalogue change log", "rule_authoring/store.py :: _log()", "catalogue_changelog.jsonl"],
    ["Data-source change log", "rule_authoring/source_store.py :: _log()", "data_sources_changelog.jsonl"],
    ["Audit surfaces (UI)", "app.py routes /runs, /runs/<id>, /activity", "browsable + downloadable"],
], [44 * mm, 66 * mm, 58 * mm]))
PB()

# ============================ 1. EVIDENCE PACK ============================
H1("1 &nbsp; The Evidence Pack &mdash; evidence/&lt;run_id&gt;/")
BODY("Every execution of the engine creates one folder, named by a random UUID4 "
     "<font face='Courier'>run_id</font>. Nothing is overwritten: a new run is a new folder. "
     "The folder covers the ten components Appendix B.2 asks for.")

A(TBL(["#", "Appendix B.2 component", "File(s)", "Content"], [
    ["1", "Run identification", "run_summary.json",
     "run_id (UUID4), run_timestamp_utc (ISO-8601 UTC), engine_version, catalogue_source; "
     "every per-rule record repeats execution_timestamp_utc"],
    ["2", "Dataset reference", "run_summary.json, <rule>_result.json",
     "dataset_reference = {name: content hash}. Hash = SHA-256 of "
     "pandas.util.hash_pandas_object(df, index=True), first 16 hex - a fingerprint of the "
     "exact data evaluated"],
    ["3", "Dataset snapshot", "snapshots/<name>.csv",
     "an exact copy of every input dataframe actually loaded, written once per dataset "
     "(df.to_csv, index=False)"],
    ["4", "Rule configuration snapshot", "<rule>_result.json .rule_configuration_snapshot",
     "dataset_scope, ref_dataset_scope, params (as executed), threshold_pct - the rule "
     "exactly as it was at run time"],
    ["5", "Execution parameters (resolved)", "<rule>_result.json .execution_parameters",
     "the effective values: e.g. reference_date 'today' -> reference_date_resolved "
     "'2026-09-08'; tolerance_pct and threshold_pct surfaced"],
    ["6", "Control results", "<rule>_result.json",
     "status (PASS / FAIL / ERROR), metrics {}, control_function name, exception_count, "
     "severity, owner"],
    ["7", "Exception dataset", "<rule>_exceptions.csv",
     "every failing row, written only when there is at least one; the path is recorded as "
     "exceptions_evidence_path"],
    ["8", "Processing log + system trace", "run_log.jsonl, run.log, system_trace.json",
     "ordered events (structured + text mirror) and the environment fingerprint (see 1.1)"],
    ["9", "Run integrity", "run_summary.json .previous_run_hash / .run_hash",
     "the link into the hash chain - see section 2"],
    ["10", "Sign-off", "signoff.json",
     "reviewed_by, reviewed_at, decision, comment - written from the Runs page (section 4)"],
], [6 * mm, 40 * mm, 44 * mm, 78 * mm]))
SMALL("A verification.json also appears once a verification has been run (section 3).")

H2("1.1  system_trace.json - the environment fingerprint")
BODY("So a reviewer can tell whether a difference comes from the data or from the tools:")
for x in BUL([
    "<b>engine_version</b>, <b>python_version</b>, <b>platform</b>, <b>host</b>",
    "<b>library versions</b>: pandas, pyyaml, openpyxl",
    "<b>SHA-256 (16 hex) of</b> control_catalogue.csv, datasets_config.yaml and controls.py "
    "- pin the exact rule set and the exact control code used",
    "<b>controls_used</b>: the control function name mapped to each rule id",
    "<b>retention_note</b>: states that a production deployment would store these files on "
    "WORM storage (S3 Object Lock / immutable data lake)",
]):
    A(x)

H2("1.2  run_log.jsonl / run.log - the processing trace")
BODY("One line per step, in order, both machine-readable (JSONL) and as plain text. Events: "
     "<font face='Courier'>run_start</font>, <font face='Courier'>dataset_loaded</font> "
     "(rows, columns, hash, snapshot path), <font face='Courier'>rule_start</font>, "
     "<font face='Courier'>rule_done</font> (status, exception count) or "
     "<font face='Courier'>rule_error</font>, <font face='Courier'>rule_skipped</font> "
     "(inactive rule), <font face='Courier'>system_trace_written</font>, "
     "<font face='Courier'>run_complete</font> (run_hash).")

H2("1.3  ERROR records - the run never crashes")
BODY("If a rule's control type is unknown, or its data source is missing / retired, the "
     "engine writes a <font face='Courier'>status: \"ERROR\"</font> record with the reason and "
     "<b>carries on with the next rule</b> (<font face='Courier'>_error_record</font>). "
     "The evidence is still complete; the reporting scores that rule as a total miss.")
PB()

# ============================ 2. RUN LEDGER ============================
H1("2 &nbsp; The hash-chained run ledger &mdash; evidence/runs_ledger.jsonl")
BODY("An append-only file, one JSON line per run, in run order. Each line:")
A(CODE(
    '{ "run_id", "timestamp", "engine_version", "catalogue_version_hash",\n'
    '  "rules_executed", "counts": {PASS, FAIL, ERROR},\n'
    '  "previous_run_hash", "run_hash" }'))

H2("2.1  How run_hash is computed")
A(CODE(
    "payload  = canonical_json( run_summary  without the previous_run_hash key )\n"
    "           # canonical_json = json.dumps(..., sort_keys=True)  -> order-independent\n"
    "\n"
    "run_hash = SHA-256( previous_run_hash + payload ).hexdigest()[:16]\n"
    "\n"
    "previous_run_hash = run_hash of the last line already in the ledger\n"
    "                    ( \"\"  for the very first run )"))
BODY("So <font face='Courier'>run_hash</font> depends on <b>the previous run's hash</b> plus "
     "<b>the entire content of this run's summary</b> - every rule status, every metric, every "
     "config snapshot, every dataset content hash.")

H2("2.2  What it guarantees")
for x in BUL([
    "<b>Tamper-evident</b>: change one byte in any past run_summary.json, or delete / reorder / "
    "insert a run, and that run's recomputed run_hash no longer matches the ledger, and every "
    "later line's previous_run_hash no longer matches either - the break is visible and "
    "localised.",
    "<b>Append-only history</b>: the next run always chains onto the last ledger line, so the "
    "sequence of runs is fixed once written.",
    "<b>Config drift is visible</b>: catalogue_version_hash on each line is the SHA-256 of the "
    "catalogue at that run - you can see the rule set changing between runs.",
]):
    A(x)
SMALL("Prototype scope: hashes are truncated to 16 hex (64-bit) for readability, and the "
      "chain detects tampering but is not itself cryptographically signed. Production would use "
      "full 256-bit digests and an HMAC / signature per line.")
PB()

# ============================ 3. VERIFICATION ============================
H1("3 &nbsp; Independent verification &mdash; verify_run() / Appendix B.3")
BODY("Proves that a recorded run is <b>reproducible from its own evidence alone</b> - not from "
     "the live catalogue or the live data.")

H2("3.1  What it does")
BODY("For the chosen run it reads <font face='Courier'>run_summary.json</font> and, for every "
     "non-ERROR rule result:")
for x in BUL([
    "looks up the control function by the recorded <font face='Courier'>control_type</font>",
    "reads the stored <font face='Courier'>snapshots/&lt;dataset&gt;.csv</font> "
    "(via <font face='Courier'>_read_snapshot</font>, which uses "
    "<font face='Courier'>engine=\"python\"</font> so it parses exactly as the engine's CSV "
    "connector did - a mixed-type column must not re-infer a different dtype)",
    "re-executes the function with the <b>stored</b> params (and the stored reference snapshot "
    "if the rule has one)",
    "re-applies the <b>stored</b> <font face='Courier'>threshold_pct</font>",
    "compares the recomputed <font face='Courier'>status</font> and "
    "<font face='Courier'>exception_count</font> against what was recorded",
]):
    A(x)
BODY("ERROR records are reported as &ldquo;not re-executed&rdquo; and count as a match (there "
     "is nothing to recompute).")

H2("3.2  Output - verification.json")
A(CODE(
    '{ "run_id", "verified_at", "run_hash",\n'
    '  "method": "re-execute stored rule config against stored dataset snapshots",\n'
    '  "all_match": true | false,\n'
    '  "checks": [ { rule_id, expected, recomputed,\n'
    '               expected_exceptions, recomputed_exceptions, match } , ... ] }'))

H2("3.3  How to run it")
A(TBL(["Surface", "Command / action"], [
    ["CLI (engine)", "python dq_engine.py --verify <run_id>   (exit 0 if reproducible, 1 if not)"],
    ["CLI (packaged)", "dqcompass verify <run_id>"],
    ["Web app", "\"Verify this run\" button on /runs/<run_id> - writes verification.json and "
                "shows the per-rule checks table"],
    ["CI gate", "dqcompass gate --severity High   (fails a pipeline when a High-severity "
                "control is failing)"],
], [30 * mm, 138 * mm]))
PB()

# ============================ 4. SIGN-OFF ============================
H1("4 &nbsp; Human sign-off &mdash; signoff.json")
BODY("A run is not &ldquo;done&rdquo; until a person accepts it. The Runs page has a small form "
     "(<font face='Courier'>decision</font> = acknowledged / accepted / rejected - remediation "
     "required, plus an optional comment). Submitting it writes:")
A(CODE('{ "reviewed_by", "reviewed_at", "decision", "comment" }'))
for x in BUL([
    "<b>reviewed_by</b> = the name in the top-bar &ldquo;editor&rdquo; field (the same identity "
    "stamped on every catalogue / source change).",
    "<b>reviewed_at</b> = server timestamp (ISO-8601 UTC).",
    "The run list then shows a <b>signed-off</b> badge; the run detail shows the decision and "
    "comment.",
]):
    A(x)
SMALL("Prototype scope: one free-text decision, no multi-party approval workflow or RBAC.")

# ============================ 5. CHANGE LOGS ============================
H1("5 &nbsp; Change logs &mdash; who changed what, when")
BODY("The audit trail is not only about runs. Every change to a <b>rule</b> or a <b>data "
     "source</b> is journalled in an append-only JSONL file, and each entry records the "
     "<b>SHA-256 of the whole file before and after</b> the change.")

A(TBL(["Log", "Written by", "Actions logged", "Per-entry fields"], [
    ["catalogue_changelog.jsonl", "rule_authoring/store.py :: _log()",
     "create, update, delete, activate, deactivate, retarget (source rename cascade)",
     "timestamp, user, action, rule_id, note, catalogue_hash_before, catalogue_hash_after, "
     "before (rule snapshot), after (rule snapshot)"],
    ["data_sources_changelog.jsonl", "rule_authoring/source_store.py :: _log()",
     "create, update, retire, reactivate, purge, rename",
     "timestamp, user, action, source, note, hash_before, hash_after, "
     "(+ affected rule ids on a cascade)"],
], [40 * mm, 40 * mm, 40 * mm, 48 * mm]))
SP(3)
for x in BUL([
    "<b>user</b> = the name typed in the top-bar &ldquo;editor&rdquo; field, stamped on every "
    "write (defaults to &ldquo;anonymous&rdquo;).",
    "Because before/after hashes are recorded, the state of the catalogue or the source "
    "registry at any past moment is reconstructible, and any edit made outside the app shows up "
    "as a file hash that no log entry explains.",
    "<b>before / after</b> rule snapshots make each change fully reversible by inspection.",
]):
    A(x)
PB()

# ============================ 6. AUDIT SURFACES ============================
H1("6 &nbsp; Audit surfaces in the web app")
A(TBL(["Route", "What it shows"], [
    ["/runs", "Every run from the ledger: run_id, timestamp, PASS/FAIL/ERROR counts, engine "
              "version, run_hash, a verified / mismatch badge (from verification.json) and a "
              "signed-off badge. Search + filter by result / verification / sign-off, and sort."],
    ["/runs/<run_id>", "The full Evidence Pack: the integrity block (run_hash, "
                       "previous_run_hash, catalogue hash, datasets_config hash, dataset "
                       "snapshots); per-rule results that expand to metrics, config snapshot, "
                       "resolved execution parameters and the exception rows (tested column "
                       "highlighted, plus a How-to-fix note); the Verify button + checks table; "
                       "the Sign-off form / record; the system trace; the processing-log tail. "
                       "Every evidence file is downloadable."],
    ["/activity", "One reverse-chronological timeline merging catalogue_changelog.jsonl and "
                  "data_sources_changelog.jsonl (filter: rules / sources)."],
    ["/mapping", "Appendix C supervisory mapping: per rule, the requirement -> control -> "
                 "evidence generated -> output, plus its last run id / status / run_hash. Ties "
                 "each control to the evidence this layer produces."],
], [30 * mm, 138 * mm]))

# ============================ 7. COMPLIANCE ============================
H1("7 &nbsp; Appendix B compliance")
A(TBL(["Requirement (Appendix B / section 4.4)", "Where satisfied", "Met"], [
    ["B.2-1 Run identification (id + timestamps)", "run_summary.json, every *_result.json", YES()],
    ["B.2-2 Dataset reference (content hash)", "_dataset_hash -> dataset_reference", YES()],
    ["B.2-3 Dataset snapshot", "snapshots/<name>.csv", YES()],
    ["B.2-4 Rule configuration snapshot", "*_result.json .rule_configuration_snapshot", YES()],
    ["B.2-5 Execution parameters (resolved)", "_resolve_execution_parameters", YES()],
    ["B.2-6 Control results (status + metrics)", "*_result.json", YES()],
    ["B.2-7 Exception dataset", "<rule>_exceptions.csv", YES()],
    ["B.2-8 Processing log + system trace", "run_log.jsonl, run.log, system_trace.json", YES()],
    ["B.2-9 Integrity / chaining", "run_hash = SHA-256(prev + canonical summary)", YES()],
    ["B.2-10 Sign-off", "signoff.json (Runs page)", YES()],
    ["B.3 Independent verification", "verify_run() -> verification.json ; dqcompass verify", YES()],
    ["Tamper-evidence over the run history", "append-only hash-chained runs_ledger.jsonl", YES()],
    ["Change accountability (rules + sources)", "two hash-chained JSONL change logs + user stamp", YES()],
], [78 * mm, 74 * mm, 14 * mm], ok_col=2))

# ============================ 8. WORKED EXAMPLE ============================
H1("8 &nbsp; Worked example (current demo, 3 runs)")
BODY("The ledger for the seeded demo (14 rules on finance_data + reference sets):")
A(CODE(
    "run_id    previous_run_hash   run_hash            counts               catalogue_hash\n"
    "f7647b20  (empty / 1st run)   9ff826b484d05bb7    8 PASS / 6 FAIL       68887c88a7fde846\n"
    "57ba0181  9ff826b484d05bb7    d16c1fac80b843cc    8 PASS / 4 FAIL       2a5c1de63d46cbe3\n"
    "0f13237e  d16c1fac80b843cc    b1c8ba33ffd68f60    8 PASS / 6 FAIL       256fdedd7d0b645d"))
for x in BUL([
    "Each <font face='Courier'>previous_run_hash</font> equals the prior line's "
    "<font face='Courier'>run_hash</font> - the chain is intact.",
    "The <font face='Courier'>catalogue_hash</font> changes across the three runs because two "
    "rules were toggled off then on again between them - visible config drift.",
    "Latest run <font face='Courier'>0f13237e</font> Evidence Pack: "
    "<font face='Courier'>run_summary.json</font>, <font face='Courier'>system_trace.json</font> "
    "(engine 1.0, Python 3.12.8, pandas 2.2.2), 6 dataset snapshots, 14 "
    "<font face='Courier'>*_result.json</font>, 8 <font face='Courier'>*_exceptions.csv</font>, "
    "<font face='Courier'>run_log.jsonl</font> + <font face='Courier'>run.log</font>.",
    "<font face='Courier'>verification.json</font>: <font face='Courier'>all_match = true</font>, "
    "14 / 14 checks - status and exception count reproduce exactly from the stored config and "
    "snapshots.",
]):
    A(x)


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 12 * mm, "DQ Compass - The Audit Layer")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
    title="DQ Compass - The Audit Layer", author="Working Group 1")
doc.addPageTemplates([PageTemplate(id="main",
                                   frames=[Frame(doc.leftMargin, doc.bottomMargin,
                                                 doc.width, doc.height, id="main")],
                                   onPage=_page)])
doc.build(story)
print(f"Wrote {OUT}")
