"""
rule_authoring/schema.py

The "meta-catalogue": the set of rules that validates the business rules.

This module performs NO I/O. It exposes:
  - the controlled vocabularies (control types, severities, frequencies...)
  - validate_rule(...) -> ValidationReport : blocking errors + warnings
  - derivation helpers that produce the auditor-readable columns of Appendix
    A.2 (logic_definition, data_element, threshold) and a plain-language
    explanation, from the technical configuration.

Principle: a rule definition (the "what") is separated from its execution
(the "how"), and it is checked BEFORE it enters the catalogue.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

# --------------------------------------------------------------------------
# Controlled vocabularies
# --------------------------------------------------------------------------
CONTROL_TYPES = [
    "Completeness", "Validity", "Uniqueness",
    "Consistency", "Timeliness", "Reconciliation",
]

SEVERITIES = ["High", "Medium", "Low"]

# Strict: a frequency outside this list is a blocking error.
FREQUENCIES = [
    "Per run", "Hourly", "Daily", "Weekly", "Monthly", "Quarterly", "On demand",
]

# Loose: suggestions only; a value outside the list only raises an info.
OUTPUT_TYPE_SUGGESTIONS = [
    "Error dataset", "Summary report", "Alert", "Validation report",
    "Duplicate records list", "Exception dataset", "SLA breach log",
    "Reconciliation report",
]

RULE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,19}$")

# Params expected per control type (drives the UI + the validation).
# ref_dataset_scope is a dedicated catalogue column, not a param.
PARAM_SPEC = {
    "Completeness":   {"required": ["field"]},
    "Validity":       {"required": ["field"], "one_of": ["allowed_values", "regex", "range"]},
    "Uniqueness":     {"required": ["keys"]},
    "Consistency":    {"required": ["field", "ref_field"], "needs_ref_dataset": True},
    "Timeliness":     {"required": ["field", "max_lag_days"], "optional": ["reference_date"]},
    "Reconciliation": {"required": ["key", "field", "ref_field", "tolerance_pct"],
                       "needs_ref_dataset": True},
}

# Length bounds for the required text fields (min, max).
REQUIRED_TEXT_FIELDS = {
    "control_name": (3, 80),
    "description": (10, 500),
    "owner": (2, 80),
    "kpi": (2, 120),
    "remediation_action": (10, 500),
}


# --------------------------------------------------------------------------
# Inline help: single source for the form tooltips AND the documentation
# page (/docs). One place to maintain.
# --------------------------------------------------------------------------
FIELD_HELP = {
    "rule_id": "Unique, stable identifier of the rule (e.g. DQ07). Key in the catalogue, "
               "the evidence and the audit log. Not editable after creation.",
    "control_name": "Short, readable name of the control (3 to 80 characters). E.g. \"Amount not null\".",
    "control_type": "The DQ dimension being tested. Determines which parameters to fill in. "
                    "See the docs for the details of the 6 types.",
    "description": "Business purpose of the control in one sentence (>= 10 characters): "
                   "what the rule guarantees and why it exists.",
    "logic_definition": "Formal definition of the rule (pseudo-SQL). Generated automatically "
                        "from the type and parameters; serves as auditor-readable evidence.",
    "data_element": "Field(s) actually tested. Generated from the parameters.",
    "threshold": "Acceptance criteria in plain words (e.g. \"0 anomaly tolerated\", "
                 "\"gap <= 0.5%\"). Generated from the threshold and parameters.",
    "severity": "Criticality: High (blocking, escalated), Medium (to fix), Low (informational). "
                "Drives prioritisation and the traffic-light colour.",
    "frequency": "Expected execution periodicity. Declarative in the prototype "
                 "(a real scheduler would rely on it).",
    "owner": "Role responsible for the control and its remediation "
             "(Data Owner, Data Steward, Control Owner...).",
    "output_type": "Nature of the output produced on anomaly. "
                   "See the docs for the list and the meaning of each value.",
    "kpi": "Quantifiable indicator measured by the control. E.g. \"% completeness\", \"duplicate rate\".",
    "remediation_action": "Action expected when the control fails (>= 10 characters). "
                          "E.g. \"Contact the source owner\".",
    "regulatory_ref": "Optional. Supervisory requirement this control satisfies "
                      "(e.g. a BCBS 239 principle). Feeds the auto-generated Supervisory "
                      "Mapping (Appendix C). Left blank, a default is derived from the DQ dimension.",
    "dataset_scope": "Dataset the rule applies to. Must be declared in datasets_config.yaml.",
    "ref_dataset_scope": "Reference dataset. Required for Consistency (referential integrity) "
                         "and Reconciliation (matching).",
    "threshold_pct": "Tolerance threshold, as a % of records in anomaly. Empty = binary mode "
                     "(fails on the first anomaly). 1 = tolerates up to 1% before failing.",
    "p_field": "Column tested in the dataset. Must exist in the file.",
    "p_keys": "One or more columns forming the key. Several columns = composite key: it is the "
              "COMBINATION that must be unique, not each column on its own.",
    "p_key": "Join column used to match the two datasets (usually the business identifier).",
    "p_ref_field": "Column of the reference dataset to compare / join.",
    "p_validity_mode": "One validity criterion at a time: value list, regular expression, "
                       "or numeric range.",
    "p_allowed_values": "Exhaustive list of accepted values, one per line or comma-separated. "
                        "Any other value is an anomaly.",
    "p_regex": "Regular expression the value must match (it must compile).",
    "p_min_val": "Lower bound accepted (inclusive).",
    "p_max_val": "Upper bound accepted (inclusive).",
    "p_max_lag_days": "Maximum lag tolerated, in days, between the tested date and the reference date.",
    "p_reference_date": "Reference date for freshness: \"today\" (default) or a fixed date YYYY-MM-DD.",
    "p_tolerance_pct": "Relative gap tolerated between the source value and the reference value, "
                       "as a %, before a break is counted.",
    "note": "Reason for the change. Written as-is into the catalogue audit log.",
    "active": "When unchecked, the rule stays in the catalogue and the history but is no longer "
              "executed by the engine.",
}

CONTROL_TYPE_HELP = {
    "Completeness": "Mandatory fields are populated (neither NULL nor blank).",
    "Validity": "Values conform to a format or a domain (list, regex or range).",
    "Uniqueness": "No duplicate on a key, simple or composite.",
    "Consistency": "Referential integrity: every value exists in a reference dataset.",
    "Timeliness": "Freshness: the data is not older than a lag threshold.",
    "Reconciliation": "Matching: values agree between two sources, within a tolerance.",
}

OUTPUT_TYPE_HELP = {
    "Error dataset": "File of the records in anomaly, exported for investigation and remediation.",
    "Summary report": "Aggregated report (counts, rates) without the row-by-row detail.",
    "Alert": "Pushed notification (mail, channel) triggered on failure, usually for High controls.",
    "Validation report": "Report of the values compliant / non-compliant with a reference or a format.",
    "Duplicate records list": "List of the rows duplicated on the key of the uniqueness control.",
    "Exception dataset": "Synonym of Error dataset: the subset of rows that fail the control.",
    "SLA breach log": "Log of the freshness deadline breaches (Timeliness).",
    "Reconciliation report": "Source vs reference matching report: breaks, rows missing on "
                             "one side or the other.",
}

SEVERITY_HELP = {
    "High": "Critical control. A failure blocks or is escalated. Red light.",
    "Medium": "Anomaly to fix without immediate blocking. Amber light.",
    "Low": "Informational / comfort quality.",
}

FREQUENCY_HELP = {
    "Per run": "On every run of the pipeline / EUC.",
    "Hourly": "Every hour.",
    "Daily": "Once a day.",
    "Weekly": "Once a week.",
    "Monthly": "Once a month.",
    "Quarterly": "Once a quarter.",
    "On demand": "Triggered manually, no schedule.",
}

REGULATORY_REF_SUGGESTIONS = [
    "BCBS 239 - Principle 3 (Accuracy and Integrity)",
    "BCBS 239 - Principle 4 (Completeness)",
    "BCBS 239 - Principle 5 (Timeliness)",
    "BCBS 239 - Principle 6 (Adaptability)",
    "BCBS 239 - Principle 7 (Accuracy - reporting)",
    "SG internal Data Quality framework",
    "EUC governance policy",
]


# --------------------------------------------------------------------------
# Validation report
# --------------------------------------------------------------------------
@dataclass
class Issue:
    level: str      # "error" | "warning" | "info"
    field: str
    code: str
    message: str


@dataclass
class ValidationReport:
    issues: list = field(default_factory=list)

    def add(self, level: str, fld: str, code: str, message: str) -> None:
        self.issues.append(Issue(level, fld, code, message))

    @property
    def errors(self) -> list:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def infos(self) -> list:
        return [i for i in self.issues if i.level == "info"]

    @property
    def ok(self) -> bool:
        return not self.errors


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def parse_list(raw) -> list:
    """Accepts a list, or a string separated by commas / semicolons / newlines."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    parts = re.split(r"[\n,;]+", str(raw))
    return [p.strip() for p in parts if p.strip()]


