const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
p.author = "Groupe 1";
p.title = "DQ Compass";

// ---- palette ----
const RED = "9E1B32", INK = "1A1A1E", WHITE = "FFFFFF", PANEL = "F4F5F7",
      MUTED = "5B6270", NAVY = "2F3C7E", GREEN = "137A46", LINE = "D8DAE0",
      LIGHTINK = "E7E5E2";
const HEAD = "Cambria", BODY = "Calibri";
const MX = 0.62; // slide margin
const CW = 13.333 - MX * 2;

function shadow() {
  return { type: "outer", color: "9A9A9A", blur: 9, offset: 3, angle: 90, opacity: 0.28 };
}
function notes(s, t) { s.addNotes(t); }

function titleBar(s, kicker, title, dark) {
  const tc = dark ? WHITE : INK;
  const kc = dark ? "C9A2AB" : RED;
  if (kicker) s.addText(kicker.toUpperCase(), {
    isTextBox: true, x: MX, y: 0.42, w: CW, h: 0.32, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: kc, charSpacing: 2
  });
  s.addText(title, {
    isTextBox: true, x: MX, y: 0.72, w: CW, h: 0.95, margin: 0,
    fontFace: HEAD, fontSize: 30, bold: true, color: tc
  });
}
function footer(s, n, dark) {
  s.addText("DQ Compass  —  Groupe 1  ·  Datathon MBA-ESG × SG GSC 2026", {
    isTextBox: true, x: MX, y: 7.06, w: 9.5, h: 0.3, margin: 0,
    fontFace: BODY, fontSize: 9, color: dark ? "8A8A93" : MUTED
  });
  s.addText(String(n), {
    isTextBox: true, x: 12.4, y: 7.06, w: 0.5, h: 0.3, margin: 0, align: "right",
    fontFace: BODY, fontSize: 9, color: dark ? "8A8A93" : MUTED
  });
}
function card(s, x, y, w, h, fill) {
  s.addShape(p.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.09, fill: { color: fill || PANEL },
    line: { color: LINE, width: 0.75 }, shadow: shadow()
  });
}
function numCircle(s, x, y, n, d) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: RED } });
  s.addText(String(n), {
    isTextBox: true, x, y, w: d, h: d, margin: 0, align: "center", valign: "middle",
    fontFace: HEAD, fontSize: 15, bold: true, color: WHITE
  });
}
function bullets(s, items, x, y, w, h, sz) {
  s.addText(items.map((t, i) => ({
    text: t, options: { bullet: { code: "2013", indent: 12 }, breakLine: true,
      paraSpaceAfter: 9, fontFace: BODY, fontSize: sz || 14, color: INK }
  })), { isTextBox: true, x, y, w, h, margin: 0, valign: "top" });
}

// ============================================================ 1 — TITLE
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  s.addText("DQ Compass", {
    isTextBox: true, x: MX, y: 2.35, w: CW, h: 1.2, margin: 0,
    fontFace: HEAD, fontSize: 58, bold: true, color: WHITE
  });
  s.addText("Une couche de contrôle Data Quality plug-and-play pour les EUC", {
    isTextBox: true, x: MX, y: 3.62, w: 10.5, h: 0.6, margin: 0,
    fontFace: BODY, fontSize: 20, color: "D8D4D0"
  });
  s.addText("Groupe 1   ·   Use case : « Building a Plug-and-Play Data Quality Control Layer for EUCs »", {
    isTextBox: true, x: MX, y: 4.5, w: 11, h: 0.4, margin: 0,
    fontFace: BODY, fontSize: 12.5, color: "8A8A93"
  });
  const labels = ["Complétude", "Validité", "Unicité", "Cohérence", "Fraîcheur", "Rapprochement"];
  labels.forEach((L, i) => {
    s.addShape(p.ShapeType.ellipse, { x: MX + i * 0.42, y: 5.55, w: 0.12, h: 0.12, fill: { color: RED } });
  });
  s.addText("6 dimensions DQ  ·  Définir → Exécuter → Restituer → Prouver", {
    isTextBox: true, x: MX, y: 5.78, w: 10, h: 0.34, margin: 0,
    fontFace: BODY, fontSize: 11, color: "8A8A93"
  });
  notes(s, "DQ Compass, par le Groupe 1. Le problème des EUC : des fichiers qui portent des processus critiques mais restent hors de toute gouvernance. Notre solution : une couche de contrôle qui se branche sur n'importe quel EUC sans écrire de code, et qui produit la preuve par défaut. Plan : la problématique, la solution partie par partie, un cas d'usage complet, la conformité au brief, puis les perspectives.");
})();

