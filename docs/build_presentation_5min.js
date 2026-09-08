const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
p.author = "Groupe 1";
p.title = "DQ Compass - 5 min";

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
  s.addText("DQ Compass  -  Groupe 1  -  Datathon MBA-ESG x SG GSC 2026", {
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
// standard "component" slide: bullets left, visual card right
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

// ================= 1 - TITLE =================
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  s.addText("DQ Compass", { isTextBox: true, x: MX, y: 2.4, w: CW, h: 1.2, margin: 0,
    fontFace: HEAD, fontSize: 56, bold: true, color: WHITE });
  s.addText("Une couche de controle Data Quality plug-and-play pour les EUC", {
    isTextBox: true, x: MX, y: 3.62, w: 11, h: 0.6, margin: 0, fontFace: BODY, fontSize: 19, color: "D8D4D0" });
  s.addText("Groupe 1   -   Datathon MBA-ESG x SG GSC 2026   -   5 min + demo", {
    isTextBox: true, x: MX, y: 4.5, w: 11, h: 0.4, margin: 0, fontFace: BODY, fontSize: 12, color: "8A8A93" });
  notes(s, "DQ Compass, Groupe 1. En 5 minutes : qui on est et comment on a travaille, le contexte, la solution en 4 briques - Catalogue, Moteur, Reporting, Audit - et les perspectives. Puis 5 minutes de demo.");
})();

// ================= 2 - EQUIPE & DEMARCHE =================
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "1 - L'equipe & notre demarche", "Groupe 1 - quatre poles, une methode");
  const poles = ["Regles & meta-catalogue", "Moteur d'execution & tests",
    "Interface web & reporting", "Gouvernance & audit"];
  s.addText("Repartition du travail", { isTextBox: true, x: MX, y: 1.75, w: 6, h: 0.36, margin: 0,
    fontFace: HEAD, fontSize: 13.5, bold: true, color: RED });
  poles.forEach((t, i) => pill(s, MX, 2.2 + i * 0.82, 5.9, 0.62, "  " + t, PANEL, INK, 11.5));
  const cx = MX + 6.7, cw = CW - 6.7;
  card(s, cx, 1.75, cw, 4.6);
  s.addText("Notre demarche", { isTextBox: true, x: cx + 0.3, y: 1.95, w: cw - 0.6, h: 0.4, margin: 0,
    fontFace: HEAD, fontSize: 13.5, bold: true, color: RED });
  const steps = [
    "Comprendre le brief et le prototype existant, identifier les manques.",
    "Concevoir l'architecture : les regles sont des donnees, le moteur est generique.",
    "Construire brique par brique, en testant chaque etape avant la suivante.",
    "Durcir (42 tests) et documenter : conformite au brief, mapping superviseur."];
  steps.forEach((t, i) => {
    const yy = 2.5 + i * 0.98;
    numCircle(s, cx + 0.3, yy, i + 1, 0.4);
    s.addText(t, { isTextBox: true, x: cx + 0.85, y: yy - 0.06, w: cw - 1.15, h: 0.9, margin: 0,
      fontFace: BODY, fontSize: 10.5, color: INK });
  });
  footer(s, 2);
  notes(s, "On s'est reparti en quatre poles : regles, moteur, interface, gouvernance. Notre demarche : d'abord comprendre le brief et le prototype, puis fixer l'architecture - regles = donnees, moteur generique - puis construire brique par brique en testant a chaque etape, et enfin durcir avec 42 tests et documenter la conformite.");
})();