def _num(raw):
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def next_rule_id(existing_rules, prefix: str = "DQ") -> str:
    nums = []
    for e in existing_rules:
        m = re.match(rf"^{prefix}(\d+)$", str(e.get("rule_id", "")))
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    return f"{prefix}{n:02d}"


def _params_signature(params: dict) -> str:
    import json
    norm = {}
    for k, v in (params or {}).items():
        norm[k] = sorted(str(x) for x in v) if isinstance(v, list) else v
    return json.dumps(norm, sort_keys=True, default=str)


# --------------------------------------------------------------------------
# Param validation, per control type
# --------------------------------------------------------------------------
def validate_params(report: ValidationReport, control_type: str, params: dict,
                    dataset_scope: str, ref_dataset_scope, datasets_config: dict,
                    dataset_columns: dict) -> None:
    cols = dataset_columns.get(dataset_scope)
    ref_cols = dataset_columns.get(ref_dataset_scope) if ref_dataset_scope else None

    def check_col(fname, value, columns, ds_label):
        if not value:
            report.add("error", fname, "param_required",
                       f"The '{fname}' parameter is required for a {control_type} control.")
            return
        if columns is not None and value not in columns:
            report.add("error", fname, "unknown_column",
                       f"Column '{value}' is not present in dataset '{ds_label}' "
                       f"(columns detected: {', '.join(columns)}).")

    if control_type == "Completeness":
        check_col("field", params.get("field"), cols, dataset_scope)

    elif control_type == "Validity":
        check_col("field", params.get("field"), cols, dataset_scope)
        av = parse_list(params.get("allowed_values"))
        modes = []
        if av:
            modes.append("allowed_values")
        if params.get("regex"):
            modes.append("regex")
        if params.get("min_val") not in (None, "") or params.get("max_val") not in (None, ""):
            modes.append("range")
        if not modes:
            report.add("error", "params", "validity_no_mode",
                       "Define a validity criterion: allowed value list, regular expression, "
                       "or min/max range.")
        elif len(modes) > 1:
            report.add("error", "params", "validity_many_modes",
                       f"Only one validity criterion at a time (got: {', '.join(modes)}).")
        if "regex" in modes:
            try:
                re.compile(params["regex"])
            except re.error as exc:
                report.add("error", "regex", "bad_regex",
                           f"Invalid regular expression: {exc}.")
            if str(params.get("regex")) in (".*", ".+", "^.*$", "^.+$"):
                report.add("warning", "regex", "permissive_regex",
                           "This regex accepts almost anything: the control will filter nothing.")
        if "allowed_values" in modes and len(av) == 1:
            report.add("warning", "allowed_values", "single_value",
                       "Only one allowed value: check that this is intended.")
        if "range" in modes:
            lo, hi = _num(params.get("min_val")), _num(params.get("max_val"))
            if params.get("min_val") not in (None, "") and lo is None:
                report.add("error", "min_val", "not_numeric", "min_val must be a number.")
            if params.get("max_val") not in (None, "") and hi is None:
                report.add("error", "max_val", "not_numeric", "max_val must be a number.")
            if lo is not None and hi is not None and lo > hi:
                report.add("error", "min_val", "range_inverted",
                           "min_val must be less than or equal to max_val.")

    elif control_type == "Uniqueness":
        keys = parse_list(params.get("keys"))
        if not keys:
            report.add("error", "keys", "param_required",
                       "Provide at least one key column for the uniqueness control.")
        if len(keys) != len(set(keys)):
            report.add("error", "keys", "duplicate_keys",
                       "The key list contains duplicates.")
        if cols is not None:
            for k in keys:
                if k not in cols:
                    report.add("error", "keys", "unknown_column",
                               f"Key column '{k}' is not present in dataset '{dataset_scope}'.")

    elif control_type == "Consistency":
        check_col("field", params.get("field"), cols, dataset_scope)
        if not ref_dataset_scope:
            report.add("error", "ref_dataset_scope", "param_required",
                       "A consistency control requires a reference dataset.")
        elif ref_dataset_scope not in datasets_config:
            report.add("error", "ref_dataset_scope", "unknown_dataset",
                       f"The reference dataset '{ref_dataset_scope}' is not declared "
                       f"in datasets_config.yaml.")
        check_col("ref_field", params.get("ref_field"), ref_cols, ref_dataset_scope or "?")
        if ref_dataset_scope and ref_dataset_scope == dataset_scope:
            report.add("warning", "ref_dataset_scope", "self_reference",
                       "The reference dataset is identical to the controlled dataset.")

    elif control_type == "Timeliness":
        check_col("field", params.get("field"), cols, dataset_scope)
        lag = params.get("max_lag_days")
        try:
            if int(lag) <= 0:
                report.add("error", "max_lag_days", "non_positive",
                           "max_lag_days must be a strictly positive integer (days).")
        except (TypeError, ValueError):
            report.add("error", "max_lag_days", "not_int",
                       "max_lag_days must be an integer (number of days).")
        rd = params.get("reference_date") or "today"
        if rd != "today":
            try:
                datetime.fromisoformat(str(rd))
            except ValueError:
                report.add("error", "reference_date", "bad_date",
                           "reference_date must be 'today' or an ISO date (YYYY-MM-DD).")

    elif control_type == "Reconciliation":
        check_col("key", params.get("key"), cols, dataset_scope)
        check_col("field", params.get("field"), cols, dataset_scope)
        if not ref_dataset_scope:
            report.add("error", "ref_dataset_scope", "param_required",
                       "A reconciliation control requires a reference dataset.")
        elif ref_dataset_scope not in datasets_config:
            report.add("error", "ref_dataset_scope", "unknown_dataset",
                       f"The reference dataset '{ref_dataset_scope}' is not declared "
                       f"in datasets_config.yaml.")
        check_col("ref_field", params.get("ref_field"), ref_cols, ref_dataset_scope or "?")
        if ref_cols is not None and params.get("key") and params.get("key") not in ref_cols:
            report.add("warning", "key", "key_absent_in_ref",
                       f"The key '{params.get('key')}' does not exist in the reference dataset "
                       f"'{ref_dataset_scope}': the join will match nothing.")
        tol = _num(params.get("tolerance_pct"))
        if tol is None:
            report.add("error", "tolerance_pct", "not_numeric",
                       "tolerance_pct must be a number (0 to 100).")
        elif not 0 <= tol <= 100:
            report.add("error", "tolerance_pct", "out_of_range",
                       "tolerance_pct must be between 0 and 100.")