// ============================================================ 2 — PROBLÉMATIQUE
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "1 · La problématique", "Les EUC : partout dans les processus, invisibles pour la gouvernance");
  const pains = [
    ["Des processus critiques dans des fichiers", "Excel, Access, scripts : ils calculent, réconcilient, alimentent des reportings — mais vivent hors du SI et de ses contrôles."],
    ["Chaque équipe réinvente ses contrôles", "Vérifications faites à la main, non standardisées, sans trace exploitable d'une fois sur l'autre."],
    ["Le régulateur veut des preuves", "BCBS 239 exige des contrôles tracés, reproductibles et auditables. Un classeur Excel ne sait pas le démontrer."]
  ];
  pains.forEach((pn, i) => {
    const y = 1.9 + i * 1.12;
    numCircle(s, MX, y, i + 1, 0.44);
    s.addText(pn[0], { isTextBox: true, x: MX + 0.62, y: y - 0.04, w: 5.6, h: 0.34, margin: 0,
      fontFace: BODY, fontSize: 14, bold: true, color: INK });
    s.addText(pn[1], { isTextBox: true, x: MX + 0.62, y: y + 0.32, w: 5.6, h: 0.72, margin: 0,
      fontFace: BODY, fontSize: 11, color: MUTED });
  });
  const cx = MX + 6.7, cw = CW - 6.7;
  card(s, cx, 1.8, cw, 4.4);
  s.addText("Ce que « bien » veut dire", { isTextBox: true, x: cx + 0.3, y: 2.0, w: cw - 0.6, h: 0.4, margin: 0,
    fontFace: HEAD, fontSize: 15, bold: true, color: RED });
  const steps = ["Définir", "Exécuter", "Restituer", "Prouver"];
  steps.forEach((st, i) => {
    const sx = cx + 0.3 + i * 1.18;
    s.addShape(p.ShapeType.roundRect, { x: sx, y: 2.55, w: 1.13, h: 0.46, rectRadius: 0.06,
      fill: { color: i === 3 ? RED : NAVY } });
    s.addText(st, { isTextBox: true, x: sx, y: 2.55, w: 1.13, h: 0.46, margin: 0,
      align: "center", valign: "middle", fontFace: BODY, fontSize: 8.5, bold: true, color: WHITE });
  });
  bullets(s, [
    "6 dimensions : complétude, validité, unicité, cohérence, fraîcheur, rapprochement.",
    "Frugal (IA optionnelle), déterministe, reproductible.",
    "Réutilisable : les mêmes contrôles pour tout dataset."
  ], cx + 0.3, 3.35, cw - 0.6, 2.75, 11);
  footer(s, 2);
  notes(s, "Le problème n'est pas technique, il est de gouvernance. Les EUC portent des processus sensibles mais échappent aux contrôles du SI. Le brief définit la cible : un cycle Définir – Exécuter – Restituer – Prouver, sur 6 dimensions de qualité, de façon frugale, déterministe et réutilisable.");
})();

