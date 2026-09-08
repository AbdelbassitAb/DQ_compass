# -*- coding: utf-8 -*-
"""
build_pitch_notes.py -- trame de presentation DQ Compass : ce qu'il FAUT dire
dans chaque partie, la section « choix de l'outil », le passage a la demo,
la prepa Q&A et le budget temps.

    pip install reportlab
    python docs/build_pitch_notes.py

Sortie : docs/DQ_Compass_Points_Cles_Presentation.pdf
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

OUT = Path(__file__).resolve().parent / "DQ_Compass_Points_Cles_Presentation.pdf"

INK = colors.HexColor("#14161c")
MUTED = colors.HexColor("#5b6270")
ACCENT = colors.HexColor("#9E1B32")
LINE = colors.HexColor("#d3d7df")
HEADBG = colors.HexColor("#f0f1f4")
OK = colors.HexColor("#137A46")
BAD = colors.HexColor("#8a1220")
CODEBG = colors.HexColor("#f5f5f7")

styles = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold",
                            fontSize=22, leading=26, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11, leading=15,
                               textColor=MUTED, spaceAfter=2),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13.5, leading=17,
                         textColor=ACCENT, spaceBefore=15, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.6, leading=14,
                         textColor=INK, spaceBefore=8, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.2, leading=12.6,
                           textColor=INK, spaceAfter=4, alignment=TA_LEFT),
    "say": ParagraphStyle("say", fontName="Helvetica", fontSize=9.2, leading=12.6,
                          textColor=INK, leftIndent=13, firstLineIndent=-11, spaceAfter=3),
    "dont": ParagraphStyle("dont", fontName="Helvetica-Oblique", fontSize=9, leading=12,
                           textColor=BAD, leftIndent=13, firstLineIndent=-11, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10.5,
                            textColor=MUTED, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10.4, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8, leading=10.4, textColor=INK),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7.6, leading=10.2, textColor=INK,
                           backColor=CODEBG, borderPadding=5, spaceBefore=2, spaceAfter=6),
}

_SUBS = [("→", " -> "), ("≤", " <= "), ("≥", " >= "), ("×", " x "),
         ("…", "..."), ("–", "-"), ("—", " - "), ("·", " - "),
         ("œ", "oe"), ("’", "'")]


def _mk(t: str, style: str) -> Paragraph:
    for a, b in _SUBS:
        t = t.replace(a, b)
    t = re.sub(r"&(?!amp;|lt;|gt;|quot;|#\d+;)", "&amp;", t)
    return Paragraph(t, S[style])


def P(t, s="body"):
    return _mk(t, s)


def SAY(items):
    return [_mk('<font color="#137A46"><b>&#9656;</b></font>  ' + t, "say") for t in items]


def DONT(items):
    return [_mk("&#215;  " + t, "dont") for t in items]


def CODE(t):
    return Paragraph(t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                     .replace("\n", "<br/>"), S["code"])


def TBL(headers, rows, widths):
    data = [[_mk(h, "cellb") for h in headers]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else _mk(str(c), "cell") for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), HEADBG),
          ("GRID", (0, 0), (-1, -1), 0.4, LINE),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
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
def sayblock(items): [A(x) for x in SAY(items)]
def dontblock(items): [A(x) for x in DONT(items)]


# ============================ COVER ============================
A(Spacer(1, 30))
A(P("DQ Compass", "title"))
A(P("Points cles a dire dans la presentation - trame par partie", "h1"))
A(Spacer(1, 6))
A(P("MBA-ESG / SG GSC - Datathon 2026   |   Groupe 1   |   15 min + 5 min Q&R", "subtitle"))
A(P("Genere le " + date.today().isoformat(), "subtitle"))
A(Spacer(1, 14))
A(P("<b>Comment lire ce document.</b> Pour chaque partie : les idees a faire passer "
    "(marquees d'un triangle vert), et ce qu'il faut eviter (en rouge italique). "
    "La section 10 (choix de l'outil) se dit a l'oral juste avant la demo. "
    "Sections 14 (Q&R) et 15 (budget temps) en preparation."))
SP(8)
H2("Regles d'or")
sayblock([
    "Placer tot les mots-cles : <b>tracable, reproductible, auditable, preuve, BCBS 239, "
    "plug-and-play, frugal, deterministe</b>.",
    "Toujours relier une fonctionnalite a une exigence du brief ou a un axe d'evaluation.",
    "Annoncer clairement le perimetre MVP - ne rien promettre qui n'est pas fait.",
])
dontblock([
    "Lire les slides mot a mot ; se perdre dans le code ; depasser le temps.",
    "Presenter les 6 briques au meme niveau de detail - l'Audit est le point fort.",
])
PB()

# ============================ 0 ============================
H1("0 - Ouverture (30 s)")
sayblock([
    "Qui : Groupe 1. Use case : <b>une couche de controle Data Quality plug-and-play "
    "pour les EUC</b>.",
    "L'accroche : <i>les EUC portent des processus critiques mais echappent a la "
    "gouvernance du SI ; DQ Compass se branche sans ecrire de code et produit la preuve "
    "par defaut.</i>",
    "Le plan : problematique, solution brique par brique, cas d'usage complet, "
    "conformite, perspectives - et une demo.",
])

# ============================ 1 ============================
H1("1 - La problematique (1 min 30)")
sayblock([
    "EUC = End-User Computing : Excel, Access, scripts qui font tourner de vrais "
    "processus metier, <b>hors du SI et de ses controles</b>.",
    "Trois douleurs : (1) hors gouvernance ; (2) chaque equipe refait ses controles a la "
    "main, sans trace exploitable ; (3) <b>BCBS 239</b> exige des controles traces, "
    "reproductibles et auditables - un classeur Excel ne sait pas le demontrer.",
    "La cible du brief : le cycle <b>Definir, Executer, Restituer, Prouver</b>, sur 6 "
    "dimensions (completude, validite, unicite, coherence, fraicheur, rapprochement), "
    "<b>frugal</b> (IA optionnelle), <b>deterministe</b>, <b>reutilisable</b>.",
])
dontblock(["Entrer dans le detail technique ici - c'est le cadrage du besoin."])

# ============================ 2 ============================
H1("2 - La solution, vue d'ensemble (1 min)")
sayblock([
    "Le principe qui porte tout : <b>les regles sont des donnees, le moteur est "
    "generique</b> -- on configure, on ne code pas.",
    "Quatre briques : <b>Catalogue</b> (definit), <b>Moteur</b> (execute), <b>Reporting</b> "
    "(restitue), <b>Audit</b> (prouve), alimentees par des connecteurs.",
    "Consequence concrete : <b>un nouvel EUC = 2 fichiers de configuration, aucun "
    "developpement</b>.",
])

# ============================ 3 ============================
H1("3 - Le Catalogue de controles (1 min)")
sayblock([
    "Une regle = <b>une ligne de fichier</b> ; une application web pour les creer, les "
    "modifier, les versionner.",
    "Un <b>meta-catalogue (~30 verifications)</b> bloque toute regle invalide <b>avant</b> "
    "enregistrement (colonne inexistante, seuil incoherent, regex qui ne compile pas).",
    "14 attributs (Annexe A.2), 6 types de controle, severite, proprietaire, seuil de "
    "tolerance, action corrective.",
    "La definition en <b>SQL lisible par un auditeur</b> est generee automatiquement ; "
    "chaque changement est journalise (journal chaine par hash).",
])

# ============================ 4 ============================
H1("4 - Le Moteur d'execution (1 min)")
sayblock([
    "Une <b>fonction generique par dimension</b> : elle ne connait que des noms de "
    "colonnes -- elle tourne sur n'importe quel dataset, sans jamais le modifier.",
    "<b>Deterministe et reproductible</b> : meme entree, meme resultat.",
    "<b>Resilient</b> : une source manquante devient un statut ERROR, l'execution "
    "continue - le moteur ne plante jamais.",
    "<b>Seuils de tolerance</b> : ex. <i>&lt;= 1 % de lignes en anomalie = conforme</i>.",
])

# ============================ 5 ============================
H1("5 - Sources de donnees, plug and play (45 s)")
sayblock([
    "<b>Abstraction connecteur</b> : CSV et Excel operationnels ; JSON / SQL / SharePoint "
    "prets en selecteurs (phase 2) - perimetre MVP assume.",
    "Ajouter une source = <b>une ligne de configuration</b>.",
    "<b>Politique de suppression maitrisee</b> : retrait reversible (cascade sur les "
    "regles), purge definitive, renommage (reaffecte les regles dependantes).",
])

# ============================ 6 ============================
H1("6 - Le Reporting (1 min)")
sayblock([
    "<b>Deux publics</b> via un filtre d'audience : le metier (risk / data owner) et le "
    "data engineer.",
    "<b>Score DQ composite</b> pondere par severite (un chiffre a suivre), tendance, "
    "sante par dataset, matrice de couverture, incidents ouverts + remediation, exceptions "
    "par proprietaire / dimension, fiabilite des regles.",
    "<b>Selecteur d'execution</b> : on peut recalculer le tableau de bord sur n'importe "
    "quelle execution passee.",
    "<b>7 exports CSV / JSON</b> : format d'echange pret pour Power BI - pas de "
    "re-developpement cote BI.",
])
dontblock([
    "Sur-vendre le score 87/100 : c'est une convention ponderee ; ce qui compte c'est la "
    "tendance et la comparaison entre datasets.",
])

# ============================ 7 ============================
H1("7 - L'Audit / l'auditabilite (1 min 30 - LE POINT FORT)")
sayblock([
    "<b>Evidence Pack par execution</b> : les 10 composants de l'Annexe B.2 - donnees "
    "figees (+ hash de contenu), configuration figee, parametres resolus, metriques, "
    "dataset d'exceptions, journaux, trace systeme, sign-off.",
    "<b>Registre des executions chaine par hash</b> : chaque run signe le precedent -- "
    "toute alteration d'un run passe devient <b>visible</b> (inviolable).",
    "<b>Verification independante « Verify »</b> : rejoue la configuration figee sur les "
    "donnees figees et retrouve le meme resultat (Annexe B.3).",
    "<b>Sign-off humain</b> + <b>2 journaux de changements chaines</b> (catalogue + "
    "sources) : qui a change quoi, quand.",
    "La phrase a marteler : <b>on ne fait pas que detecter les anomalies, on prouve le "
    "controle.</b>",
])

# ============================ 8 ============================
H1("8 - Le Mapping superviseur (45 s)")
sayblock([
    "<b>Genere depuis le catalogue</b> - jamais desynchronise.",
    "Pour chaque controle : <b>l'exigence BCBS 239 couverte, la preuve produite, le hash "
    "du run qui l'atteste</b> (Annexe C).",
    "C'est le <b>pont entre le technique et le langage superviseur</b>.",
])

# ============================ 9 ============================
H1("9 - Cas d'usage (1 min 30)")
sayblock([
    "Donnee <b>reelle</b> : fichier BIS « OTC derivatives turnover », ~78 000 lignes, "
    "73 colonnes - pas un jeu de donnees jouet.",
    "<b>14 regles : 2 par dimension</b>, une concue pour passer, une pour echouer -- une "
    "seule execution produit un reporting complet et tous les cas.",
    "Exemples parlants : code pays « 5Z » absent du referentiel = <b>8 997 lignes</b> ; "
    "<b>5 flux</b> pays datant de plus de 7 jours ; grand livre stresse = <b>3 ecarts + "
    "1 deal manquant</b>.",
    "Resultat : scorecard + Evidence Pack + mapping superviseur en un seul passage, "
    "le tout <b>verifie 14 / 14</b>.",
])
PB()

# ============================ 10 ============================
H1("10 - Choix de l'outil et de la stack (1 min 30) -- JUSTE AVANT LA DEMO")
BODY("Cette section justifie les decisions techniques. Elle repond a la contrainte "
     "« frugal by design » du brief et coupe court aux questions du jury.")
A(TBL(["Choix", "Pourquoi (a dire)"], [
    ["Python + pandas ; 0 IA, 0 base de donnees, 0 cloud",
     "Contrainte de frugalite du brief. Tourne sur un simple poste. Langage des equipes "
     "data, lisible."],
    ["Les regles en CSV (pas une appli a base de donnees)",
     "Versionnable dans Git, comparable (diff), lisible sans l'outil, zero infrastructure. "
     "Le meta-catalogue garantit la validite ; l'ecriture est atomique."],
    ["Une petite appli web (Flask)",
     "Une interface d'autorite pour creer / valider les regles et signer les runs, sans "
     "framework lourd - lancable en une commande."],
    ["Preuve en fichiers JSON / CSV (pas un SIEM)",
     "Transparents, auditables a l'oeil, portables. En production on les pousse sur du "
     "stockage WORM (immuable) - l'interface est deja la."],
    ["Hachage SHA-256 + chainage des runs",
     "Standard, deterministe, sans tiers de confiance. Detecte l'alteration ; la signature "
     "cryptographique est l'etape production."],
    ["Pas d'IA dans le scoring",
     "Un score DQ doit etre deterministe et explicable. L'IA reste une piste optionnelle "
     "(suggestion de regles par profilage des donnees)."],
    ["Reproductibilite",
     "Prouvee par 42 tests automatises et par la commande Verify - pas une promesse."],
], [58 * mm, 110 * mm]))
SP(4)
sayblock(["Transition : <i>« voila pour les choix techniques - place a la demonstration. »</i>"])

# ============================ 11 ============================
H1("11 - Passage a la demo (30 s d'annonce + 4-5 min)")
BODY("Annoncer la sequence, puis derouler. Garder une regle « en echec » sous la main "
     "pour le drill-down.")
A(TBL(["#", "Ce qu'on montre", "Ce qu'on dit en le montrant"], [
    ["1", "Le Catalogue - creer / valider une regle",
     "« une regle = un formulaire ; le meta-catalogue refuse une regle invalide. »"],
    ["2", "Lancer une execution (Run engine now)",
     "« le moteur applique tout le catalogue au dataset. »"],
    ["3", "La page Reporting",
     "score, tendance, incidents ouverts + remediation ; ouvrir une regle de Validite en "
     "echec -- les lignes fautives + « comment corriger »."],
    ["4", "La page Runs -- un Evidence Pack -- bouton Verify",
     "« tout est fige et rejouable ; Verify retrouve le meme resultat. »"],
    ["5", "La page Mapping",
     "« chaque controle relie a une exigence BCBS 239 et au hash du run. »"],
], [6 * mm, 62 * mm, 100 * mm]))
SP(3)
dontblock([
    "Plan B si la demo plante : les captures dans les slides + le PDF de conformite. "
    "Le dire calmement et continuer.",
])

# ============================ 12 ============================
H1("12 - Conformite et axes d'evaluation (1 min)")
sayblock([
    "Cocher explicitement : <b>Annexe A.2</b> (14 attributs), <b>B.2</b> (10 composants "
    "de preuve), <b>B.3</b> (verification independante), <b>Annexe C</b> (mapping), "
    "<b>6/6 dimensions</b>, <b>frugal / sans IA</b>, <b>deterministe</b>, <b>42 tests</b>.",
    "Relier aux 4 axes du jury : <b>qualite technique</b> (moteur generique, "
    "reproductible, resilient), <b>maturite DQ</b> (6 dimensions, reutilisable), "
    "<b>gouvernance et auditabilite</b> (Evidence Pack, chaine de hash, Verify, sign-off), "
    "<b>valeur metier</b> (risque reduit, incidents actionnables, deploiement 2 fichiers, "
    "exports BI).",
])

# ============================ 13 ============================
H1("13 - Perspectives (1 min)")
sayblock([
    "<b>A l'horizontale</b> : un EUC de plus = 2 fichiers ; catalogue central versionne, "
    "tire par chaque EUC ; la CLI s'insere dans la CI (controle bloquant).",
    "<b>A la verticale</b> : les 6 fonctions ont un contrat fixe -- on remplace pandas "
    "par DuckDB ou Spark SQL <b>sans toucher</b> au catalogue, a la preuve, ni a l'appli.",
    "<b>MVP honnete</b> : 3 connecteurs a finir, execution en memoire, preuve locale, "
    "appli mono-utilisateur -- phase suivante documentee, a faible risque.",
    "Cloture : <i>« d'un EUC que personne ne peut auditer, a une couche de controle qu'un "
    "regulateur peut lire. »</i>",
])
PB()

# ============================ 14 ============================
H1("14 - Q&R : questions probables et reponses courtes")
A(TBL(["Question", "Reponse en une phrase"], [
    ["Pourquoi pas d'IA ?",
     "Un score DQ doit etre deterministe et explicable. L'IA est une piste optionnelle "
     "(suggestion de regles par profilage)."],
    ["Ca tient a l'echelle ?",
     "Echelle EUC aujourd'hui ; grace au contrat de fonction fixe, on passe a DuckDB / "
     "Spark sans reecrire le catalogue ni la preuve."],
    ["Des regles en CSV, c'est robuste ?",
     "Meta-catalogue (~30 verifications) + ecriture atomique + journal chaine par hash + "
     "versionnement Git."],
    ["Qu'est-ce qui empeche de trafiquer une preuve ?",
     "La chaine de hash rend toute alteration visible ; en production, stockage WORM "
     "immuable."],
    ["Difference avec Great Expectations / un outil du marche ?",
     "Ici l'accent est sur la preuve et l'auditabilite de bout en bout + le mapping "
     "superviseur, pas seulement la detection - et zero infrastructure."],
    ["Combien de temps pour brancher un nouvel EUC ?",
     "Le temps d'ecrire 2 fichiers de configuration (source + regles)."],
    ["Le score 87/100, ca veut dire quoi ?",
     "Convention ponderee par severite : une regle High pese 5x une Low. On suit la "
     "tendance, pas la valeur absolue."],
    ["Et si une source est indisponible le jour J ?",
     "La regle passe en ERROR, l'execution continue, et c'est trace dans l'Evidence Pack."],
], [56 * mm, 112 * mm]))

# ============================ 15 ============================
H1("15 - Budget temps (15 min + 5 min Q&R)")
A(TBL(["Partie", "Duree", "Diapos"], [
    ["0  Ouverture", "0:30", "1"],
    ["1  Problematique", "1:30", "2"],
    ["2  Solution - vue d'ensemble", "1:00", "3"],
    ["3-8  Les 6 briques (Catalogue, Moteur, Sources, Reporting, Audit, Mapping)", "5:00", "4-9"],
    ["9  Cas d'usage", "1:30", "10-11"],
    ["10  Choix de l'outil / stack", "1:30", "oral, avant demo"],
    ["11  Demo", "4:00 - 5:00", "app live"],
    ["12  Conformite et axes d'evaluation", "1:00", "12-13"],
    ["13  Perspectives + cloture", "1:00", "14-15"],
    ["Total", "~15:00", ""],
], [104 * mm, 34 * mm, 30 * mm]))
SP(4)
SMALL("Si le temps deborde : compresser 3-8 (une phrase par brique sauf Audit) et raccourcir "
      "la demo aux etapes 3 et 4 (Reporting + Verify).")


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 12 * mm, "DQ Compass - Points cles de la presentation")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, "Page %d" % doc.page)
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
    title="DQ Compass - Points cles de la presentation", author="Groupe 1")
doc.addPageTemplates([PageTemplate(id="main",
                                   frames=[Frame(doc.leftMargin, doc.bottomMargin,
                                                 doc.width, doc.height, id="main")],
                                   onPage=_page)])
doc.build(story)
print("Wrote", OUT)
