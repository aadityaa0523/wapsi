---
title: Wapsi
sdk: docker
app_port: 7860
---

# Wapsi

Cyber-fraud recovery agent for Forge '26, Theme 1, Problem 3. Early scaffold: only the live status endpoint exists so far.

`GET /api/status` checks official sources live and returns the time, result and page hash of each check, plus whether each quoted rule clause is still on its source page. Results are cached for 5 minutes.

## Run locally

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --port 7860
```

## Configure

Set `DATABASE_URL` to a hosted Postgres URL. On Hugging Face Spaces, add it as a Space secret. See `.env.example`.
