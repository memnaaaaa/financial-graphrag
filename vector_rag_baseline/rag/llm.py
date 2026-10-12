import os
import time

import google.auth.transport.requests  # noqa: F401  (used by Gemini vertex path)


def _retry(fn, tries=5):
    for n in range(tries):
        try:
            return fn()
        except Exception as e:  # free tiers rate-limit; back off and retry
            msg = str(e).lower()
            if n == tries - 1 or not any(s in msg for s in ("429", "rate", "quota", "503", "overloaded", "unavailable")):
                raise
            time.sleep(min(60, 4 * 2**n))


def _gcloud_token() -> str:
    """Short-lived (1h) token from the user's company gcloud login."""
    import shutil
    import subprocess

    from . import config

    exe = config.GCLOUD_BIN or shutil.which("gcloud")
    if not exe:
        raise RuntimeError("gcloud not found; set GCLOUD_BIN in .env or run `gcloud auth application-default login`")
    out = subprocess.run([exe, "auth", "print-access-token"], capture_output=True, text=True, timeout=60)
    if out.returncode or not out.stdout.strip():
        raise RuntimeError("gcloud auth print-access-token failed; run `gcloud auth login`")
    return out.stdout.strip()


def _credentials():
    """Vertex creds: VERTEX_ACCESS_TOKEN env (1h token passed in at run time) > ADC > local gcloud login."""
    import google.auth
    import google.auth.transport.requests
    from google.oauth2.credentials import Credentials

    tok = os.getenv("VERTEX_ACCESS_TOKEN")
    if tok:
        return Credentials(tok.strip())
    try:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(google.auth.transport.requests.Request())
        return creds
    except Exception:
        return Credentials(_gcloud_token())


class Gemini:
    """Gemini via AI Studio key if GEMINI_API_KEY is set, else via company Vertex AI (GCP login)."""

    def __init__(self, model=None):
        from google import genai

        from . import config

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model or config.GEMINI_MODEL
        if key:
            self.client, self.backend = genai.Client(api_key=key), "ai-studio"
            return
        creds = _credentials()
        self.client = genai.Client(
            vertexai=True, project=config.GCP_PROJECT, location=config.GCP_LOCATION, credentials=creds
        )
        self.backend = "vertex"

    def generate(self, prompt: str, system: str | None = None) -> str:
        from google.genai import types

        cfg = types.GenerateContentConfig(temperature=0.0, system_instruction=system)
        r = _retry(lambda: self.client.models.generate_content(model=self.model, contents=prompt, config=cfg))
        return (r.text or "").strip()


class Groq:
    def __init__(self, model=None):
        from groq import Groq as _G

        from . import config

        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set (see .env.example)")
        self.client, self.model = _G(api_key=key), model or config.GROQ_MODEL

    def chat(self, system: str, user: str, json_mode=False) -> str:
        kw = {"response_format": {"type": "json_object"}} if json_mode else {}
        r = _retry(
            lambda: self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                **kw,
            )
        )
        return r.choices[0].message.content.strip()


class VertexLlama:
    """Llama (Model Garden MaaS) on company Vertex AI; same chat() interface as Groq."""

    def __init__(self, model=None):
        import google.auth
        import requests
        from google.oauth2.credentials import Credentials

        from . import config

        try:
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            creds.refresh(google.auth.transport.requests.Request())
        except Exception:
            creds = Credentials(_gcloud_token())
        self.sess = google.auth.transport.requests.AuthorizedSession(creds)
        self.model = model or config.VERTEX_LLAMA_MODEL
        self.url = (
            f"https://{config.GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/{config.GCP_PROJECT}"
            f"/locations/{config.GCP_LOCATION}/endpoints/openapi/chat/completions"
        )
        self.backend = "vertex"

    def chat(self, system: str, user: str, json_mode=False) -> str:
        body = {
            "model": self.model,
            "temperature": 0.0,
            "max_tokens": 512,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }

        def call():
            r = self.sess.post(self.url, json=body, timeout=120)
            if r.status_code != 200:
                raise RuntimeError(f"vertex llama {r.status_code}: {r.text[:200]}")
            return r.json()["choices"][0]["message"]["content"].strip()

        return _retry(call)


def get_judge_llm():
    """Groq if GROQ_API_KEY is set, else Llama on company Vertex AI."""
    return Groq() if os.getenv("GROQ_API_KEY") else VertexLlama()


class GeminiJudge(Gemini):
    """Judge model (Gemini Flash) on company Vertex AI; same chat() interface as Groq."""

    def __init__(self, model=None):
        from . import config

        super().__init__(model or config.JUDGE_MODEL)

    def chat(self, system: str, user: str, json_mode=False) -> str:
        from google.genai import types

        cfg = types.GenerateContentConfig(
            temperature=0.0,
            system_instruction=system,
            response_mime_type="application/json" if json_mode else None,
        )
        r = _retry(lambda: self.client.models.generate_content(model=self.model, contents=user, config=cfg))
        return (r.text or "").strip()


def get_judge_llm():
    """Groq if GROQ_API_KEY is set, else Gemini Flash on company Vertex AI."""
    return Groq() if os.getenv("GROQ_API_KEY") else GeminiJudge()
