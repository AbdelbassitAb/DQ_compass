const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
p.author = "Group 1";
p.title = "DQ Compass - 5 min (EN)";

const RED = "9E1B32", INK = "1A1A1E", WHITE = "FFFFFF", PANEL = "F4F5F7",
      MUTED = "5B6270", NAVY = "2F3C7E", GREEN = "137A46", LINE = "D8DAE0";
const HEAD = "Cambria", BODY = "Calibri";
const MX = 0.62, CW = 13.333 - MX * 2;

function shadow() { return { type: "outer", color: "9A9A9A", blur: 9, offset: 3, angle: 90, opacity: 0.28 }; }
function notes(s, t) { s.addNotes(t); }
function titleBar(s, kicker, title, dark) {
  s.addText(kicker.toUpperCase(), { isTextBox: true, x: MX, y: 0.42, w: CW, h: 0.32, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: dark ? "C9A2AB" : RED, charSpacing: 2 });
  s.addText(title, { isTextBox: true, x: MX, y: 0.72, w: CW, h: 0.9, margin: 0,
    fontFace: HEAD, fontSize: 29, bold: true, color: dark ? WHITE : INK });
}
function footer(s, n, dark) {
  s.addText("DQ Compass  -  Group 1  -  MBA-ESG x SG GSC Datathon 2026", {
    isTextBox: true, x: MX, y: 7.06, w: 9.5, h: 0.3, margin: 0, fontFace: BODY, fontSize: 9,
    color: dark ? "8A8A93" : MUTED });
  s.addText(String(n), { isTextBox: true, x: 12.4, y: 7.06, w: 0.5, h: 0.3, margin: 0, align: "right",
    fontFace: BODY, fontSize: 9, color: dark ? "8A8A93" : MUTED });
}
function card(s, x, y, w, h, fill) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.09, fill: { color: fill || PANEL },
    line: { color: LINE, width: 0.75 }, shadow: shadow() });
}
function numCircle(s, x, y, n, d) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: RED } });
  s.addText(String(n), { isTextBox: true, x, y, w: d, h: d, margin: 0, align: "center", valign: "middle",
    fontFace: HEAD, fontSize: 15, bold: true, color: WHITE });
}
function bullets(s, items, x, y, w, h, sz) {
  s.addText(items.map((t) => ({ text: t, options: { bullet: { code: "2013", indent: 12 },
    breakLine: true, paraSpaceAfter: 10, fontFace: BODY, fontSize: sz || 13.5, color: INK } })),
    { isTextBox: true, x, y, w, h, margin: 0, valign: "top" });
}
function pill(s, x, y, w, h, txt, fill, tc, sz) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.05, fill: { color: fill },
    line: { color: LINE, width: 0.5 } });
  s.addText(txt, { isTextBox: true, x: x + 0.12, y, w: w - 0.24, h, margin: 0, valign: "middle",
    fontFace: BODY, fontSize: sz || 10, color: tc || INK });
}
function vHead(s, x, y, w, t) {
  s.addText(t, { isTextBox: true, x, y, w, h: 0.36, margin: 0, fontFace: HEAD, fontSize: 12.5,
    bold: true, color: RED });
}
function compSlide(n, kicker, title, items, visFn, page) {
  const s = p.addSlide(); s.background = { color: WHITE };
  s.addText(kicker.toUpperCase(), { isTextBox: true, x: MX, y: 0.42, w: CW, h: 0.32, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: RED, charSpacing: 2 });
  numCircle(s, MX, 0.78, n, 0.6);
  s.addText(title, { isTextBox: true, x: MX + 0.85, y: 0.74, w: CW - 0.85, h: 0.75, margin: 0,
    fontFace: HEAD, fontSize: 25, bold: true, color: INK });
  const lw = 6.7, rx = MX + lw + 0.5, rw = CW - lw - 0.5;
  bullets(s, items, MX, 2.15, lw, 4.3, 13.5);
  card(s, rx, 1.95, rw, 4.55);
  visFn(s, rx + 0.32, 2.2, rw - 0.64);
  footer(s, page);
  return s;
}


