# FINN — Financial Investment Intelligence

A mobile-responsive Streamlit MVP for the ENAM AI Engineer Build Challenge.

## Features

- **Today:** end-of-day market watchlist and configurable unusual price/volume alerts using Yahoo Finance data.
- **Intelligence:** announcement feed from CSV, category classification, filtering, and Groq-generated investor briefs.
- **Research:** PDF ingestion, page-aware extraction, TF-IDF retrieval, and Groq answers grounded in retrieved primary-source excerpts with page citations.

> Prototype only. No trading, no real-time alerts, and no claim that the sample announcement rows are live exchange filings.

## Local setup (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...
streamlit run app.py
```

If `.env` already exists, edit it rather than overwriting it. Never commit secrets.

## Deploy on Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ using GitHub.
2. Create app → repository `sainiiitdtextile-hash/FINN`, branch `main`, main file `app.py`.
3. In app settings → Secrets, add:

```toml
GROQ_API_KEY = "gsk_your_real_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

4. Deploy. Do not put API keys in GitHub.

The Groq service reads credentials from Streamlit secrets in deployment and from `.env` locally.

## Announcement CSV schema

Required columns: `date,symbol,headline,details,source_url`. Optional: `category,priority`.

`data/announcements.csv` contains illustrative fixtures for testing, not live exchange filings. Replace with verified filings and source URLs for a live demonstration.

## Research workflow

Upload searchable annual reports or earnings-call transcripts as PDFs. PyMuPDF extracts text by page; TF-IDF ranks relevant pages; Groq receives only retrieved excerpts and is instructed to cite `[document, p. X]`. Scanned/image-only PDFs are not OCR-processed in this MVP.

## Known limitations

- NSE/BSE automated ingestion is not connected to a stable official feed; CSV ingestion is the reliable demo path.
- Yahoo Finance data can be delayed or unavailable.
- The portfolio is a watchlist, not a capital-weighted portfolio valuation; holdings quantities and cost basis are not modelled.
- Retrieval is lexical TF-IDF, not embeddings. Complex tables and scanned PDFs need dedicated OCR/table extraction and validation.
- Alerts are generated on refresh; no always-on scheduler or push notification service is included.
