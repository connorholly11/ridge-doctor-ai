Done! Here's how to run locally and deploy:

  🚀 Running Locally

  1. Set up your API key:
  cp .env.example .env
  # Edit .env and add your OpenAI API key
  2. Install dependencies:
  pip install -r requirements.txt
  3. Run the app:
  streamlit run app.py

  The app will open at http://localhost:8501

  📦 Deployment Options

  Option 1: Streamlit Community Cloud (Easiest)

  1. Go to https://share.streamlit.io
  2. Sign in with GitHub
  3. Click "New app"
  4. Select your repo:
  connorholly11/ridge-doctor-ai
  5. Branch: main, Main file: app.py
  6. Click "Deploy"
  7. In app settings, add your OPENAI_API_KEY as a
  secret