// ================= 2 - THE TEAM =================
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "1 - The team", "Group 1 - four roles, one method");
  const members = [
    ["Rules & meta-catalogue", "Rule schema and the ~30 validation checks."],
    ["Engine & tests", "The 6 generic controls and the 42 automated tests."],
    ["Web app & reporting", "The authoring interface and the reporting dashboard."],
    ["Governance & audit", "Evidence Pack, hash-chained ledger, supervisory mapping."]];
  s.addText("Who did what", { isTextBox: true, x: MX, y: 1.75, w: 6, h: 0.36, margin: 0,
    fontFace: HEAD, fontSize: 13.5, bold: true, color: RED });
  members.forEach((m, i) => {
    const y = 2.2 + i * 1.02;
    card(s, MX, y, 5.9, 0.86, PANEL);
    s.addText(m[0], { isTextBox: true, x: MX + 0.22, y: y + 0.08, w: 5.5, h: 0.34, margin: 0,
      fontFace: BODY, fontSize: 12, bold: true, color: INK });
    s.addText(m[1], { isTextBox: true, x: MX + 0.22, y: y + 0.42, w: 5.5, h: 0.4, margin: 0,
      fontFace: BODY, fontSize: 10, color: MUTED });
  });
  const cx = MX + 6.7, cw = CW - 6.7;
  card(s, cx, 1.75, cw, 4.6);
  s.addText("Our approach", { isTextBox: true, x: cx + 0.3, y: 1.95, w: cw - 0.6, h: 0.4, margin: 0,
    fontFace: HEAD, fontSize: 13.5, bold: true, color: RED });
  const steps = [
    "Understand the brief and the existing prototype; spot the gaps.",
    "Fix the architecture: rules are data, the engine is generic.",
    "Build brick by brick, testing each step before the next.",
    "Harden (42 tests) and document: brief compliance, supervisory mapping."];
  steps.forEach((t, i) => {
    const yy = 2.5 + i * 0.98;
    numCircle(s, cx + 0.3, yy, i + 1, 0.4);
    s.addText(t, { isTextBox: true, x: cx + 0.85, y: yy - 0.06, w: cw - 1.15, h: 0.9, margin: 0,
      fontFace: BODY, fontSize: 10.5, color: INK });
  });
  footer(s, 1);
  notes(s, "We split into four roles: rules, engine, interface, governance - a brief word from each of us. Our method: first understand the brief and the prototype, then lock the architecture - rules are data, the engine is generic - then build brick by brick with a test at every step, and finally harden with 42 tests and document compliance.");
})();

// ================= 3 - CONTEXT =================
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "2 - The context", "EUCs everywhere - but outside governance");
  const pains = [
    ["Critical processes living in files", "Excel, Access, scripts feed reportings, outside IT and its controls."],
    ["Ad hoc, untraced checks", "Every team verifies by hand, with no reusable proof from one run to the next."],
    ["The supervisor wants evidence", "BCBS 239 requires controls that are traceable, repeatable, auditable."]];
  pains.forEach((pn, i) => {
    const y = 1.9 + i * 1.12;
    numCircle(s, MX, y, i + 1, 0.44);
    s.addText(pn[0], { isTextBox: true, x: MX + 0.62, y: y - 0.04, w: 5.7, h: 0.34, margin: 0,
      fontFace: BODY, fontSize: 14, bold: true, color: INK });
    s.addText(pn[1], { isTextBox: true, x: MX + 0.62, y: y + 0.32, w: 5.7, h: 0.7, margin: 0,
      fontFace: BODY, fontSize: 11, color: MUTED });
  });
  const cx = MX + 6.7, cw = CW - 6.7;
  card(s, cx, 1.9, cw, 3.5);
  s.addText("What the brief asks for", { isTextBox: true, x: cx + 0.3, y: 2.1, w: cw - 0.6, h: 0.4,
    margin: 0, fontFace: HEAD, fontSize: 13.5, bold: true, color: RED });
  const st2 = ["Define", "Execute", "Report", "Prove"];
  st2.forEach((t, i) => {
    const sx = cx + 0.3 + i * 1.18;
    s.addShape(p.ShapeType.roundRect, { x: sx, y: 2.65, w: 1.13, h: 0.46, rectRadius: 0.06,
      fill: { color: i === 3 ? RED : NAVY } });
    s.addText(t, { isTextBox: true, x: sx, y: 2.65, w: 1.13, h: 0.46, margin: 0, align: "center",
      valign: "middle", fontFace: BODY, fontSize: 8.5, bold: true, color: WHITE });
  });
  bullets(s, ["6 quality dimensions.", "Frugal (AI optional), deterministic, reusable."],
    cx + 0.3, 3.4, cw - 0.6, 1.8, 11);
  footer(s, 2);
  notes(s, "The problem is one of governance: EUCs carry sensitive processes but escape controls, every team improvises its checks, and BCBS 239 demands evidence. The brief asks for a Define-Execute-Report-Prove cycle, 6 dimensions, frugal and deterministic.");
})();

