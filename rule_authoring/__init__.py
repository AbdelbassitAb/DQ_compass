"""
rule_authoring

Web interface to create / edit the business rules of the DQ Compass Control
Catalogue, with:
  - schema.py : the "meta-catalogue" -> the validation rules applied to every
    business rule entered (structure, params per control type, cross-field
    consistency) + generation of the auditor-readable columns.
  - store.py  : CSV persistence in the canonical format (14 Appendix A.2
    attributes + technical columns) and append-only catalogue audit log.
  - app.py    : Flask application (list + coverage matrix, dynamic form per
    control type, history, generated preview).
"""
