# DQ Compass — architecture & design

## 1. The four layers

```
                         ┌───────────────────────────────────────────────┐
  control_catalogue.csv  │  [1] CONTROL CATALOGUE  — DEFINES              │
  (20 columns: 14 A.2    │      one row per rule; 6 DQ dimensions;        │
   attributes + params,  │      params drive behaviour, no rule in code  │
   threshold_pct, active,└───────────────────────┬───────────────────────┘
   regulatory_ref, …)                            │  validated by
                                                 │  rule_authoring/schema.py
  datasets_config.yaml    ── connectors.py ──────┤  before it is saved
  (per-source: type,         (CSV, Excel impl.;  │
   status, config)            JSON/SQL/URL       │
                              preview)           ▼
                         ┌───────────────────────────────────────────────┐
                         │  [2] DATA QUALITY ENGINE  — EXECUTES          │
  controls.py            │      dq_engine.py reads the catalogue, loads  │
  (6 generic functions,  │      each source, dispatches by control_type, │
   one per dimension)    │      applies threshold_pct, skips inactive    │
                         └───────────────────────┬───────────────────────┘
                                                 │ writes
                        ┌────────────────────────┴───────────────────────┐
                        ▼                                                ▼
       ┌─────────────────────────────────┐        ┌──────────────────────────────┐
       │ [4] AUDIT LAYER — EVIDENCES     │        │ [3] REPORTING LAYER — REPORTS │
       │ evidence/<run_id>/              │        │ reporting/scorecard.py        │
       │   run_summary.json (hash-chain) │        │   scorecard.csv / .html       │
       │   <rule>_result.json            │        │   exceptions_detail.csv       │
       │   <rule>_exceptions.csv         │        │   coverage.csv                │
       │   snapshots/<dataset>.csv       │        │   exception_summary.csv       │
       │   system_trace.json             │        │   dataset_score.csv           │
       │   run_log.jsonl / run.log       │        │   trend.csv / alerts.json     │
       │   verification.json (on verify) │        │ mapping.py                    │
       │   signoff.json (on sign-off)    │        │   supervisory_mapping.csv (C) │
       │ evidence/runs_ledger.jsonl      │        └──────────────────────────────┘
       └─────────────────────────────────┘
```

`rule_authoring/` is the web app over the catalogue, the data source registry and
the audit trails. `cli.py` (`dqcompass`) is the same capabilities for a pipeline.

## 2. Data flow of one run

1. `DQEngine` loads `control_catalogue.csv` and `datasets_config.yaml`.
2. For each **active** rule: load its dataset via the connector, hash it
   (SHA-256) and **snapshot it** to `snapshots/<name>.csv`; call the generic
   control function for its `control_type`; apply `threshold_pct`.
3. Write `<rule>_result.json` (status, metrics, config snapshot, resolved
   execution parameters, dataset hashes) and `<rule>_exceptions.csv`.
4. Write `system_trace.json` (engine / Python / library versions, host, file
   hashes, control function per rule).
5. Build `run_summary.json`, compute `run_hash = sha256(previous_run_hash +
   canonical(summary))`, append `runs_ledger.jsonl`.

`dqcompass verify <run_id>` re-executes step 2 from the **stored config and
stored snapshots** and asserts status + exception counts are unchanged
(independent verification).

## 3. Evidence Pack — contents

| B.2 component | Where |
|---|---|
| Run ID, Execution Timestamp | `run_summary.json`, every `<rule>_result.json` |
| Dataset Reference (version / snapshot / hash) | dataset SHA-256 in each result + `snapshots/<name>.csv` |
| Rule Configuration | `rule_configuration_snapshot` in each result |
| Execution Parameters | `execution_parameters` (resolved: e.g. `reference_date_resolved`) |
| Control Results (pass/fail, KPI values) | `status` + `metrics` |
| Exception Dataset | `<rule>_exceptions.csv` |
| Logs (processing steps) | `run_log.jsonl` + `run.log` |
| System Trace | `system_trace.json` |
| Sign-off Fields | `signoff.json` (recorded from the Runs page) |

## 4. Governance model

- **Catalogue integrity** — every rule is validated (`rule_authoring/schema.py`)
  before it enters the CSV: unique/well-formed id, controlled vocabularies,
  dataset declared, columns present (probed), params consistent per type.
- **Change history** — `catalogue_changelog.jsonl` and
  `data_sources_changelog.jsonl` are append-only and **hash-chained** (each entry
  carries the SHA-256 of the file before/after). The catalogue state at any past
  date is reconstructible.
- **Data source lifecycle** — retire (reversible soft delete, cascades to
  deactivate dependent rules), purge (permanent; rule definitions kept),
  rename (retargets `dataset_scope` on dependent rules in one logged transaction).
- **Run history** — `runs_ledger.jsonl` chains every run; a rule pointing at a
  missing/retired source yields a `status: ERROR` record and the run continues.
- **Supervisory mapping** — `mapping.py` generates the supervisory-requirement table
  (Requirement → Control → Evidence → Output → last run + hash) from the
  catalogue's `regulatory_ref` column (default per dimension when blank).

## 5. Limitations & scalability

**Limitations (prototype scope)**
- Connectors implemented: CSV and Excel. JSON / SQL / SharePoint are shown as
  selectors and saved with `status: preview`; the engine skips them.
- Evidence is local files. Production would point `evidence/` at versioned WORM
  storage (S3 Object Lock / immutable data-lake prefix); the engine records this
  intent in `system_trace.json` (`retention_note`).
- The engine executes rules sequentially with pandas in memory.
- The traffic-light per rule is pass/fail; `dataset_score.csv` adds a
  severity-weighted composite score but there is no run-over-run alerting yet
  beyond `trend.csv`.
- No built-in scheduler — `dqcompass run` is meant to be called by cron / Airflow
  (see `docs/DEPLOYMENT.md`).

**Scalability by design**
- New EUC / dataset = one entry in `datasets_config.yaml`; new rule = one row in
  `control_catalogue.csv`. No engine code changes.
- New source type = one connector class in `connectors.py` (implements
  `load` / `probe` / `validate`); the engine, catalogue and reporting are
  untouched.
- New control type = one function in `controls.py` + one registry entry.
- The generic control functions take only column names, so one function serves
  any field of any dataset.
- Path to volume: swap the pandas execution in `controls.py` for a push-down
  backend (DuckDB / SQL) behind the same function signatures; the catalogue,
  evidence format and reporting stay identical.
