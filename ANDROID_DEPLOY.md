# Android deployment

1. Upload the contents of this folder to a GitHub repository.
2. On Streamlit Community Cloud choose Create app, select the repository, `main`,
   and `app.py`.
3. In App Settings -> Secrets add:
   SPORTMONKS_TOKEN = "YOUR_LICENSED_TOKEN"
4. Never commit `.streamlit/secrets.toml` or an API token.
5. Open the resulting `https://*.streamlit.app` URL in Chrome on Android.
6. Chrome -> menu -> Add to Home screen.

`requirements.txt` is included at the repository root for Community Cloud.
