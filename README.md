# AI Debate Stage

A lightweight Streamlit front-end for a multi-model AI debate application.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the displayed local URL.

## Hosting

This is deliberately a small Python/Streamlit app. It can be deployed easily to Streamlit Community Cloud, Hugging Face Spaces (Streamlit), or a normal Python container/server.

The current UI has no API calls. The `Start Debate` action is the integration point for the later orchestration/backend layer.

## Planned backend shape

Each participant should receive a dedicated system prompt:

- Analyst — evidence, nuance, definitions
- Advocate — argues FOR
- Skeptic — argues AGAINST
- Contrarian — challenges assumptions and both sides
- Judge (Gemini) — neutral scoring and final verdict

Debate style and round count are already exposed in the UI.