// ================= 3 - CONTEXTE =================
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "2 - Le contexte", "Des EUC partout - mais hors de la gouvernance");
  const pains = [
    ["Processus critiques dans des fichiers", "Excel, Access, scripts alimentent des reportings, hors du SI et de ses controles."],
    ["Controles ad hoc, non traces", "Chaque equipe verifie a la main, sans preuve exploitable d'une fois sur l'autre."],
    ["Le regulateur veut des preuves", "BCBS 239 exige des controles traces, reproductibles, auditables."]];
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
  s.addText("La cible fixee par le brief", { isTextBox: true, x: cx + 0.3, y: 2.1, w: cw - 0.6, h: 0.4,
    margin: 0, fontFace: HEAD, fontSize: 13.5, bold: true, color: RED });
  const st2 = ["Definir", "Executer", "Restituer", "Prouver"];
  st2.forEach((t, i) => {
    const sx = cx + 0.3 + i * 1.18;
    s.addShape(p.ShapeType.roundRect, { x: sx, y: 2.65, w: 1.13, h: 0.46, rectRadius: 0.06,
      fill: { color: i === 3 ? RED : NAVY } });
    s.addText(t, { isTextBox: true, x: sx, y: 2.65, w: 1.13, h: 0.46, margin: 0, align: "center",
      valign: "middle", fontFace: BODY, fontSize: 8.5, bold: true, color: WHITE });
  });
  bullets(s, ["6 dimensions de qualite.", "Frugal (IA optionnelle), deterministe, reutilisable."],
    cx + 0.3, 3.4, cw - 0.6, 1.8, 11);
  footer(s, 3);
  notes(s, "Le probleme est de gouvernance : les EUC portent des process sensibles mais echappent aux controles, chaque equipe bricole ses verifications, et BCBS 239 exige des preuves. Le brief demande un cycle Definir-Executer-Restituer-Prouver, 6 dimensions, frugal et deterministe.");
})();

// ================= 4 - SOLUTION VUE D'ENSEMBLE =================
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "3 - La solution", "On configure, on ne code pas");
  s.addText("Les regles sont des donnees. La preuve est produite par defaut.", {
    isTextBox: true, x: MX, y: 1.6, w: CW, h: 0.4, margin: 0, fontFace: BODY, fontSize: 14,
    italic: true, color: NAVY });
  const blocks = [["Catalogue", "definit"], ["Moteur", "execute"], ["Reporting", "restitue"], ["Audit", "prouve"]];
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
  s.addText([{ text: "Connecteurs  ", options: { fontFace: BODY, fontSize: 12.5, bold: true, color: INK } },
    { text: "CSV - Excel operationnels  |  JSON - SQL - SharePoint en selecteurs (phase 2)",
      options: { fontFace: BODY, fontSize: 12, color: MUTED } }],
    { isTextBox: true, x: MX + 0.35, y: y0 + 2.42, w: CW - 0.7, h: 0.4, margin: 0 });
  s.addText("Un nouvel EUC : 2 fichiers de configuration, aucun developpement.", {
    isTextBox: true, x: MX + 0.35, y: y0 + 2.85, w: CW - 0.7, h: 0.35, margin: 0, fontFace: BODY,
    fontSize: 11, italic: true, color: NAVY });
  footer(s, 4);
  notes(s, "L'idee centrale : une regle est une ligne de fichier, le moteur est generique. Quatre briques : le Catalogue definit, le Moteur execute, le Reporting restitue, l'Audit prouve. Ajouter un EUC, c'est deux fichiers de config.");
})();

// ================= 5 - CATALOGUE (CRUD) =================
compSlide(1, "3 - La solution", "Le Catalogue - CRUD complet des regles", [
  "Une regle = une ligne. L'application web offre un CRUD complet : creer, consulter, modifier, activer / desactiver, supprimer.",
  "Un meta-catalogue (~30 verifications) bloque toute regle invalide avant enregistrement.",
  "14 attributs (Annexe A.2), 6 types de controle, severite, seuil de tolerance, action corrective.",
  "Chaque operation est journalisee (journal chaine par hash) - une regle desactivee reste tracee, jamais perdue."
], (s, x, y, w) => {
  vHead(s, x, y, w, "CRUD depuis l'interface");
  const ops = ["Creer une regle", "Consulter / rechercher", "Modifier", "Activer / desactiver", "Supprimer (trace)"];
  ops.forEach((o, k) => pill(s, x, y + 0.5 + k * 0.62, w, 0.5, "  " + o, PANEL, INK, 10.5));
  s.addText("+ validation ~30 controles avant enregistrement", { isTextBox: true, x, y: y + 0.5 + 5 * 0.62 + 0.05,
    w, h: 0.4, margin: 0, fontFace: BODY, fontSize: 9.5, italic: true, color: MUTED });
}, 5);
notes(p.slides[p.slides.length - 1], "Le Catalogue : une regle est une ligne de fichier, et l'appli web permet un CRUD complet dessus - creer, consulter, modifier, activer ou desactiver, supprimer. Avant chaque enregistrement, un meta-catalogue de ~30 verifications refuse une regle invalide. Et tout est journalise dans un log chaine par hash.");