// ================= 4 - SOLUTION OVERVIEW =================
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "3 - The solution", "You configure, you don't code");
  s.addText("Rules are data. Evidence is produced by default.", {
    isTextBox: true, x: MX, y: 1.6, w: CW, h: 0.4, margin: 0, fontFace: BODY, fontSize: 14,
    italic: true, color: NAVY });
  const blocks = [["Catalogue", "defines"], ["Engine", "executes"], ["Reporting", "reports"], ["Audit", "proves"]];
  const bw = 2.7, gap = 0.44, y0 = 2.55;
  blocks.forEach((b, i) => {
    const x = MX + i * (bw + gap);
    s.addShape(p.ShapeType.roundRect, { x, y: y0, w: bw, h: 1.7, rectRadius: 0.09,
      fill: { color: i === 3 ? RED : INK }, shadow: shadow() });
    s.addText(b[0], { isTextBox: true, x, y: y0 + 0.35, w: bw, h: 0.5, margin: 0, align: "center",
      fontFace: HEAD, fontSize: 17, bold: true, color: WHITE });
    s.addText(b[1], { isTextBox: true, x, y: y0 + 0.95, w: bw, h: 0.4, margin: 0, align: "center",
      fontFace: BODY, fontSize: 10.5, color: "D8D4D0" });
  });
  for (let i = 0; i < 3; i++) s.addText(">", { isTextBox: true, x: MX + i * (bw + gap) + bw, y: y0 + 0.5,
    w: gap, h: 0.7, margin: 0, align: "center", valign: "middle", fontFace: HEAD, fontSize: 22, bold: true, color: RED });
  card(s, MX, y0 + 2.2, CW, 1.05, PANEL);
  s.addText([{ text: "Connectors  ", options: { fontFace: BODY, fontSize: 12.5, bold: true, color: INK } },
    { text: "CSV - Excel live  |  JSON - SQL - SharePoint as selectors (phase 2)",
      options: { fontFace: BODY, fontSize: 12, color: MUTED } }],
    { isTextBox: true, x: MX + 0.35, y: y0 + 2.42, w: CW - 0.7, h: 0.4, margin: 0 });
  s.addText("A new EUC: 2 configuration files, no development.", {
    isTextBox: true, x: MX + 0.35, y: y0 + 2.85, w: CW - 0.7, h: 0.35, margin: 0, fontFace: BODY,
    fontSize: 11, italic: true, color: NAVY });
  footer(s, 3);
  notes(s, "The core idea: a rule is a line in a file, the engine is generic. Four blocks: the Catalogue defines, the Engine executes, Reporting reports, Audit proves. Adding an EUC is two config files.");
})();

// ================= 5 - CATALOGUE (CRUD) =================
compSlide(1, "3 - The solution", "The Catalogue - full CRUD on the rules", [
  "A rule = one line. The web app offers full CRUD: create, read, update, activate / deactivate, delete.",
  "A meta-catalogue (~30 checks) blocks any invalid rule before it is saved.",
  "14 attributes (Appendix A.2), 6 control types, severity, tolerance threshold, remediation action.",
  "Every operation is journalled (hash-chained log) - a deactivated rule stays traced, never lost."
], (s, x, y, w) => {
  vHead(s, x, y, w, "CRUD from the interface");
  const ops = ["Create a rule", "Read / search", "Update", "Activate / deactivate", "Delete (traced)"];
  ops.forEach((o, k) => pill(s, x, y + 0.5 + k * 0.62, w, 0.5, "  " + o, PANEL, INK, 10.5));
  s.addText("+ ~30-check validation before save", { isTextBox: true, x, y: y + 0.5 + 5 * 0.62 + 0.05,
    w, h: 0.4, margin: 0, fontFace: BODY, fontSize: 9.5, italic: true, color: MUTED });
}, 4);
notes(p.slides[p.slides.length - 1], "The Catalogue: a rule is a line in a file, and the web app gives full CRUD over it - create, read, update, activate or deactivate, delete. Before each save, a meta-catalogue of ~30 checks rejects an invalid rule. And everything is journalled in a hash-chained log.");

