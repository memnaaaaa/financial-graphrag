"""Central config. Everything Mohini's file might change lives here."""
import os
from pathlib import Path

from dotenv import load_dotenv

try:  # corporate TLS-inspection proxies: trust the OS keychain CAs (verification stays ON)
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# --- chunks.jsonl schema: first matching alias wins; extra fields are kept as metadata
ID_FIELDS = ["chunk_id", "id", "chunk_uid"]
TEXT_FIELDS = ["text", "content", "chunk_text"]

# --- finalized tools
ENCODERS = {
    "bge-small": {
        "name": "BAAI/bge-small-en-v1.5",  # ~33M
        "query_prefix": "Represent this sentence for searching relevant passages: ",
    },
    "distilbert": {
        "name": "sentence-transformers/multi-qa-distilbert-cos-v1",  # ~66M, DistilBERT-based
        "query_prefix": "",
    },
}
RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_POOL = 20
KS = (5, 10)

AGREED_GEMINI = "gemini-3.5-flash-lite"  # the one model the team agreed on (Nov 19); 2.5 Flash-Lite / Flash are closed to new keys
GEMINI_MODEL = os.getenv("GEMINI_MODEL", AGREED_GEMINI)  # generator
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")  # Vertex AI fallback; set via env or rag/local_config.py
VERTEX_LLAMA_MODEL = os.getenv("VERTEX_LLAMA_MODEL", "meta/llama-3.3-70b-instruct-maas")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", AGREED_GEMINI)  # judge: same agreed model, temperature 0, kept as in rag/judge.py
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GCLOUD_BIN = os.getenv("GCLOUD_BIN", "")
TEMPERATURE = 0.0

INDEX_DIR = ROOT / "indexes"
RESULTS_DIR = ROOT / "results"

try:  # optional, git-ignored machine-specific overrides (see local_config.example.py)
    from .local_config import *  # noqa: F401,F403
except ImportError:
    pass
