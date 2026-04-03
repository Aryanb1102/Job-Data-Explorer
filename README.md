# Parikshak — Job Description Structuring Pipeline

## Overview
This take-home assignment for Parikshak converts unstructured public job descriptions into structured, queryable hiring data. It includes a lightweight scraper, a Gemini-powered extraction pipeline, and a minimal Streamlit dashboard for exploration.

## What this project does
- Collects raw job descriptions from public ATS sources (Greenhouse and Lever)
- Extracts structured fields (skills, seniority, remote type, etc.) using Gemini
- Outputs clean CSVs for analysis and review
- Provides a simple Streamlit UI for filtering and viewing results

## Project structure
- `scrape_jobs.py` — fetches raw job descriptions into `raw_jobs.csv`
- `jd_pipeline.py` — extracts structured data from `raw_jobs.csv` into `structured_jobs.csv`
- `app.py` — Streamlit dashboard for exploring `structured_jobs.csv`
- `raw_jobs.csv` — raw scraped job data
- `structured_jobs.csv` — structured output data
- `failed_jobs.csv` — rows that failed extraction

## How the pipeline works
1. **Scrape**: `scrape_jobs.py` hits public ATS APIs and stores raw job text in `raw_jobs.csv`.
2. **Extract**: `jd_pipeline.py` sends raw job text to Gemini and parses structured JSON.
3. **Explore**: `app.py` loads the structured data and provides basic filters and detail views.

## Setup instructions
1. Create a virtual environment (recommended):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Environment variables
Set your Gemini API key via environment variables only. **Do not hardcode keys** and **never commit keys to git**.

PowerShell:
```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
# or
$env:GOOGLE_API_KEY="YOUR_KEY_HERE"
```

**Security warning:**
- Do **not** hardcode API keys in code or notebooks.
- Do **not** commit or screenshot keys.
- Check commit history before pushing to ensure no key leakage.

> Note: Pre-generated outputs are already included in this repo. You only need an API key to rerun the extraction step.

## How to run the scraper
```powershell
python scrape_jobs.py
```

## How to run the extraction pipeline
```powershell
python jd_pipeline.py
```

## How to run the Streamlit dashboard
```powershell
python -m streamlit run app.py
```


## Output files
- `raw_jobs.csv` — raw scraped jobs
- `structured_jobs.csv` — structured extraction output
- `failed_jobs.csv` — failed extraction attempts with error notes

## Reproducing the results
1. Run the scraper to regenerate `raw_jobs.csv`.
2. Set your API key and run the extraction pipeline to regenerate `structured_jobs.csv` and `failed_jobs.csv`.
3. Launch the Streamlit app to explore results.

> Due to API quota limits, extraction was tested on a smaller processed subset even though the raw dataset is larger.

## Notes / limitations
- API quotas can limit extraction throughput.
- Extraction quality depends on the clarity of source job descriptions.
- Some ATS listings may be unavailable or intermittently fail.

## Future improvements
- Batch and parallel extraction with rate-limit handling
- Stronger validation and schema enforcement
- Add unit tests for normalization
- Optional database storage for larger datasets

## GitHub readiness
- Add `.env`, notebook checkpoints, cache files, and virtual environments to `.gitignore`.
- Review commit history for leaked secrets before pushing.

Loom walkthrough: https://www.loom.com/share/d8ced325fb254f3aaecfda32ffdf0bd3

---

Recommended `.gitignore` block:
```gitignore
# Environment variables
.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
venv/

# Jupyter
.ipynb_checkpoints/

# Streamlit
.streamlit/

# OS
.DS_Store
Thumbs.db

# Cache
.cache/
.pytest_cache/
```