// ============================================================ 3 — RÉPONSE + ARCHITECTURE
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "2 · La solution", "Notre réponse : on configure, on ne code pas");
  s.addText("Les règles sont des données. La preuve est produite par défaut.", {
    isTextBox: true, x: MX, y: 1.6, w: CW, h: 0.4, margin: 0,
    fontFace: BODY, fontSize: 14, italic: true, color: NAVY });
  const blocks = [
    ["Catalogue", "définit les règles"],
    ["Moteur", "exécute sur les données"],
    ["Reporting", "restitue l'état"],
    ["Audit", "produit la preuve"]
  ];
  const bw = 2.7, gap = 0.44, y0 = 2.5;
  blocks.forEach((b, i) => {
    const x = MX + i * (bw + gap);
    s.addShape(p.ShapeType.roundRect, { x, y: y0, w: bw, h: 1.7, rectRadius: 0.09,
      fill: { color: i === 3 ? RED : INK }, shadow: shadow() });
    s.addText(b[0], { isTextBox: true, x, y: y0 + 0.32, w: bw, h: 0.5, margin: 0, align: "center",
      fontFace: HEAD, fontSize: 17, bold: true, color: WHITE });
    s.addText(b[1], { isTextBox: true, x, y: y0 + 0.9, w: bw, h: 0.5, margin: 0, align: "center",
      fontFace: BODY, fontSize: 10.5, color: "D8D4D0" });
  });
  for (let i = 0; i < 3; i++) {
    s.addText("›", { isTextBox: true, x: MX + i * (bw + gap) + bw, y: y0 + 0.45, w: gap, h: 0.8,
      margin: 0, align: "center", valign: "middle", fontFace: HEAD, fontSize: 24, bold: true, color: RED });
  }
  card(s, MX, y0 + 2.15, CW, 1.15, PANEL);
  s.addText([
    { text: "Connecteurs   ", options: { fontFace: BODY, fontSize: 12.5, bold: true, color: INK } },
    { text: "CSV · Excel opérationnels    ·    JSON · SQL · SharePoint prêts en sélecteurs (phase 2)",
      options: { fontFace: BODY, fontSize: 12, color: MUTED } }
  ], { isTextBox: true, x: MX + 0.35, y: y0 + 2.4, w: CW - 0.7, h: 0.4, margin: 0 });
  s.addText("Un nouvel EUC : 2 fichiers de configuration, aucun développement.", {
    isTextBox: true, x: MX + 0.35, y: y0 + 2.85, w: CW - 0.7, h: 0.35, margin: 0,
    fontFace: BODY, fontSize: 11, italic: true, color: NAVY });
  footer(s, 3);
  notes(s, "L'idée centrale : une règle est une ligne de fichier, le moteur est générique. On ne développe pas un contrôle, on le configure. Quatre briques : le Catalogue définit, le Moteur exécute, le Reporting restitue, l'Audit prouve. Les connecteurs alimentent le moteur : CSV et Excel sont opérationnels, les autres sont câblés en sélecteurs.");
})();

