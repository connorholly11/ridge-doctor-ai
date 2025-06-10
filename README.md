# ⚡ Quick MD Helper

A lightweight clinical decision-support tool for licensed clinicians. Provides evidence-based summaries in ≤5 bullet points.

## Quick Start

### Local Development

1. Clone this repository
2. Copy `.env.example` to `.env` and add your OpenAI API key
3. Install dependencies: `pip install -r requirements.txt`
4. Run locally: `streamlit run app.py`

### Deploy to Streamlit Community Cloud

1. Fork this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy this app
5. In Streamlit Cloud settings, add your `OPENAI_API_KEY` as a secret

### Deploy to Render

1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT`
4. Add `OPENAI_API_KEY` environment variable

### Deploy to Railway

1. Create a new project on [Railway](https://railway.app)
2. Deploy from GitHub repo
3. Add `OPENAI_API_KEY` environment variable
4. Railway will auto-detect Streamlit and deploy

## Features

- **3 Clinical Tasks**: Treatment, Confirmatory Tests, Differential Diagnosis
- **Template Buttons**: Common presentations for quick access
- **Guideline Citations**: References ≥2022 guidelines when available
- **Copy-friendly Output**: Results in code blocks with copy button
- **Safety First**: Built-in disclaimers and PHI warnings

## Important Notes

- For licensed clinicians only
- Not for diagnosis
- No PHI allowed
- Clinical judgment required

## Customization

Edit `common_cases.json` to add your own template cases.