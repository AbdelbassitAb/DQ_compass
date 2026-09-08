# DQ Compass — Plug-and-play data quality control layer

MVP prototype answering the "MBA-ESG / SG GSC Datathon" use case: a generic,
reusable and auditable data quality control layer, pluggable into any EUC
without writing new code.

## Architecture (mapped onto the use case, section 4)

```
control_catalogue.csv          -> [1] Control Catalogue   (DEFINES)
rule_authoring/  (web app)     -> catalogue + data source authoring & validation
connectors.py                  -> data source connector abstraction (CSV, Excel, ...)
datasets_config.yaml           -> data source registry (separation of concerns)
controls.py + dq_engine.py     -> [2] Data Quality Engine  (EXECUTES)
reporting/scorecard.py + mapping.py -> [3] Reporting Layer (REPORTS + Appendix C)
evidence/<run_id>/...           -> [4] Audit Layer         (EVIDENCES, Appendix B)
evidence/runs_ledger.jsonl     -> hash-chained run history
catalogue_changelog.jsonl      -> catalogue audit log (append-only, hash-chained)
data_sources_changelog.jsonl   -> data source audit log (append-only, hash-chained)
cli.py (`dqcompass`)           -> the same capabilities for a pipeline / CI
```

Definition -> Execution -> Reporting -> Audit: the 4 lifecycle stages required
by the brief are covered end to end. See `docs/ARCHITECTURE.md` and
`docs/DEPLOYMENT.md`.

## Audit Layer — Evidence Pack per run (Appendix B)

`dq_engine.py` writes `evidence/<run_id>/`:

| File | Appendix B.2 component |
|---|---|
| `run_summary.json` | run id, timestamps, catalogue/config hashes, per-rule results, `run_hash` chained from the previous run |
| `<rule>_result.json` | status, metrics, **rule config snapshot**, **resolved execution parameters**, dataset hashes |
| `<rule>_exceptions.csv` | detailed failing records |
| `snapshots/<name>.csv` | an exact copy of every input dataset used |
| `system_trace.json` | engine / Python / library versions, host, file hashes, control function per rule |
| `run_log.jsonl` + `run.log` | ordered processing steps |
| `verification.json` | written by `dqcompass verify <run_id>` |
| `signoff.json` | written from the Runs page |

`evidence/runs_ledger.jsonl` chains every run (`previous_run_hash -> run_hash`),
so the run history is append-only and tamper-evident.

**Independent verification** (section 7.3): `dqcompass verify <run_id>`
re-executes the stored rule configuration against the stored dataset snapshots
and asserts identical status + exception counts.

## Reporting Layer (section 4.3, Appendix C)

`reporting/scorecard.py` writes, from the latest run:
`scorecard.csv` / `.html`, `exceptions_detail.csv`, `coverage.csv`,
`exception_summary.csv`, `dataset_score.csv` (severity-weighted composite),
`trend.csv` (from the ledger), `alerts.json` (failing High-severity controls +
remediation action).

`mapping.py` writes `supervisory_mapping.csv` — Appendix C.2/C.3:
Requirement -> Control -> Evidence -> Output -> last run (id + hash), with the
requirement taken from each rule's `regulatory_ref` (default per DQ dimension).

The web app surfaces all of this: **Runs** (run history, per-run drill-down,
verify + sign-off, embedded reporting) and **Mapping** (the Appendix C table).

## `dqcompass` CLI

```bash
pip install -e .
dqcompass run                     # execute, write the Evidence Pack
dqcompass verify <run_id>         # prove a past run is reproducible
dqcompass report                  # (re)generate the Reporting Layer files
dqcompass mapping                 # write reporting/supervisory_mapping.csv
dqcompass catalogue-validate      # validate every rule (exit 1 on error)
dqcompass gate --severity High    # run + exit 1 if a High-severity control broke (CI)
dqcompass serve                   # start the web app
```

## How it works

1. `control_catalogue.csv` has one column per Appendix A.2 attribute (Rule ID,
   Control Name, Control Type, Description, Logic Definition, Dataset Scope,
   Data Element, Threshold, Severity, Frequency, Owner, Output Type, KPI,
   Remediation Action) + technical columns: `ref_dataset_scope`, `params`
   (generated JSON: fields, thresholds, allowed values…), `threshold_pct`,
   `active`, `created_at`, `updated_at`. `logic_definition`, `data_element`
   and `threshold` are **generated** on save by the authoring interface (see
   below).