# --------------------------------------------------------------------------
# Validation of a full rule
# --------------------------------------------------------------------------
def validate_rule(rule: dict, existing_rules: list, datasets_config: dict,
                  dataset_columns: dict) -> ValidationReport:
    """
    rule            : flat dict, already parsed (params is a dict, threshold_pct float|None)
    existing_rules  : the rest of the catalogue (self excluded when editing)
    datasets_config : content of datasets_config.yaml (dict name -> meta)
    dataset_columns : dict name -> list of columns (or None if dataset unreadable)
    """
    r = ValidationReport()

    # --- Rule ID ---
    rid = (rule.get("rule_id") or "").strip()
    if not rid:
        r.add("error", "rule_id", "required", "Rule ID is required.")
    elif not RULE_ID_RE.match(rid):
        r.add("error", "rule_id", "format",
              "Rule ID: 2 to 20 characters (letters, digits, _ or -), starting with a "
              "letter. Example: DQ07.")
    if rid and any((e.get("rule_id") or "").strip().lower() == rid.lower() for e in existing_rules):
        r.add("error", "rule_id", "duplicate", f"Rule ID '{rid}' already exists in the catalogue.")

    # --- Control type ---
    ctype = (rule.get("control_type") or "").strip()
    if ctype not in CONTROL_TYPES:
        r.add("error", "control_type", "invalid",
              f"Invalid control type. Expected: {', '.join(CONTROL_TYPES)}.")

    # --- Required text fields ---
    for fname, (lo, hi) in REQUIRED_TEXT_FIELDS.items():
        val = (rule.get(fname) or "").strip()
        if not val:
            r.add("error", fname, "required", f"The '{fname}' field is required.")
        elif not lo <= len(val) <= hi:
            r.add("error", fname, "length",
                  f"The '{fname}' field must be between {lo} and {hi} characters (currently {len(val)}).")

    # --- Severity / frequency / output ---
    sev = (rule.get("severity") or "").strip()
    if sev not in SEVERITIES:
        r.add("error", "severity", "invalid", f"Invalid severity. Expected: {', '.join(SEVERITIES)}.")

    freq = (rule.get("frequency") or "").strip()
    if freq not in FREQUENCIES:
        r.add("error", "frequency", "invalid", f"Invalid frequency. Expected: {', '.join(FREQUENCIES)}.")

    otype = (rule.get("output_type") or "").strip()
    if not otype:
        r.add("error", "output_type", "required", "Output type is required.")
    elif otype not in OUTPUT_TYPE_SUGGESTIONS:
        r.add("info", "output_type", "non_standard",
              "Output type outside the standard list: check consistency with the reporting.")

    # --- Target dataset ---
    ds = (rule.get("dataset_scope") or "").strip()
    if not ds:
        r.add("error", "dataset_scope", "required", "Target dataset is required.")
    elif ds not in datasets_config:
        r.add("error", "dataset_scope", "unknown_dataset",
              f"Dataset '{ds}' is not declared in datasets_config.yaml "
              f"(declared: {', '.join(datasets_config) or 'none'}).")

    # --- Tolerance threshold ---
    tpct = rule.get("threshold_pct")
    if tpct in (None, ""):
        r.add("info", "threshold_pct", "no_threshold",
              "No tolerance threshold: the control fails on the first anomaly (binary mode).")
    else:
        t = _num(tpct)
        if t is None:
            r.add("error", "threshold_pct", "not_numeric", "The threshold must be a number (0 to 100).")
        elif not 0 <= t <= 100:
            r.add("error", "threshold_pct", "out_of_range", "The threshold must be between 0 and 100.")
        elif t > 5 and sev == "High":
            r.add("warning", "threshold_pct", "loose_critical",
                  "High tolerance threshold (> 5%) on a High severity control.")

    # --- Type-specific params ---
    if ctype in CONTROL_TYPES:
        validate_params(r, ctype, rule.get("params") or {}, ds,
                        (rule.get("ref_dataset_scope") or "").strip() or None,
                        datasets_config, dataset_columns)

    # --- Cross-field rules (warnings) ---
    if sev == "High" and freq in ("Weekly", "Monthly", "Quarterly", "On demand"):
        r.add("warning", "frequency", "critical_low_freq",
              "Critical control (High) run at low frequency: weak risk coverage.")

    sig = (ctype, ds, _params_signature(rule.get("params") or {}),
           (rule.get("ref_dataset_scope") or "").strip())
    for e in existing_rules:
        esig = (e.get("control_type"), e.get("dataset_scope"),
                _params_signature(e.get("params") or {}),
                (e.get("ref_dataset_scope") or "").strip())
        if sig == esig:
            r.add("warning", "params", "duplicate_control",
                  f"Possible duplicate: same logic as rule '{e.get('rule_id')}'.")
            break

    return r