// ============================================================ 4..9 — COMPONENTS
const COMP = [
  ["Le Catalogue de contrôles", [
    "Une règle = une ligne de fichier. Une application web pour les créer, les modifier, les versionner.",
    "Un méta-catalogue (~30 vérifications) bloque toute règle invalide avant enregistrement.",
    "6 types de contrôle, sévérité, propriétaire, seuil de tolérance, action corrective.",
    "Définition en SQL lisible par un auditeur, générée automatiquement."
  ]],
  ["Le Moteur d'exécution", [
    "Une fonction générique par dimension : elle ne connaît que des noms de colonnes.",
    "Tourne sur n'importe quel dataset, sans jamais y toucher.",
    "Déterministe et reproductible : même entrée → même résultat.",
    "Ne plante jamais : une source manquante devient un statut ERROR, l'exécution continue."
  ]],
  ["Sources de données — plug & play", [
    "Abstraction connecteur : CSV et Excel opérationnels ; JSON / SQL / SharePoint prêts en sélecteurs (phase 2).",
    "Ajouter une source = une ligne de configuration.",
    "Politique de suppression maîtrisée : retrait réversible (cascade sur les règles), purge, renommage (réaffecte les règles dépendantes)."
  ]],
  ["Le Reporting", [
    "Un tableau de bord pour le métier et pour la data : score DQ composite pondéré par sévérité, tendance, santé par dataset, matrice de couverture.",
    "Incidents ouverts + action corrective ; exceptions par propriétaire et par dimension ; fiabilité des règles dans le temps.",
    "Sélecteur d'exécution ; 7 exports CSV / JSON prêts pour Power BI."
  ]],
  ["L'Audit — l'auditabilité", [
    "Un Evidence Pack par exécution : les 10 composants de l'Annexe B.2 (données figées, config, métriques, exceptions, journaux, trace système…).",
    "Registre des exécutions chaîné par hash : toute altération d'un run passé devient visible.",
    "Vérification indépendante « Verify » : rejoue la configuration figée sur les données figées.",
    "Sign-off humain + 2 journaux de changements chaînés : qui a changé quoi, quand."
  ]],
  ["Le Mapping superviseur", [
    "Généré depuis le catalogue — jamais désynchronisé.",
    "Chaque contrôle → l'exigence BCBS 239 couverte → la preuve produite → le hash du run qui l'atteste.",
    "Répond à l'Annexe C (C.2 exigence→contrôle→preuve, C.3 traçabilité, C.4 principes)."
  ]]
];
function pill(s, x, y, w, h, txt, fill, tc, sz) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.05,
    fill: { color: fill }, line: { color: LINE, width: 0.5 } });
  s.addText(txt, { isTextBox: true, x: x + 0.1, y, w: w - 0.2, h, margin: 0, valign: "middle",
    fontFace: BODY, fontSize: sz || 9.5, color: tc || INK });
}
function vHead(s, x, y, w, t) {
  s.addText(t, { isTextBox: true, x, y, w, h: 0.36, margin: 0,
    fontFace: HEAD, fontSize: 12.5, bold: true, color: RED });
}
const visBuilders = [
  (s, x, y, w) => { // Catalogue
    vHead(s, x, y, w, "Une règle = quelques champs");
    const rows = ["RULE-07", "Type : Validité", "Champ : commandes.statut",
      "Sévérité : High", "Seuil de tolérance : 1 %", "Action : prévenir le propriétaire"];
    rows.forEach((r, k) => pill(s, x, y + 0.5 + k * 0.54, w, 0.44, r,
      k === 0 ? INK : PANEL, k === 0 ? WHITE : INK, k === 0 ? 10 : 9.5));
  },
  (s, x, y, w) => { // Moteur
    vHead(s, x, y, w, "6 fonctions génériques");
    const d = ["Complétude", "Validité", "Unicité", "Cohérence", "Fraîcheur", "Rapprochement"];
    const cw = (w - 0.16) / 2;
    d.forEach((n, k) => {
      const col = k % 2, row = Math.floor(k / 2);
      pill(s, x + col * (cw + 0.16), y + 0.55 + row * 0.78, cw, 0.62, n, PANEL, INK, 10.5);
    });
    s.addText("→ chacune ne reçoit que des noms de colonnes", {
      isTextBox: true, x, y: y + 0.55 + 3 * 0.78 + 0.1, w, h: 0.4, margin: 0,
      fontFace: BODY, fontSize: 9.5, italic: true, color: MUTED });
  },
  (s, x, y, w) => { // Sources
    vHead(s, x, y, w, "5 types de source");
    const srcs = [["CSV", true], ["Excel", true], ["JSON", false], ["SQL (base de données)", false], ["SharePoint / Drive", false]];
    srcs.forEach(([n, live], k) => {
      const yy = y + 0.55 + k * 0.62;
      s.addShape(p.ShapeType.ellipse, { x, y: yy + 0.06, w: 0.22, h: 0.22,
        fill: { color: live ? GREEN : WHITE }, line: { color: live ? GREEN : "9AA0AC", width: 1 } });
      s.addText(n, { isTextBox: true, x: x + 0.36, y: yy, w: w - 1.4, h: 0.34, margin: 0,
        fontFace: BODY, fontSize: 11, color: INK });
      s.addText(live ? "opérationnel" : "phase 2", { isTextBox: true, x: x + w - 1.05, y: yy, w: 1.05, h: 0.34,
        margin: 0, align: "right", fontFace: BODY, fontSize: 9, color: live ? GREEN : MUTED });
    });
  },
  (s, x, y, w) => { // Reporting
    vHead(s, x, y, w, "En un coup d'œil");
    const st = [["87 / 100", "Score DQ composite"], ["8 / 14", "contrôles conformes"], ["4", "incidents critiques ouverts"]];
    st.forEach(([v, l], k) => {
      const yy = y + 0.5 + k * 1.18;
      s.addShape(p.ShapeType.roundRect, { x, y: yy, w, h: 1.02, rectRadius: 0.06,
        fill: { color: PANEL }, line: { color: LINE, width: 0.5 } });
      s.addText(v, { isTextBox: true, x: x + 0.2, y: yy + 0.06, w: w - 0.4, h: 0.5, margin: 0,
        fontFace: HEAD, fontSize: 19, bold: true, color: RED });
      s.addText(l, { isTextBox: true, x: x + 0.2, y: yy + 0.58, w: w - 0.4, h: 0.36, margin: 0,
        fontFace: BODY, fontSize: 9.5, color: MUTED });
    });
  },
  (s, x, y, w) => { // Audit
    vHead(s, x, y, w, "Historique chaîné par hash");
    const bw2 = (w - 2 * 0.3) / 3;
    [0, 1, 2].forEach((k) => {
      const bx = x + k * (bw2 + 0.3);
      s.addShape(p.ShapeType.roundRect, { x: bx, y: y + 0.65, w: bw2, h: 0.7, rectRadius: 0.05,
        fill: { color: k === 2 ? RED : INK } });
      s.addText("Run " + (k + 1), { isTextBox: true, x: bx, y: y + 0.65, w: bw2, h: 0.7, margin: 0,
        align: "center", valign: "middle", fontFace: BODY, fontSize: 10, bold: true, color: WHITE });
      if (k < 2) s.addText("→", { isTextBox: true, x: bx + bw2, y: y + 0.65, w: 0.3, h: 0.7, margin: 0,
        align: "center", valign: "middle", fontFace: HEAD, fontSize: 14, bold: true, color: MUTED });
    });
    s.addText("chaque run signe le précédent", { isTextBox: true, x, y: y + 1.45, w, h: 0.32, margin: 0,
      fontFace: BODY, fontSize: 9, italic: true, color: MUTED });
    pill(s, x, y + 1.95, w, 0.5, "  « Verify » — 14 / 14 contrôles reproduits à l'identique", PANEL, GREEN, 10);
  },
  (s, x, y, w) => { // Mapping
    vHead(s, x, y, w, "Chaîne de traçabilité");
    const steps = ["Contrôle", "Exigence BCBS 239 couverte", "Preuve produite (Evidence Pack)", "Hash du run qui l'atteste"];
    steps.forEach((t, k) => {
      const yy = y + 0.55 + k * 0.92;
      pill(s, x, yy, w, 0.6, "  " + t, k === 3 ? INK : PANEL, k === 3 ? WHITE : INK, 10);
      if (k < 3) s.addText("↓", { isTextBox: true, x, y: yy + 0.58, w, h: 0.34, margin: 0,
        align: "center", fontFace: HEAD, fontSize: 12, bold: true, color: RED });
    });
  }
];
COMP.forEach((c, i) => {
  const s = p.addSlide(); s.background = { color: WHITE };
  s.addText("2 · La solution".toUpperCase(), { isTextBox: true, x: MX, y: 0.42, w: CW, h: 0.32, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: RED, charSpacing: 2 });
  numCircle(s, MX, 0.78, i + 1, 0.6);
  s.addText(c[0], { isTextBox: true, x: MX + 0.85, y: 0.74, w: CW - 0.85, h: 0.75, margin: 0,
    fontFace: HEAD, fontSize: 26, bold: true, color: INK });
  const lw = 6.7, rx = MX + lw + 0.5, rw = CW - lw - 0.5;
  bullets(s, c[1], MX, 2.15, lw, 4.2, 13.5);
  card(s, rx, 1.95, rw, 4.55);
  visBuilders[i](s, rx + 0.32, 2.2, rw - 0.64, 4.05);
  footer(s, 4 + i);
  notes(s, c[0] + ". " + c[1].join(" "));
});