// ================= 6 - ENGINE =================
compSlide(2, "3 - The solution", "The Engine", [
  "One generic function per dimension: it only knows column names -- it runs on any dataset.",
  "Deterministic and repeatable: same input, same result.",
  "Resilient: a missing source becomes an ERROR status, execution continues.",
  "Tolerance thresholds: e.g. <= 1 % of rows in anomaly = compliant."
], (s, x, y, w) => {
  vHead(s, x, y, w, "6 generic functions");
  const d = ["Completeness", "Validity", "Uniqueness", "Consistency", "Timeliness", "Reconciliation"];
  const cw = (w - 0.16) / 2;
  d.forEach((n, k) => {
    const col = k % 2, row = Math.floor(k / 2);
    pill(s, x + col * (cw + 0.16), y + 0.55 + row * 0.82, cw, 0.64, n, PANEL, INK, 10.5);
  });
  s.addText("-> each one only receives column names", { isTextBox: true, x, y: y + 0.55 + 3 * 0.82 + 0.1,
    w, h: 0.4, margin: 0, fontFace: BODY, fontSize: 9.5, italic: true, color: MUTED });
}, 5);
notes(p.slides[p.slides.length - 1], "The Engine: a single generic function per dimension, which only receives column names, so it works on any dataset. Deterministic and repeatable. And resilient: if a source is missing, the rule turns ERROR and execution continues.");

// ================= 7 - REPORTING (business only) =================
compSlide(3, "3 - The solution", "The Reporting", [
  "A dashboard for the business - risk owners and data stewards.",
  "Severity-weighted composite DQ score, trend, dataset health, coverage matrix.",
  "Open incidents with their remediation action; exceptions by owner (accountability).",
  "Run selector (replay any past execution); 7 CSV / JSON exports, ready for Power BI."
], (s, x, y, w) => {
  vHead(s, x, y, w, "At a glance");
  const st = [["87 / 100", "Composite DQ score"], ["8 / 14", "controls passing"], ["4", "open critical incidents"]];
  st.forEach(([v, l], k) => {
    const yy = y + 0.5 + k * 1.2;
    s.addShape(p.ShapeType.roundRect, { x, y: yy, w, h: 1.04, rectRadius: 0.06, fill: { color: PANEL },
      line: { color: LINE, width: 0.5 } });
    s.addText(v, { isTextBox: true, x: x + 0.2, y: yy + 0.06, w: w - 0.4, h: 0.5, margin: 0,
      fontFace: HEAD, fontSize: 19, bold: true, color: RED });
    s.addText(l, { isTextBox: true, x: x + 0.2, y: yy + 0.58, w: w - 0.4, h: 0.36, margin: 0,
      fontFace: BODY, fontSize: 9.5, color: MUTED });
  });
}, 6);
notes(p.slides[p.slides.length - 1], "The Reporting is built for the business - risk owners and data stewards. It shows a severity-weighted composite DQ score, the trend, dataset health, a coverage matrix, and the open incidents with their remediation action, plus exceptions by owner so accountability is clear. A selector replays the dashboard on any past run, and there are 7 exports ready for Power BI.");