2. `datasets_config.yaml` declares where to find each dataset. This file is
   what makes the brief's "Separation of Concerns" principle real: the engine
   never knows *where* the data is until it is told.
3. `dq_engine.py` reads the catalogue row by row, loads the required
   datasets, calls the generic function matching the `control_type` (in
   `controls.py`), and writes a complete Evidence Pack per run in
   `evidence/<run_id>/`.
4. `reporting/scorecard.py` turns the latest run into a traffic-light
   scorecard (CSV for Power BI + HTML for a quick demo) and a consolidated
   exceptions view with record-by-record drill-down.

## Catalogue authoring interface (`rule_authoring/`)

A local web app to **create and edit the business rules without editing the
CSV by hand**, with a dedicated validation engine — a "catalogue of rules
that validates the rules".

```bash
pip install -r requirements.txt
python migrate_catalogue.py     # once: brings the CSV to the 20-column schema
python migrate_sources.py       # once: rich per-source datasets_config.yaml
python run_authoring.py         # http://127.0.0.1:5001
```

App shell — a sidebar with eight sections:

| Section | What it shows |
|---|---|
| **Home** | dashboard: rule/source health tiles, latest engine run (pass/fail/error donut), a "needs attention" list (validation errors, probe failures, retired sources with live dependents), the coverage heatmap, recent activity |
| **Catalogue** | the rules as filterable list items (search + state + control-type chips), each expandable to its logic, issues, owner/KPI/remediation |
| **Data Sources** | one card per source: connector, status, plain-language summary, "used by" rule chips, retire / reactivate / rename / purge |
| **Runs** | run history + per-run Evidence Pack drill-down, Verify this run, sign-off |
| **Reporting** | cross-run analytics with an audience filter (All / Control owners & risk / Data engineers): composite DQ score + trend, dataset-health ranking, 3-state coverage matrix, open High-severity issues, exceptions by owner / dimension / rule, rule-reliability, run-over-run diff. Dependency-free inline-SVG charts; Power-BI-ready downloads |
| **Mapping** | the Appendix C.2/C.3 supervisory mapping + the C.4 principles |
| **Activity** | unified append-only audit timeline across the catalogue and the data source registry |
| **Help** | field reference (`/docs`) |

Light / dark theme toggle in the top bar (persisted in `localStorage`).

What it brings:

- **Dynamic form per control type**: the parameters shown adapt to the chosen
  `control_type` (field, keys, ref_field, regex, min/max, max_lag_days,
  tolerance_pct…). The user never types JSON; the engine's `params` field is
  generated.
- **Contextual help**: required fields marked `*`, a `?` icon on hover of each
  field (tooltip) linked to a **documentation page** (`/docs`) that details
  the 14 attributes, the 6 control types and their parameters, the meaning of
  each `output_type` / `severity` / `frequency`, the tolerance threshold and
  the validation rules.
- **Validation before saving** (`rule_authoring/schema.py`), at two levels:
  - *blocking errors*: unique and well-formed Rule ID, required fields,
    controlled vocabularies (type, severity, frequency), `dataset_scope`
    declared in `datasets_config.yaml`, **columns actually present in the
    target dataset** (checked on a sample), param consistency per type (e.g.
    Validity = exactly one criterion among list / regex / range; a regex that
    compiles; `tolerance_pct` in [0, 100]…);
  - *warnings*: critical control at low frequency, logic duplicated with an
    existing rule, high tolerance threshold on a High control, self-reference,
    overly permissive regex…
- **Generated auditor-readable columns** (Appendix A.2): `logic_definition`
  (pseudo-SQL), `data_element`, `threshold`, + a plain-language explanation —
  shown as a live preview in the form.