// ============================================================ 10 — USE CASE (dataset)
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "3 · Cas d'usage", "Un fichier EUC réel, 14 règles, chaque dimension couverte");
  s.addText([
    { text: "Fichier BIS « OTC derivatives turnover »  ", options: { bold: true, fontFace: BODY, fontSize: 13, color: INK } },
    { text: "— ~78 000 lignes, 73 colonnes.   14 règles : deux par dimension, une conçue pour passer, une pour échouer.",
      options: { fontFace: BODY, fontSize: 12.5, color: MUTED } }
  ], { isTextBox: true, x: MX, y: 1.62, w: CW, h: 0.5, margin: 0 });
  const rows = [
    ["Dimension", "Règle conforme", "Règle en écart (volume détecté)"],
    ["Complétude", "Catégorie de risque toujours renseignée", "Colonne « 2013 » vide à 23 %"],
    ["Validité", "Code pays de contrepartie connu", "Code secteur hors référentiel — 2 lignes"],
    ["Unicité", "Identifiant de série unique", "Combinaison de dimensions non unique — 27 290"],
    ["Cohérence", "Secteur présent au référentiel", "Code pays « 5Z » absent du référentiel — 8 997"],
    ["Fraîcheur", "Flux daté à moins de 10 ans", "5 flux pays datant de plus de 7 jours"],
    ["Rapprochement", "Positions EUC = grand livre", "Grand livre stressé — 3 écarts + 1 deal manquant"]
  ];
  s.addTable(rows.map((r, ri) => r.map((cell, ci) => ({
    text: cell,
    options: {
      fontFace: BODY, fontSize: ri === 0 ? 11 : 11.5,
      bold: ri === 0, color: ri === 0 ? WHITE : (ci === 1 ? GREEN : (ci === 2 ? RED : INK)),
      fill: { color: ri === 0 ? INK : (ri % 2 ? WHITE : PANEL) },
      align: "left", valign: "middle", margin: 4
    }
  }))), { x: MX, y: 2.25, w: CW, colW: [2.1, 4.7, 5.33], rowH: 0.6,
    border: { type: "solid", color: LINE, pt: 0.75 } });
  footer(s, 10);
  notes(s, "Pour montrer les 6 dimensions, on a chargé un vrai fichier EUC de la BIS. 14 règles : pour chaque dimension, une règle qui passe et une qui échoue, avec le volume d'anomalies réellement détecté. Cohérence et rapprochement s'appuient sur de petits fichiers de référence — parce qu'un contrôle de cohérence a besoin d'une deuxième table.");
})();

