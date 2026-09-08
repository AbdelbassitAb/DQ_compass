"""
demo_seed.py -- register the demo data sources and seed a full Control Catalogue
for the `finance_data` dataset (BIS OTC-derivatives turnover).

Creates, for every one of the 6 DQ dimensions, at least one rule that PASSES and
one that FAILS, so a single `python dq_engine.py` run produces a complete
Reporting + Audit demo.

    python demo_seed.py            # add sources + rules (idempotent upsert)
    python dq_engine.py           # execute -> evidence/<run_id>/
    python reporting/scorecard.py # build reporting/ outputs

Helper reference files live in sample_data/ :
    ref_dimension_codes.csv   valid code lists (Consistency)
    feed_status.csv           per-country feed timestamps (Timeliness)
    recon_euc_positions.csv   EUC position extract       (Reconciliation source)
    recon_gl_match.csv        ledger extract, ties out   (Reconciliation PASS ref)
    recon_gl_break.csv        ledger extract, 3 gaps + 1 missing deal (FAIL ref)
"""
from __future__ import annotations

from rule_authoring import schema
from rule_authoring.app import source_store, store

USER = "demo_seed"
CSV = lambda path: {"path": path, "delimiter": ",", "header_row": "1",
                    "encoding": "utf-8", "quotechar": '"', "skip_rows": "0"}

SOURCES = [
    ("ref_dimension_codes",  CSV("sample_data/ref_dimension_codes.csv")),
    ("feed_status",          CSV("sample_data/feed_status.csv")),
    ("recon_euc_positions",  CSV("sample_data/recon_euc_positions.csv")),
    ("recon_gl_match",       CSV("sample_data/recon_gl_match.csv")),
    ("recon_gl_break",       CSV("sample_data/recon_gl_break.csv")),
]

# (rule_id, name, type, description, dataset, params, severity, frequency, owner,
#  output_type, kpi, remediation, ref_dataset, regulatory_ref, threshold_pct)
R = []


def rule(rid, name, ctype, desc, ds, params, sev, freq, owner, otype, kpi, rem,
         ref="", reg="", tpct=None):
    r = dict(rule_id=rid, control_name=name, control_type=ctype, description=desc,
             dataset_scope=ds, ref_dataset_scope=ref, severity=sev, frequency=freq,
             owner=owner, output_type=otype, kpi=kpi, remediation_action=rem,
             regulatory_ref=reg, params=params, threshold_pct=tpct, active=True)
    r["data_element"] = schema.derive_data_element(ctype, params)
    r["threshold"] = schema.derive_threshold_text(ctype, params, tpct)
    r["logic_definition"] = schema.derive_logic_definition(ctype, params, ds, ref)
    R.append(r)


# ------------------------------------------------------------------ COMPLETENESS
rule("CMP_PASS", "Risk category always populated", "Completeness",
     "Every turnover series must carry a derivatives risk category (DER_RISK).",
     "finance_data", {"field": "DER_RISK"},
     "High", "Daily", "Data Steward Markets", "Error dataset",
     "% completeness", "Reject the feed and ask the source to repopulate DER_RISK.",
     reg="BCBS 239 - Principle 4 (Completeness)")

rule("CMP_FAIL", "2013 turnover value populated", "Completeness",
     "The 2013 turnover column must be populated for every reported series.",
     "finance_data", {"field": "2013"},
     "Medium", "Monthly", "Data Owner EUC", "Error dataset",
     "% completeness 2013",
     "Confirm whether 2013 is in scope; backfill from the historical extract or "
     "mark the column out of scope.")

rule("CMP_THRESHOLD_PASS", "2019 turnover value populated (<=30% gap tolerated)",
     "Completeness",
     "The 2019 turnover column should be mostly populated; up to 30% of series "
     "may legitimately have no 2019 observation.",
     "finance_data", {"field": "2019"},
     "Low", "Monthly", "Data Owner EUC", "Summary report",
     "% completeness 2019",
     "If the gap exceeds 30%, investigate the 2019 extract before publishing.",
     tpct=30.0)

# ---------------------------------------------------------------------- VALIDITY
rule("VAL_LIST_PASS", "Counterparty country code is known", "Validity",
     "DER_CPC must be one of the three published counterparty-country groupings.",
     "finance_data",
     {"field": "DER_CPC", "allowed_values": ["1E", "5J", "5Z"]},
     "Medium", "Daily", "Data Steward Markets", "Validation report",
     "% valid DER_CPC", "Map the unknown code or extend the reference list.")

rule("VAL_LIST_FAIL", "Counterparty sector is an accepted code", "Validity",
     "DER_SECTOR_CPY must belong to the accepted counterparty-sector set "
     "(A-J, P, U, V, W). 'X' (related-party trades) is not accepted here.",
     "finance_data",
     {"field": "DER_SECTOR_CPY",
      "allowed_values": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
                         "P", "U", "V", "W"]},
     "High", "Daily", "Control Owner", "Validation report",
     "% valid DER_SECTOR_CPY",
     "Confirm whether related-party trades ('X') belong in this cut; if so, add "
     "'X' to the rule, otherwise correct the source classification.")

rule("VAL_REGEX_PASS", "Series key format", "Validity",
     "The Series identifier must be upper-case alphanumerics and colons only "
     "(the BIS key convention).",
     "finance_data", {"field": "Series", "regex": "^[A-Z0-9:]+$"},
     "Low", "Per run", "Data Owner EUC", "Validation report",
     "% well-formed Series keys",
     "Trim stray characters / whitespace from the Series key at the source.")

