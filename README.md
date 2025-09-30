# RBA AUD Exchange Rates (4pm AEST)

This repo fetches **daily AUD-based exchange rates** from the Reserve Bank of Australia (official 4pm AEST print).  

It does 3 things:
1. **Parses the RBA XML feed** (no dependencies, pure Python stdlib).
2. **Publishes data** as JSON and a Plotly chart on GitHub Pages:
   - `rates-latest.json` → most recent day’s data
   - `history.json` → cumulative time series
   - `index.html` → interactive graph (choose any currency → AUD)
3. **Notifies downstream repos** (via GitHub `repository_dispatch`) when fresh rates are available.  

---

## 🔗 Works Together With

- **[rba-aud-rates-notion](https://github.com/taylorsudo/rba-aud-rates-notion) (Repo B)**: optional consumer.  
  - Repo A emits a webhook to Repo B when new data is ready.  
  - Repo B then writes the rates into a Notion database.  
  - If you don’t need Notion, ignore Repo B and just use the JSON/graph here.

---

## 📂 Live URLs (GitHub Pages)

- Latest JSON → `https://<owner>.github.io/rba-aud-rates/rates-latest.json`  
- History JSON → `https://<owner>.github.io/rba-aud-rates/history.json`  
- Chart UI → `https://<owner>.github.io/rba-aud-rates/`

---

## 🛠️ Setup

- Workflow: `.github/workflows/fetch.yml` runs daily (~07:05 UTC, after RBA 4pm AEST release).
- It commits updated JSON to `public/` and dispatches an event to Repo B.

### Secrets / Variables
- `REPO_B_TOKEN` → a PAT that allows Repo A to trigger Repo B.  
- `PAGES_BASE` → your GitHub Pages base URL (e.g. `https://<owner>.github.io/rba-aud-rates`).

---

## 🧰 Local Run

```bash
python3 scripts/fetch_rba.py
# Generates public/rates-latest.json + public/history.json
```