# DQ Compass

**A plug-and-play data-quality control layer for End-User Computing (EUC) applications.**

Point it at a spreadsheet or a CSV export, describe the checks once in a catalogue, and
get a reproducible quality score plus a tamper-evident audit trail on every run — without
writing validation code for each new file.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen)
![Dependencies](https://img.shields.io/badge/runtime%20deps-pandas%20%C2%B7%20pyyaml%20%C2%B7%20flask-lightgrey)

---

## The problem

Banks and large companies run critical numbers through **EUCs** — Excel workbooks, Access
databases, local scripts maintained by business teams, outside the governed IT systems.
They typically have no input validation, no audit trail, and no owner for data quality.
Regulators (notably **BCBS 239** on risk-data aggregation) expect firms to inventory these
tools and put controls around the material ones.

Rebuilding every workbook as a proper system is not realistic. DQ Compass takes the other
route: a **generic control layer you bolt on**, so an EUC reaches a governed standard with
no bespoke project.

## What it does

Four layers, matching the lifecycle *define → execute → report → evidence*:

| Layer | Component | Role |
|---|---|---|
| **1. Control Catalogue** | `control_catalogue.csv` + `rule_authoring/` web app | One row per rule. Parameters drive behaviour — **no rule logic in code**. Every rule is validated before it is saved. |
| **2. DQ Engine** | `dq_engine.py` + `controls.py` | Reads the catalogue, loads each source through a connector, dispatches by control type, applies tolerance thresholds. |
| **3. Reporting Layer** | `reporting/scorecard.py` + `mapping.py` | Severity-weighted composite score, coverage matrix, trend, alerts, and a supervisory-requirement mapping — all as Power BI–ready CSV. |
| **4. Audit Layer** | `evidence/<run_id>/` + hash-chained ledgers | A complete **Evidence Pack** per run: input snapshots, config snapshot, results, exceptions, logs, hashes. Independently re-verifiable. |

### The six data-quality dimensions

Each is one generic function in `controls.py` with the signature `fn(df, **params) → {status, metrics, exceptions}`:

| Dimension | Checks | Key parameters |
|---|---|---|
| **Completeness** | a field is populated | `field` |
| **Validity** | values match an allowed set, a regex, or a numeric range | `field` + one of `allowed_values` / `regex` / `range` |
| **Uniqueness** | no duplicate rows on a key | `keys` |
| **Consistency** | values reconcile against a reference table | `field`, `ref_field` (+ reference dataset) |
| **Timeliness** | data is not older than a lag threshold | `field`, `max_lag_days` |
| **Reconciliation** | amounts agree between two sources within a tolerance | `key`, `field`, `ref_field`, `tolerance_pct` (+ reference dataset) |

The functions take **only column names**. The same `check_completeness` serves any field of
any dataset — that is what makes the layer reusable.

---

## Quickstart

```bash
git clone https://github.com/AbdelbassitAb/DQ_compass.git
cd DQ_compass
pip install -r requirements.txt

# 1. load a demo catalogue: 5 data sources + 14 rules across all 6 dimensions,
#    each with an explicit passing and failing case
python demo_seed.py

# 2. run the engine — writes evidence/<run_id>/
python dq_engine.py

# 3. build the reporting files from the latest run
python reporting/scorecard.py latest

# 4. explore everything in the browser
python run_authoring.py            # http://127.0.0.1:5001
```

The web app has a sidebar with: **Home** (health dashboard), **Catalogue** (create/edit
rules with live validation), **Data Sources**, **Runs** (per-run Evidence Pack, *Verify*,
*Sign-off*), **Reporting**, **Mapping** (supervisory view), and **Activity** (audit
timeline).

### Or use the CLI

```bash
pip install -e .

dqcompass run                    # execute, write the Evidence Pack
dqcompass verify <run_id>        # prove a past run reproduces exactly
dqcompass report                 # (re)generate the Reporting Layer files
dqcompass mapping                # write the supervisory mapping
dqcompass catalogue-validate     # validate every rule   (exit 1 on error)
dqcompass gate --severity High   # run + exit 1 if a High-severity control broke (CI)
dqcompass serve                  # start the web app
```

---

## How it works

```
control_catalogue.csv ──┐
                        ├─► DQEngine ──► for each active rule:
datasets_config.yaml ───┘                  load source (connectors.py)
   (where each source lives)                hash + snapshot the exact input
                                            run controls.py function by control_type
                                            apply threshold_pct
                                            │
                                            ├─► evidence/<run_id>/   (Audit Layer)
                                            └─► reporting/*.csv      (Reporting Layer)
```

1. **`control_catalogue.csv`** holds one column per governance attribute (control name,
   type, description, logic definition, dataset scope, data element, threshold, severity,
   frequency, owner, output type, KPI, remediation, regulatory reference) plus technical
   columns (`params` JSON, `threshold_pct`, `active`, timestamps). The human-readable
   `logic_definition` (a neutral pseudo-SQL), `data_element` and `threshold` text are
   **generated** from the form when a rule is saved.
2. **`datasets_config.yaml`** declares where each dataset lives (connector type, status,
   config). The engine never knows *where* the data is until it is told — sources and rules
   evolve independently.
3. **`dq_engine.py`** walks the catalogue, skips `active = FALSE` rows, and for each rule
   applies `threshold_pct`: if the anomaly rate stays under the threshold the control
   passes and is flagged `within_threshold`.
4. **`reporting/scorecard.py`** turns the latest run into a traffic-light scorecard (CSV +
   a standalone HTML page) and a record-by-record exceptions view. **`mapping.py`** derives
   the supervisory table: *requirement → control → evidence → last run (id + hash)*.

## The audit layer

The differentiator. Every run produces `evidence/<run_id>/` with:

| File | Contents |
|---|---|
| `run_summary.json` | run id, timestamps, catalogue/config hashes, per-rule results, and `run_hash` |
| `<rule>_result.json` | status, metrics, **frozen rule-config snapshot**, resolved execution parameters, dataset hashes |
| `<rule>_exceptions.csv` | the failing rows |
| `snapshots/<name>.csv` | a byte-exact copy of every input dataset used |
| `system_trace.json` | engine / Python / library versions, host, file hashes, control function per rule |
| `run_log.jsonl` + `run.log` | ordered processing steps |
| `verification.json` | written by `dqcompass verify` — see below |
| `signoff.json` | written from the Runs page — reviewer, timestamp, decision, comment |

**Hash chain.** `run_hash = sha256(previous_run_hash + canonical_json(run_summary))[:16]`,
appended to `evidence/runs_ledger.jsonl`. Change one byte in an old run and its hash — and
every run after it — no longer matches. The run history is append-only and tamper-evident.
The catalogue and data-source change logs are chained the same way.

**Independent verification.** `dqcompass verify <run_id>` re-executes the *stored* rule
config against the *stored* snapshots and asserts the status and exception count are
identical. An auditor can re-derive the result from the folder alone, with no access to
your environment or live data.

**Sign-off.** A named person records a review decision (`acknowledged` / `accepted` /
`rejected` + a comment) on a run. The machine says the numbers are real; the human says who
accepts them.

---

## Project layout

```
control_catalogue.csv        the rules (one row each)
datasets_config.yaml         the data-source registry
controls.py                  6 generic control functions + CONTROL_REGISTRY
dq_engine.py                 the engine + verify_run()
mapping.py                   supervisory-requirement mapping
cli.py                       the `dqcompass` command
demo_seed.py                 loads a full demo catalogue + sample sources

rule_authoring/              Flask app: catalogue & source authoring, runs, reporting
  schema.py                    ~30 validation checks run before a rule is saved
  store.py / source_store.py   persistence + hash-chained change logs
  charts.py                    dependency-free inline-SVG charts
reporting/scorecard.py       scorecard, coverage, dataset score, trend, alerts
connectors.py                connector abstraction (CSV, Excel; JSON/SQL/URL preview)

sample_data/                 demo datasets (incl. a ~78k-row BIS derivatives extract)
evidence/                    Evidence Packs from example runs + runs_ledger.jsonl
tests/                       42 tests (schema, connectors, controls, engine)
docs/ARCHITECTURE.md         design & data flow
docs/DEPLOYMENT.md           cron / Airflow / CI-gate / notifications
docs/build_*.py|js           generators for the datathon slide decks & PDFs (optional)
```

## Tests

No pytest required — each file has a plain runner:

```bash
python tests/test_schema.py        # 21  meta-catalogue validation
python tests/test_connectors.py    # 11  connector config validation
python tests/test_controls.py      #  4  control-function edge cases
python tests/test_engine.py        #  6  evidence pack, ledger chain, verify, thresholds
```

`python -m pytest tests/` also works if pytest is installed.

## Tech stack & design decisions

- **Python 3.10+, pandas, PyYAML, Flask.** No database, no build step, no JS framework —
  the web app is server-rendered Jinja with a design-token stylesheet and one small
  vanilla-JS file; charts are inline SVG generated in Python. Clone and run.
- **Rules are data, the engine is generic.** Adding a rule is one CSV row; adding a data
  source is one registry entry; neither touches engine code. A new control type is one
  function plus one registry entry.
- **Neutral pseudo-SQL** in `logic_definition` (`regexp_matches`, `INTERVAL`, `NULLIF`) so
  the pandas execution in `controls.py` can later be swapped for a push-down backend
  (DuckDB / Spark) behind the same function signatures, with the catalogue, evidence
  format and reporting unchanged.
- **Everything auditable by construction** — no manual step produces the run id, the
  hashes, the snapshots or the config freeze.

## Limitations & roadmap

- Connectors implemented: **CSV and Excel**. JSON / SQL / SharePoint appear in the UI as
  selectors and are saved with `status: preview`; the engine skips them.
- Evidence is stored as local files. In production `evidence/` would point at versioned
  WORM storage (S3 Object Lock / immutable data-lake prefix); the engine already records
  this intent in `system_trace.json`.
- The engine runs rules sequentially with pandas in memory. The path to volume is the
  push-down backend described above.
- No built-in scheduler — `dqcompass run` is designed to be called by cron / Airflow
  (see `docs/DEPLOYMENT.md`).

---

<sub>Built for the MBA-ESG / SG GSC Datathon 2026 use case *“DQ Compass: building a
plug-and-play data quality control layer for EUCs.”* The `docs/build_*` scripts and the
generated decks are specific to that presentation and are not part of the product.</sub>