# -------------------------------------------------------------------- UNIQUENESS
rule("UNQ_PASS", "Series identifier is unique", "Uniqueness",
     "The Series key must identify exactly one row in the extract.",
     "finance_data", {"keys": ["Series"]},
     "High", "Per run", "Data Owner EUC", "Duplicate records list",
     "Duplicate rate", "De-duplicate the extract and investigate the source join.",
     reg="BCBS 239 - Principle 3 (Accuracy and Integrity)")

rule("UNQ_FAIL", "One row per business dimension combination", "Uniqueness",
     "The combination of every business dimension (country, instrument, risk, "
     "sector, both currency legs, maturity, rating, execution method, basis) is "
     "expected to identify a single series.",
     "finance_data",
     {"keys": ["DER_REP_CTY", "DER_INSTR", "DER_RISK", "DER_SECTOR_CPY",
               "DER_CURR_LEG1", "DER_CURR_LEG2", "DER_ISSUE_MAT", "DER_RATING",
               "DER_EX_METHOD", "DER_BASIS"]},
     "Medium", "Per run", "Control Owner", "Duplicate records list",
     "Duplicate rate",
     "Review the grain of the extract: add the missing dimension(s) to the key "
     "or aggregate the duplicates.")

# ------------------------------------------------------------------- CONSISTENCY
rule("CON_PASS", "Counterparty sector exists in the code table", "Consistency",
     "Every DER_SECTOR_CPY value must exist in the counterparty-sector "
     "reference code table.",
     "finance_data", {"field": "DER_SECTOR_CPY", "ref_field": "sector_code"},
     "Medium", "Daily", "Data Steward Reference", "Exception dataset",
     "% referential integrity",
     "Add the missing code to ref_dimension_codes or correct the source value.",
     ref="ref_dimension_codes")

rule("CON_FAIL", "Counterparty country exists in the code table", "Consistency",
     "Every DER_CPC value must exist in the counterparty-country reference code "
     "table (which currently lists only 1E and 5J).",
     "finance_data", {"field": "DER_CPC", "ref_field": "cpc_code"},
     "High", "Daily", "Data Steward Reference", "Exception dataset",
     "% referential integrity",
     "Extend ref_dimension_codes with the missing counterparty-country grouping "
     "(5Z) after confirming it is a valid published code.",
     ref="ref_dimension_codes", reg="BCBS 239 - Principle 3 (Accuracy and Integrity)")

# --------------------------------------------------------------------- TIMELINESS
rule("TIM_PASS", "Feed refreshed within 10 years", "Timeliness",
     "Every country feed in feed_status must have been refreshed within the last "
     "3650 days (sanity bound).",
     "feed_status", {"field": "last_updated", "max_lag_days": 3650,
                     "reference_date": "today"},
     "Low", "Daily", "Control Owner", "SLA breach log",
     "% feeds within sanity bound",
     "Investigate any feed with no refresh in a decade -- likely decommissioned.")

rule("TIM_FAIL", "Feed refreshed within 7 days", "Timeliness",
     "Every country feed in feed_status must have been refreshed within the last "
     "7 calendar days.",
     "feed_status", {"field": "last_updated", "max_lag_days": 7,
                     "reference_date": "today"},
     "High", "Daily", "Data Steward Markets", "SLA breach log",
     "% feeds within SLA",
     "Chase the source for the stale country feeds; escalate if no refresh in "
     "the next cycle.",
     reg="BCBS 239 - Principle 5 (Timeliness)")

# ----------------------------------------------------------------- RECONCILIATION
rule("REC_PASS", "EUC positions tie to the ledger", "Reconciliation",
     "Each EUC position amount must match the ledger amount within 1%.",
     "recon_euc_positions",
     {"key": "deal_id", "field": "amount", "ref_field": "amount",
      "tolerance_pct": 1},
     "High", "Daily", "Finance Control", "Reconciliation report",
     "% reconciled", "Escalate any residual break to Finance Control.",
     ref="recon_gl_match")

rule("REC_FAIL", "EUC positions tie to the ledger (stressed feed)",
     "Reconciliation",
     "Each EUC position amount must match the stressed ledger extract within 1% "
     "(this extract has three re-priced deals and one dropped deal).",
     "recon_euc_positions",
     {"key": "deal_id", "field": "amount", "ref_field": "amount",
      "tolerance_pct": 1},
     "High", "Daily", "Finance Control", "Reconciliation report",
     "% reconciled",
     "Investigate each break: confirm the trade economics, then correct the EUC "
     "or the ledger; chase the deal that is missing on the ledger side.",
     ref="recon_gl_break", reg="BCBS 239 - Principle 7 (Accuracy - reporting)")


def main():
    for name, cfg in SOURCES:
        source_store.upsert(name, "csv", cfg, user=USER,
                            note="demo reference dataset", status="active")
        print(f"source  + {name}")
    for r in R:
        store.upsert(r, user=USER, note="demo seed: full pass/fail matrix")
        print(f"rule    + {r['rule_id']:20} {r['control_type']:14} {r['dataset_scope']}")
    print(f"\n{len(SOURCES)} sources, {len(R)} rules seeded.")


if __name__ == "__main__":
    main()