// ============================================================ 11 — USE CASE (one run)
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "3 · Cas d'usage", "Une seule exécution — et tout est produit, et vérifié");
  const stats = [
    ["87 / 100", "Score DQ composite\n(pondéré par sévérité)"],
    ["8 / 14", "contrôles conformes"],
    ["4", "incidents critiques ouverts\n+ action corrective"],
    ["14 / 14", "contrôles reproduits à\nl'identique par « Verify »"]
  ];
  const sw = (CW - 0.45 * 3) / 4;
  stats.forEach((st, i) => {
    const x = MX + i * (sw + 0.45);
    card(s, x, 1.75, sw, 1.85);
    s.addText(st[0], { isTextBox: true, x, y: 1.9, w: sw, h: 0.7, margin: 0, align: "center",
      fontFace: HEAD, fontSize: 26, bold: true, color: RED });
    s.addText(st[1], { isTextBox: true, x: x + 0.12, y: 2.62, w: sw - 0.24, h: 0.85, margin: 0, align: "center",
      fontFace: BODY, fontSize: 10, color: MUTED });
  });
  s.addText("Conformes vs en écart — 3 exécutions chaînées", {
    isTextBox: true, x: MX, y: 3.95, w: CW, h: 0.35, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: INK });
  s.addChart(p.ChartType.bar, [
    { name: "Conformes", labels: ["Run 1", "Run 2", "Run 3"], values: [8, 8, 8] },
    { name: "En écart", labels: ["Run 1", "Run 2", "Run 3"], values: [6, 4, 6] }
  ], {
    x: MX, y: 4.3, w: 7.4, h: 2.5, barDir: "col", barGrouping: "clustered",
    chartColors: [GREEN, RED], showLegend: true, legendPos: "b", legendFontSize: 9,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 9, dataLabelColor: INK,
    catAxisLabelColor: MUTED, catAxisLabelFontSize: 10, valAxisHidden: true,
    valGridLine: { style: "none" }, catGridLine: { style: "none" },
    valAxisMaxVal: 16, barGapWidthPct: 90
  });
  card(s, MX + 7.9, 4.3, CW - 7.9, 2.5, PANEL);
  bullets(s, [
    "Scorecard + Evidence Pack + mapping superviseur générés en un seul passage.",
    "3 runs chaînés par hash : l'historique est inviolable.",
    "Le catalogue a changé entre les runs — c'est visible dans le registre."
  ], MX + 8.25, 4.55, CW - 8.55, 2.1, 11);
  footer(s, 11);
  notes(s, "Une exécution produit tout : le score composite, la liste des contrôles conformes et en écart, les incidents critiques avec leur remédiation, et l'Evidence Pack. Le « Verify » rejoue la config figée sur les données figées et retrouve exactement les 14 résultats. Sur 3 exécutions on voit la reproductibilité et la trace de l'historique.");
})();

