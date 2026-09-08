# DQ Compass — deployment & industrialisation

## Install

```bash
pip install -e .          # exposes the `dqcompass` command
# or, without packaging:
pip install -r requirements.txt
```

## The `dqcompass` command

| Command | Purpose |
|---|---|
| `dqcompass run` | execute the catalogue, write `evidence/<run_id>/` |
| `dqcompass verify <run_id>` | re-execute a past run from its snapshots, assert identical results |
| `dqcompass report` | (re)generate the Reporting Layer CSVs + `alerts.json` |
| `dqcompass mapping` | write `reporting/supervisory_mapping.csv` (Appendix C) |
| `dqcompass catalogue-validate` | validate every rule against the meta-catalogue (exit 1 on error) |
| `dqcompass gate --severity High` | run + exit 1 if any control at/above that severity broke |
| `dqcompass serve` | start the authoring web app on 127.0.0.1:5001 |

## Add the control layer to an existing EUC (3 lines)

Drop two files next to the EUC — `control_catalogue.csv` and `datasets_config.yaml` —
then, at the end of the EUC's pipeline:

```python
from dq_engine import DQEngine
summary = DQEngine("control_catalogue.csv", "datasets_config.yaml", "evidence").run()
assert not any(r["status"] in ("FAIL", "ERROR") and r["severity"] == "High"
               for r in summary["results"]), "High-severity DQ control broke"
```

No engine code is touched to onboard a new EUC: a new dataset is one entry in
`datasets_config.yaml`, a new rule is one row in `control_catalogue.csv`.

## Scheduling

**cron** (daily 06:00, run + report):

```cron
0 6 * * *  cd /opt/euc/orders && dqcompass run && dqcompass report
```

**Airflow**:

```python
from airflow.operators.bash import BashOperator
run_dq  = BashOperator(task_id="dq_run",    bash_command="cd /opt/euc/orders && dqcompass run")
report  = BashOperator(task_id="dq_report", bash_command="cd /opt/euc/orders && dqcompass report")
run_dq >> report
```

**Windows Task Scheduler**: action = `dqcompass`, arguments = `run`, start-in = the EUC folder.

## CI gate (fail the build on a High-severity break)

`.github/workflows/dq.yml`:

```yaml
name: Data Quality
on: [push, pull_request]
jobs:
  dq:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e .
      - run: dqcompass catalogue-validate
      - run: dqcompass gate --severity High
```

## Notifications

`dqcompass report` writes `reporting/alerts.json` — one entry per failing
High-severity control, carrying `owner`, `exception_count` and the
`remediation_action` from the catalogue. Wire it to a channel:

```python
import json, urllib.request
for a in json.load(open("reporting/alerts.json")):
    text = f":red_circle: {a['rule_id']} {a['control_name']} — {a['exception_count']} exception(s) " \
           f"on `{a['dataset_scope']}` (owner {a['owner']}). Action: {a['remediation_action']}"
    urllib.request.urlopen(urllib.request.Request(
        WEBHOOK_URL, data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"}))
```

## Retention

The prototype writes local files under `evidence/`. In production, point
`evidence/` at versioned WORM storage (S3 Object Lock, an immutable data-lake
prefix) so the Evidence Pack and the hash-chained `runs_ledger.jsonl` cannot be
altered after the fact. The engine already records a `retention_note` to this
effect in every `system_trace.json`.