- **Coverage matrix** datasets × 6 DQ dimensions (the brief's "control
  coverage view", 4.3) + catalogue health indicators.
- **Catalogue audit log** (`catalogue_changelog.jsonl`, append-only): every
  create / update / delete / (de)activate is tracked with the editor, the
  timestamp, the before/after and the **SHA-256 hash of the catalogue before
  and after**. The catalogue state at any past date is reconstructible —
  governance and auditability (Appendix C).
- **Deactivation without deletion** (`active=FALSE`): a rule removed from the
  execution scope stays in the catalogue and the history.

The engine (`dq_engine.py`) consumes the same CSV: it skips `active=FALSE`
rules and applies the `threshold_pct` column (if the anomaly rate stays below
the threshold, the control passes and is marked `within_threshold`).

## Data sources (`connectors.py` + the "Data Sources" page)

Each rule targets a named data source declared on the **Data Sources** page and
stored in `datasets_config.yaml` with a connector `type`, a `status` and a
connector-specific `config`.

| Connector | Status | Config |
|---|---|---|
| **CSV file** | implemented | `path`, `delimiter` (incl. `\t`), `header_row`, encoding, quotechar, skip_rows |
| **Excel file** | implemented | `path`, `sheet`, `header_row`, skip_rows, nrows (needs `openpyxl`) |
| **JSON file** | preview | `path`, `orient`, `lines`, `record_path` |
| **SQL database** | preview | `driver`, `host`, `port`, `database`, `schema`, `username`, `password`, `table` / `query` |
| **SharePoint / Drive / URL** | preview | `url`, `auth`, `token`, `format` |

*Preview* connectors show the full field form (for the demo) but do not run:
they are saved with `status: preview` and skipped by the engine. Credentials on
preview connectors are used only to render the form shape.

The "New data source" form has a connector picker, progressive fields (advanced
options collapsed), and a **Test connection** button that previews the detected
columns and first rows — the same probe the catalogue validation uses to check
that a rule cannot reference a column its source does not expose.

**Delete policy** (data source audit log records every step, hash-chained):

- **Retire** — reversible soft delete. `status -> retired`; dependent rules are
  auto-deactivated and can be brought back with one click.
- **Purge** — permanent removal from the registry (typed `PURGE` confirmation).
  Dependent rule *definitions* are never deleted, only deactivated.
- **Rename** — rewrites `dataset_scope` / `ref_dataset_scope` on every dependent
  rule in one logged transaction.
- A rule pointing at a missing / retired source **does not crash the run**: it
  produces a `status: ERROR` record in the evidence pack and execution
  continues.

`migrate_sources.py` brings a flat legacy `datasets_config.yaml` to the rich
per-source schema (the engine reads both).

Tests: `python tests/test_schema.py`, `python tests/test_connectors.py`,
`python tests/test_engine.py` (or `python -m pytest tests/`).

## Why it is scalable / plug-and-play

- **Add a new dataset (new EUC)**: register it on the Data Sources page (CSV /
  Excel / …). Zero lines of code changed. A new *connector type* is one class
  in `connectors.py`.
- **Add a new rule on an existing dataset**: one line in
  `control_catalogue.csv`. Zero lines of code changed.
- **Add a new control type** (rare): one function in `controls.py` + one
  entry in `CONTROL_REGISTRY`. The engine, the reporting and the audit do not
  change.
- The 6 functions in `controls.py` are **fully generic**: none knows the name
  of a dataset or a project, only column names passed as parameters. The same
  `check_completeness` serves any field of any dataset, indefinitely.

## Why it is auditable (Appendix B and C of the brief)

Every execution generates, with no manual intervention:
- a unique `run_id` and a UTC timestamp
- a SHA-256 hash of the exact content of each dataset used (proof that the
  data was not modified between execution and review)
- a full snapshot of the rule configuration used (params, thresholds,
  dataset scope)
- the result metrics (pass/fail + quantifiable KPIs)
- the detail of the failing records, exported as CSV

Two successive runs on the same data produce identical dataset hashes and the
same results: execution is **reproducible**, a condition explicitly required
by the brief (sections 7.1 and 7.3).

## Running

```bash
pip install pandas pyyaml
python dq_engine.py                  # runs the rules, generates the evidence pack
python reporting/scorecard.py        # generates scorecard.csv / .html / exceptions_detail.csv
```

## Known limitations (to mention in the documentation/presentation)

- CSV loading only in this prototype; plugging Excel/SQL/Alteryx output only
  needs a new `format` in `_load_dataset()` (planned extension, not a
  rewrite).
- Evidence storage is local (files); in production, `run_dir` would point to
  versioned storage (S3, data lake) for regulatory retention.
- The traffic-light scoring is currently binary (pass/fail per rule); a V2
  could compute a weighted composite score per dataset from severity and
  exception rate.
- No built-in scheduler (the catalogue's Frequency is declarative); in
  production, `dq_engine.py` would be called by an orchestrator (cron,
  Airflow).

## Sample dataset

`sample_data/orders.csv`, `sample_data/orders_reference.csv` and
`sample_data/customers.csv` simulate an EUC export of orders with deliberate
anomalies (missing amount, invalid status, duplicate, orphan customer, stale
order, reconciliation break) to demonstrate that the 6 dimensions do catch
real cases.
#   D Q _ c o m p a s s  
 