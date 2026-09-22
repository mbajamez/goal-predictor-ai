import os, time, re, requests

class SportmonksClient:
    def __init__(self, token=None, timeout=20):
        self.token = token or os.getenv("SPORTMONKS_TOKEN")
        if not self.token:
            try:
                import streamlit as st
                self.token = st.secrets.get("SPORTMONKS_TOKEN")
            except Exception:
                pass
        if not self.token:
            raise RuntimeError("SPORTMONKS_TOKEN is not configured in Streamlit Secrets.")
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "GoalPredictAI/1.1",
            # Header auth avoids putting the secret in exception URLs/logs.
            "Authorization": self.token,
        })

    def _redact(self, text):
        text = str(text)
        if self.token:
            text = text.replace(self.token, "[REDACTED]")
        text = re.sub(r"([?&]api_token=)[^&\\s]+", r"\\1[REDACTED]", text)
        return text

    def _get(self, path, params=None, retries=3):
        params = dict(params or {})
        # Sportmonks supports header authentication; don't place the token in URLs.
        last = None
        for attempt in range(retries):
            try:
                r = self.session.get(
                    f"{self.base_url}/{path.lstrip('/')}",
                    params=params,
                    timeout=self.timeout,
                )
                if r.status_code == 429:
                    retry_after = r.headers.get("Retry-After", "2")
                    try:
                        delay = min(int(retry_after), 15)
                    except ValueError:
                        delay = 2
                    time.sleep(delay)
                    continue
                if r.status_code in (401, 403):
                    detail = ""
                    try:
                        body = r.json()
                        detail = body.get("message") or body.get("error") or ""
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Sportmonks rejected the request ({r.status_code}). {detail}".strip()
                    )
                if r.status_code == 404:
                    detail = ""
                    try:
                        body = r.json()
                        detail = body.get("message") or body.get("error") or ""
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Sportmonks endpoint returned 404 Not Found. {detail}".strip()
                    )
                r.raise_for_status()
                return r.json()
            except RuntimeError:
                raise
            except requests.RequestException as e:
                last = self._redact(e)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Sportmonks request failed: {self._redact(last)}")