// ================= 8 - AUDIT =================
compSlide(4, "3 - The solution", "The Audit - auditability", [
  "One Evidence Pack per execution: the 10 components of Appendix B.2 (frozen data + hash, config, metrics, exceptions, logs, system trace, sign-off).",
  "Hash-chained run ledger: any tampering with a past run becomes visible.",
  "Independent Verify: replays the frozen config against the frozen data (Appendix B.3).",
  "Human sign-off + 2 hash-chained change logs: who changed what, when."
], (s, x, y, w) => {
  vHead(s, x, y, w, "Hash-chained history");
  const bw2 = (w - 2 * 0.3) / 3;
  [0, 1, 2].forEach((k) => {
    const bx = x + k * (bw2 + 0.3);
    s.addShape(p.ShapeType.roundRect, { x: bx, y: y + 0.65, w: bw2, h: 0.7, rectRadius: 0.05,
      fill: { color: k === 2 ? RED : INK } });
    s.addText("Run " + (k + 1), { isTextBox: true, x: bx, y: y + 0.65, w: bw2, h: 0.7, margin: 0,
      align: "center", valign: "middle", fontFace: BODY, fontSize: 10, bold: true, color: WHITE });
    if (k < 2) s.addText(">", { isTextBox: true, x: bx + bw2, y: y + 0.65, w: 0.3, h: 0.7, margin: 0,
      align: "center", valign: "middle", fontFace: HEAD, fontSize: 14, bold: true, color: MUTED });
  });
  s.addText("each run signs the previous one", { isTextBox: true, x, y: y + 1.45, w, h: 0.32, margin: 0,
    fontFace: BODY, fontSize: 9, italic: true, color: MUTED });
  pill(s, x, y + 1.95, w, 0.5, "  Verify - 14 / 14 controls reproduced identically", PANEL, GREEN, 10);
}, 7);
notes(p.slides[p.slides.length - 1], "The Audit is our strong point. Every execution produces a complete Evidence Pack - the 10 components of Appendix B.2. The run ledger is hash-chained, so any tampering shows up. The Verify command replays the frozen config against the frozen data and gets the same result. Plus the human sign-off and the change logs. We don't just detect, we prove.");

// ================= 9 - PERSPECTIVES =================
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  titleBar(s, "4 - Perspectives", "Scaling out and up - without a rewrite", true);
  const cw = (CW - 0.5) / 2;
  [["Scaling out - more EUCs",
    ["A new EUC = 2 config files + 1 call.", "A central, versioned catalogue, pulled by each EUC.",
     "The CLI drops into any CI pipeline (blocking gate)."]],
   ["Scaling up - more volume",
    ["The 6 functions have a fixed contract.", "Swap pandas for DuckDB or Spark SQL without touching the catalogue, the evidence or the app.",
     "Parallel execution, incremental runs."]]
  ].forEach((b, i) => {
    const x = MX + i * (cw + 0.5);
    s.addShape(p.ShapeType.roundRect, { x, y: 1.9, w: cw, h: 3.4, rectRadius: 0.09,
      fill: { color: "26262C" }, line: { color: "3A3A42", width: 0.75 } });
    s.addText(b[0], { isTextBox: true, x: x + 0.35, y: 2.12, w: cw - 0.7, h: 0.45, margin: 0,
      fontFace: HEAD, fontSize: 15, bold: true, color: "C9A2AB" });
    s.addText(b[1].map((t) => ({ text: t, options: { bullet: { code: "2013", indent: 12 },
      breakLine: true, paraSpaceAfter: 9, fontFace: BODY, fontSize: 11.5, color: "E7E5E2" } })),
      { isTextBox: true, x: x + 0.35, y: 2.65, w: cw - 0.7, h: 2.5, margin: 0, valign: "top" });
  });
  s.addShape(p.ShapeType.roundRect, { x: MX, y: 5.55, w: CW, h: 0.85, rectRadius: 0.08, fill: { color: RED } });
  s.addText("An honest MVP: 3 connectors to finish, in-memory execution, local evidence - but the governance lifecycle itself is complete and proven.", {
    isTextBox: true, x: MX + 0.35, y: 5.55, w: CW - 0.7, h: 0.85, margin: 0, valign: "middle",
    fontFace: BODY, fontSize: 12, bold: true, color: WHITE });
  footer(s, 8, true);
  notes(s, "Perspectives. Scaling out is already configuration: one more EUC is two files. Scaling up: the fixed function contract lets us move to DuckDB or Spark without touching the rest. It's an MVP - three connectors to finish, in-memory execution - but the governance lifecycle is complete and proven.");
})();


p.writeFile({ fileName: "C:/Users/Basset/Downloads/DQ_Compass_Presentation_5min_EN.pptx" })
  .then(f => console.log("wrote", f));