// ============================================================ 12 — CONFORMITÉ
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "4 · Conformité", "Ce que le brief demande — et où nous le livrons");
  const items = [
    ["Annexe A.2 — 14 attributs de règle", "Catalogue au schéma canonique"],
    ["Annexe B.2 — 10 composants de preuve", "Evidence Pack par exécution"],
    ["Annexe B.3 — vérification indépendante", "« Verify this run »"],
    ["Annexe C — mapping superviseur", "Généré depuis le catalogue"],
    ["6 dimensions de qualité", "6 sur 6 couvertes"],
    ["Frugal, IA optionnelle", "0 dépendance IA"],
    ["Déterministe & reproductible", "Prouvé (tests + Verify)"],
    ["Qualité logicielle", "42 tests automatisés, code nettoyé"]
  ];
  const colW = (CW - 0.5) / 2;
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * (colW + 0.5), y = 1.85 + row * 1.18;
    s.addShape(p.ShapeType.ellipse, { x, y: y + 0.03, w: 0.32, h: 0.32, fill: { color: GREEN } });
    s.addText("✓", { isTextBox: true, x, y: y + 0.03, w: 0.32, h: 0.32, margin: 0, align: "center",
      valign: "middle", fontFace: BODY, fontSize: 13, bold: true, color: WHITE });
    s.addText(it[0], { isTextBox: true, x: x + 0.46, y: y - 0.05, w: colW - 0.46, h: 0.34, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: INK });
    s.addText(it[1], { isTextBox: true, x: x + 0.46, y: y + 0.3, w: colW - 0.46, h: 0.6, margin: 0,
      fontFace: BODY, fontSize: 11, color: MUTED });
  });
  footer(s, 12);
  notes(s, "Point par point : chaque exigence du brief — les annexes A.2, B.2, B.3, C, les 6 dimensions, la contrainte de frugalité, le déterminisme — est adressée, et on peut montrer où. Plus 42 tests automatisés pour la robustesse.");
})();

// ============================================================ 13 — AXES D'ÉVALUATION
(() => {
  const s = p.addSlide(); s.background = { color: WHITE };
  titleBar(s, "4 · Valorisation", "Les quatre axes d'évaluation — notre réponse");
  const ax = [
    ["Qualité technique", "Moteur générique, exécution reproductible, résilient aux pannes de source, 42 tests automatisés."],
    ["Maturité DQ", "6 dimensions sur 6, règles réutilisables sur tout dataset, seuils de tolérance paramétrables."],
    ["Gouvernance & auditabilité", "Evidence Pack, registre chaîné par hash, vérification indépendante, sign-off, journaux de changements."],
    ["Valeur métier", "Réduction du risque, incidents actionnables avec remédiation, déploiement « 2 fichiers », exports Power BI."]
  ];
  const cw = (CW - 0.5) / 2, ch = 2.15;
  ax.forEach((a, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * (cw + 0.5), y = 1.9 + row * (ch + 0.4);
    card(s, x, y, cw, ch);
    numCircle(s, x + 0.28, y + 0.28, i + 1, 0.4);
    s.addText(a[0], { isTextBox: true, x: x + 0.8, y: y + 0.26, w: cw - 1.1, h: 0.44, margin: 0,
      fontFace: HEAD, fontSize: 15, bold: true, color: RED });
    s.addText(a[1], { isTextBox: true, x: x + 0.32, y: y + 0.85, w: cw - 0.64, h: 1.1, margin: 0,
      fontFace: BODY, fontSize: 11.5, color: INK });
  });
  footer(s, 13);
  notes(s, "Sur les quatre axes d'évaluation annoncés : qualité technique, maturité DQ, gouvernance et auditabilité, valeur métier — voici en une ligne ce que la solution apporte pour chacun.");
})();