# --------------------------------------------------------------------------
# Derivation of the auditor-readable columns (Appendix A.2)
# --------------------------------------------------------------------------
def derive_data_element(control_type: str, params: dict) -> str:
    if control_type == "Uniqueness":
        return ", ".join(parse_list(params.get("keys")))
    return str(params.get("field") or params.get("key") or "")


def derive_threshold_text(control_type: str, params: dict, threshold_pct) -> str:
    bits = []
    if control_type == "Reconciliation":
        bits.append(f"unit gap tolerated <= {params.get('tolerance_pct', 0)}%")
    if control_type == "Timeliness":
        bits.append(f"lag <= {params.get('max_lag_days', '?')} day(s)")
    if threshold_pct in (None, ""):
        bits.append("0 anomaly tolerated (binary)")
    else:
        bits.append(f"<= {threshold_pct}% of records in anomaly")
    return " ; ".join(bits)


def derive_logic_definition(control_type: str, params: dict,
                            dataset_scope: str, ref_dataset_scope: str) -> str:
    ds = dataset_scope or "<dataset>"
    ref = ref_dataset_scope or "<ref_dataset>"
    f = params.get("field", "<field>")
    if control_type == "Completeness":
        return (f"No row in {ds} where {f} is NULL or blank. "
                f"SQL: SELECT * FROM {ds} WHERE {f} IS NULL OR TRIM({f}) = '';")
    if control_type == "Validity":
        av = parse_list(params.get("allowed_values"))
        if av:
            lst = ", ".join(f"'{v}'" for v in av)
            return (f"{f} belongs to the allowed set. "
                    f"SQL: SELECT * FROM {ds} WHERE {f} NOT IN ({lst});")
        if params.get("regex"):
            return (f"{f} matches the pattern {params['regex']!r}. "
                    f"SQL: SELECT * FROM {ds} WHERE NOT regexp_matches({f}, '{params['regex']}');")
        lo = params.get("min_val", "-inf")
        hi = params.get("max_val", "+inf")
        return (f"{f} between {lo} and {hi}. "
                f"SQL: SELECT * FROM {ds} WHERE {f} < {lo} OR {f} > {hi};")
    if control_type == "Uniqueness":
        keys = ", ".join(parse_list(params.get("keys"))) or "<keys>"
        return (f"No duplicate on ({keys}). "
                f"SQL: SELECT {keys}, COUNT(*) FROM {ds} GROUP BY {keys} HAVING COUNT(*) > 1;")
    if control_type == "Consistency":
        rf = params.get("ref_field", "<ref_field>")
        return (f"Every {f} in {ds} exists in {ref}.{rf}. "
                f"SQL: SELECT s.* FROM {ds} s LEFT JOIN {ref} r ON s.{f} = r.{rf} "
                f"WHERE r.{rf} IS NULL;")
    if control_type == "Timeliness":
        lag = params.get("max_lag_days", "?")
        rd = params.get("reference_date", "today")
        base = "CURRENT_DATE" if rd == "today" else f"DATE '{rd}'"
        return (f"{f} is not older than {lag} day(s) relative to {rd}. "
                f"SQL: SELECT * FROM {ds} WHERE {f} < {base} - INTERVAL '{lag}' DAY;")
    if control_type == "Reconciliation":
        k = params.get("key", "<key>")
        rf = params.get("ref_field", "<ref_field>")
        tol = params.get("tolerance_pct", 0)
        return (f"Value of {f} reconciled between {ds} and {ref} (tolerance {tol}%). "
                f"SQL: SELECT * FROM {ds} s FULL OUTER JOIN {ref} r ON s.{k} = r.{k} "
                f"WHERE s.{k} IS NULL OR r.{k} IS NULL "
                f"OR ABS(s.{f} - r.{rf}) / NULLIF(r.{rf}, 0) * 100 > {tol};")
    return ""