// ================= 6 - MOTEUR =================
compSlide(2, "3 - La solution", "Le Moteur d'execution", [
  "Une fonction generique par dimension : elle ne connait que des noms de colonnes -- elle tourne sur n'importe quel dataset.",
  "Deterministe et reproductible : meme entree, meme resultat.",
  "Resilient : une source manquante devient un statut ERROR, l'execution continue.",
  "Seuils de tolerance : ex. <= 1 % de lignes en anomalie = conforme."
], (s, x, y, w) => {
  vHead(s, x, y, w, "6 fonctions generiques");
  const d = ["Completude", "Validite", "Unicite", "Coherence", "Fraicheur", "Rapprochement"];
  const cw = (w - 0.16) / 2;
  d.forEach((n, k) => {
    const col = k % 2, row = Math.floor(k / 2);
    pill(s, x + col * (cw + 0.16), y + 0.55 + row * 0.82, cw, 0.64, n, PANEL, INK, 10.5);
  });
  s.addText("-> chacune ne recoit que des noms de colonnes", { isTextBox: true, x, y: y + 0.55 + 3 * 0.82 + 0.1,
    w, h: 0.4, margin: 0, fontFace: BODY, fontSize: 9.5, italic: true, color: MUTED });
}, 6);
notes(p.slides[p.slides.length - 1], "Le Moteur : une seule fonction generique par dimension, qui ne recoit que des noms de colonnes, donc elle marche sur n'importe quel dataset. Deterministe et reproductible. Et resilient : si une source manque, la regle passe en ERROR et l'execution continue.");

// ================= 7 - REPORTING =================
compSlide(3, "3 - La solution", "Le Reporting", [
  "Deux publics via un filtre d'audience : le metier (risk / data owner) et le data engineer.",
  "Score DQ composite pondere par severite, tendance, sante par dataset, matrice de couverture.",
  "Incidents ouverts + action corrective ; exceptions par proprietaire et par dimension ; fiabilite des regles.",
  "Selecteur d'execution ; 7 exports CSV / JSON prets pour Power BI."
], (s, x, y, w) => {
  vHead(s, x, y, w, "En un coup d'oeil");
  const st = [["87 / 100", "Score DQ composite"], ["8 / 14", "controles conformes"], ["4", "incidents critiques ouverts"]];
  st.forEach(([v, l], k) => {
    const yy = y + 0.5 + k * 1.2;
    s.addShape(p.ShapeType.roundRect, { x, y: yy, w, h: 1.04, rectRadius: 0.06, fill: { color: PANEL },
      line: { color: LINE, width: 0.5 } });
    s.addText(v, { isTextBox: true, x: x + 0.2, y: yy + 0.06, w: w - 0.4, h: 0.5, margin: 0,
      fontFace: HEAD, fontSize: 19, bold: true, color: RED });
    s.addText(l, { isTextBox: true, x: x + 0.2, y: yy + 0.58, w: w - 0.4, h: 0.36, margin: 0,
      fontFace: BODY, fontSize: 9.5, color: MUTED });
  });
}, 7);
notes(p.slides[p.slides.length - 1], "Le Reporting : un tableau de bord pour deux publics - le metier et le data engineer - avec un score DQ composite pondere par severite, la tendance, les incidents ouverts avec leur action corrective, et les exceptions par proprietaire. Un selecteur permet de rejouer le tableau sur n'importe quel run passe. Et 7 exports prets pour Power BI.");