// ============================================================ 14 — PERSPECTIVES : SCALE
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  titleBar(s, "5 · Perspectives", "Passer à l'échelle — sans rien réécrire", true);
  const cw = (CW - 0.5) / 2;
  [["À l'horizontale — plus d'EUC",
    ["Un nouvel EUC = 2 fichiers de config + 1 appel. Zéro code.",
     "Un catalogue central versionné, tiré par chaque EUC.",
     "La CLI s'insère dans n'importe quel pipeline ou CI (contrôle bloquant)."]],
   ["À la verticale — plus de volume",
    ["Les 6 fonctions ont un contrat fixe.",
     "On remplace pandas par DuckDB ou Spark SQL sans toucher au catalogue, à la preuve, ni à l'appli.",
     "Exécution parallèle des règles, runs incrémentaux par partition."]]
  ].forEach((b, i) => {
    const x = MX + i * (cw + 0.5);
    s.addShape(p.ShapeType.roundRect, { x, y: 1.95, w: cw, h: 4.4, rectRadius: 0.09,
      fill: { color: "26262C" }, line: { color: "3A3A42", width: 0.75 } });
    s.addText(b[0], { isTextBox: true, x: x + 0.35, y: 2.2, w: cw - 0.7, h: 0.5, margin: 0,
      fontFace: HEAD, fontSize: 16, bold: true, color: i ? "C9A2AB" : "C9A2AB" });
    s.addText(b[1].map((t, j) => ({ text: t, options: { bullet: { code: "2013", indent: 12 },
      breakLine: true, paraSpaceAfter: 11, fontFace: BODY, fontSize: 12.5, color: "E7E5E2" } })),
      { isTextBox: true, x: x + 0.35, y: 2.85, w: cw - 0.7, h: 3.3, margin: 0, valign: "top" });
  });
  footer(s, 14, true);
  notes(s, "Scalabilité. À l'horizontale, c'est déjà de la configuration : un EUC de plus, c'est deux fichiers. À la verticale, comme les six fonctions de contrôle ont un contrat fixe, on peut changer le moteur d'exécution — DuckDB, Spark SQL — sans toucher au reste. Rien dans le design ne change.");
})();

// ============================================================ 15 — MVP + CLÔTURE
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  titleBar(s, "5 · Perspectives", "Un MVP honnête — et une suite à faible risque", true);
  const cw = (CW - 0.5) / 2;
  [["Aujourd'hui",
    ["CSV & Excel opérationnels (3 connecteurs à finir)",
     "Exécution en mémoire — échelle EUC",
     "Preuve en fichiers locaux",
     "Application mono-utilisateur"]],
   ["Phase suivante",
    ["Connecteurs JSON / SQL / SharePoint",
     "Backend SQL push-down (DuckDB / Spark)",
     "Stockage WORM pour la preuve",
     "Authentification et rôles"]]
  ].forEach((b, i) => {
    const x = MX + i * (cw + 0.5);
    s.addShape(p.ShapeType.roundRect, { x, y: 1.9, w: cw, h: 3.0, rectRadius: 0.09,
      fill: { color: "26262C" }, line: { color: "3A3A42", width: 0.75 } });
    s.addText(b[0], { isTextBox: true, x: x + 0.35, y: 2.1, w: cw - 0.7, h: 0.45, margin: 0,
      fontFace: HEAD, fontSize: 15, bold: true, color: "C9A2AB" });
    s.addText(b[1].map((t) => ({ text: t, options: { bullet: { code: "2013", indent: 12 },
      breakLine: true, paraSpaceAfter: 8, fontFace: BODY, fontSize: 11.5, color: "E7E5E2" } })),
      { isTextBox: true, x: x + 0.35, y: 2.65, w: cw - 0.7, h: 2.1, margin: 0, valign: "top" });
  });
  s.addShape(p.ShapeType.roundRect, { x: MX, y: 5.15, w: CW, h: 0.85, rectRadius: 0.08, fill: { color: RED } });
  s.addText("Le cycle de gouvernance est complet et prouvé. Le durcissement production est la phase suivante — les interfaces sont déjà définies.", {
    isTextBox: true, x: MX + 0.35, y: 5.15, w: CW - 0.7, h: 0.85, margin: 0, valign: "middle",
    fontFace: BODY, fontSize: 12, bold: true, color: WHITE });
  s.addText("« D'un EUC que personne ne peut auditer, à une couche de contrôle qu'un régulateur peut lire. »", {
    isTextBox: true, x: MX, y: 6.2, w: CW, h: 0.6, margin: 0,
    fontFace: HEAD, fontSize: 15, italic: true, color: WHITE });
  footer(s, 15, true);
  notes(s, "Soyons honnêtes : c'est un MVP. CSV et Excel marchent, trois connecteurs restent à finir ; l'exécution est en mémoire ; la preuve est en fichiers locaux. Mais le cycle de gouvernance — définir, exécuter, restituer, prouver — est complet et démontré. La suite, c'est du durcissement, à faible risque, parce que les interfaces sont déjà là. Merci.");
})();

p.writeFile({ fileName: "C:/Users/Basset/Downloads/dq_compass/dq_compass/docs/DQ_Compass_Presentation.pptx" })
  .then(f => console.log("wrote", f));