def explain_plain_language(control_type: str, params: dict,
                           dataset_scope: str, ref_dataset_scope: str) -> str:
    ds = dataset_scope or "the dataset"
    ref = ref_dataset_scope or "the reference dataset"
    f = params.get("field", "the field")
    if control_type == "Completeness":
        return f"Every record in \"{ds}\" must have a value in \"{f}\"."
    if control_type == "Validity":
        av = parse_list(params.get("allowed_values"))
        if av:
            return f"\"{f}\" in \"{ds}\" must be one of: {', '.join(av)}."
        if params.get("regex"):
            return f"\"{f}\" in \"{ds}\" must match the format {params['regex']!r}."
        return (f"\"{f}\" in \"{ds}\" must be between "
                f"{params.get('min_val', '-inf')} and {params.get('max_val', '+inf')}.")
    if control_type == "Uniqueness":
        return f"No duplicate of ({', '.join(parse_list(params.get('keys')))}) in \"{ds}\"."
    if control_type == "Consistency":
        return (f"Every \"{f}\" in \"{ds}\" must match an existing record in \"{ref}\" "
                f"(referential integrity).")
    if control_type == "Timeliness":
        return (f"\"{f}\" in \"{ds}\" must not exceed "
                f"{params.get('max_lag_days', '?')} day(s) of lag.")
    if control_type == "Reconciliation":
        return (f"The value \"{f}\" in \"{ds}\" must match \"{ref}\" "
                f"within {params.get('tolerance_pct', 0)}%.")
    return ""
