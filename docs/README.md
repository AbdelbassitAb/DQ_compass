# docs/

| File | What it is |
|---|---|
| `ARCHITECTURE.md` | The four layers, the data flow of one run, the Evidence Pack, the governance model, limitations & scalability. |
| `DEPLOYMENT.md` | Running the engine from cron / Airflow, the CI quality gate, notifications. |
| `build_*.py` / `build_*.js` | Generators for the datathon slide decks and explanatory PDFs. **Not part of the product.** They need `reportlab` (PDF) or `npm i pptxgenjs` (decks); output is git-ignored (`docs/*.pdf`, `docs/*.pptx`). |