// ================= 8 - AUDIT =================
compSlide(4, "3 - La solution", "L'Audit - l'auditabilite", [
  "Un Evidence Pack par execution : les 10 composants de l'Annexe B.2 (donnees figees + hash, config, metriques, exceptions, journaux, trace systeme, sign-off).",
  "Registre des executions chaine par hash : toute alteration d'un run passe devient visible.",
  "Verification independante Verify : rejoue la config figee sur les donnees figees (Annexe B.3).",
  "Sign-off humain + 2 journaux de changements chaines : qui a change quoi, quand."
], (s, x, y, w) => {
  vHead(s, x, y, w, "Historique chaine par hash");
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
  s.addText("chaque run signe le precedent", { isTextBox: true, x, y: y + 1.45, w, h: 0.32, margin: 0,
    fontFace: BODY, fontSize: 9, italic: true, color: MUTED });
  pill(s, x, y + 1.95, w, 0.5, "  Verify - 14 / 14 controles reproduits a l'identique", PANEL, GREEN, 10);
}, 8);
notes(p.slides[p.slides.length - 1], "L'Audit, c'est notre point fort. Chaque execution produit un Evidence Pack complet : les 10 composants de l'annexe B.2. Le registre des runs est chaine par hash - toute alteration devient visible. La commande Verify rejoue la config figee sur les donnees figees et retrouve le meme resultat. Plus le sign-off humain et les journaux de changements. On ne fait pas que detecter, on prouve.");

// ================= 9 - PERSPECTIVES =================
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  titleBar(s, "4 - Perspectives", "Passer a l'echelle - sans rien reecrire", true);
  const cw = (CW - 0.5) / 2;
  [["A l'horizontale - plus d'EUC",
    ["Un nouvel EUC = 2 fichiers de config + 1 appel.", "Catalogue central versionne, tire par chaque EUC.",
     "La CLI s'insere dans la CI (controle bloquant)."]],
   ["A la verticale - plus de volume",
    ["Les 6 fonctions ont un contrat fixe.", "On remplace pandas par DuckDB ou Spark SQL sans toucher au catalogue, a la preuve, ni a l'appli.",
     "Execution parallele, runs incrementaux."]]
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
  s.addText("MVP honnete : 3 connecteurs a finir, execution en memoire, preuve locale - le cycle de gouvernance, lui, est complet et prouve.", {
    isTextBox: true, x: MX + 0.35, y: 5.55, w: CW - 0.7, h: 0.85, margin: 0, valign: "middle",
    fontFace: BODY, fontSize: 12, bold: true, color: WHITE });
  footer(s, 9, true);
  notes(s, "Perspectives. A l'horizontale c'est deja de la config : un EUC de plus, deux fichiers. A la verticale, le contrat de fonction fixe permet de passer a DuckDB ou Spark sans toucher au reste. C'est un MVP - trois connecteurs a finir, execution en memoire - mais le cycle de gouvernance est complet et prouve.");
})();

// ================= 10 - DEMO =================
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  s.addText("Place a la demonstration", { isTextBox: true, x: MX, y: 1.5, w: CW, h: 1.0, margin: 0,
    fontFace: HEAD, fontSize: 34, bold: true, color: WHITE });
  const steps = [
    "Le Catalogue - creer et valider une regle (le meta-catalogue refuse une regle invalide).",
    "Lancer une execution - le moteur applique tout le catalogue au dataset.",
    "Le Reporting - ouvrir un incident : les lignes fautives et l'action corrective.",
    "Un Evidence Pack - cliquer Verify : le run se rejoue a l'identique.",
    "Le Mapping - chaque controle relie a une exigence BCBS 239 et au hash du run."];
  steps.forEach((t, i) => {
    numCircle(s, MX, 2.8 + i * 0.82, i + 1, 0.44);
    s.addText(t, { isTextBox: true, x: MX + 0.62, y: 2.8 + i * 0.82 + 0.02, w: CW - 0.62, h: 0.6, margin: 0,
      fontFace: BODY, fontSize: 13, color: "E7E5E2" });
  });
  footer(s, 10, true);
  notes(s, "Passons a la demo, en cinq etapes : creer une regle dans le catalogue, lancer un run, ouvrir un incident dans le reporting avec les lignes fautives, ouvrir un Evidence Pack et cliquer Verify, et enfin le mapping superviseur.");
})();

p.writeFile({ fileName: "C:/Users/Basset/Downloads/dq_compass/dq_compass/docs/DQ_Compass_Presentation_5min.pptx" })
  .then(f => console.log("wrote", f));
