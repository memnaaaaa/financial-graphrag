"""Gemini over its REST API (standard library only), with every reply cached on disk.

Same model and settings as the vector-RAG baseline (vector_rag_baseline/rag/config.py: gemini-3.5-flash-lite,
temperature 0, system instruction). The key is GEMINI_API_KEY from the environment or the repo-root .env
(the same key extract_relations_llm.py uses). A rerun reads replies from the cache instead of calling Gemini.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-3.5-flash-lite"


def load_key(repo):
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    for env in (os.path.join(repo, ".env"), os.path.join(repo, "vector_rag_baseline", ".env")):
        if key or not os.path.exists(env):
            continue
        for line in open(env, encoding="utf-8"):
            k, _, v = line.strip().partition("=")
            if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY") and v.strip():
                key = v.strip().strip('"').strip("'")
    return key


class Cache:
    def __init__(self, path):
        self.path, self.data = path, {}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.strip():
                    r = json.loads(line)
                    self.data[r["key"]] = r["reply"]

    @staticmethod
    def key(*parts):
        return hashlib.sha256("\x1e".join(parts).encode()).hexdigest()

    def put(self, key, reply, **meta):
        self.data[key] = reply
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"key": key, "reply": reply, **meta}, ensure_ascii=False) + "\n")


class Gemini:
    def __init__(self, repo, model=DEFAULT_MODEL, cache_dir=None, rpm=10):
        self.model, self.rpm, self.key = model, rpm, load_key(repo)
        self.cache = Cache(os.path.join(cache_dir or os.path.join(repo, "answer_step", "cache"), f"{model}.jsonl"))
        self.calls = self.hits = 0
        self._last = 0.0

    def _post(self, system, prompt, json_mode):
        if not self.key:
            raise SystemExit("GEMINI_API_KEY not found in the environment or in .env at the repo root.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        cfg = {"temperature": 0.0}
        if json_mode:
            cfg["responseMimeType"] = "application/json"
        body = json.dumps({"systemInstruction": {"parts": [{"text": system}]},
                           "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                           "generationConfig": cfg}).encode()
        wait = 10
        for attempt in range(6):
            time.sleep(max(0.0, 60.0 / self.rpm - (time.time() - self._last)))
            self._last = time.time()
            req = urllib.request.Request(url, data=body, method="POST",
                                         headers={"Content-Type": "application/json", "x-goog-api-key": self.key})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.loads(r.read())
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:300]
                if e.code == 429 and "PerDay" in msg:
                    raise SystemExit("Daily Gemini limit reached. Run the same command tomorrow; "
                                     "finished answers are cached.")
                if e.code in (429, 500, 503) and attempt < 5:
                    print(f"  HTTP {e.code}, waiting {wait}s ...", file=sys.stderr)
                    time.sleep(wait)
                    wait = min(wait * 2, 120)
                    continue
                raise SystemExit(f"Gemini error HTTP {e.code}: {msg}")
            except urllib.error.URLError as e:
                if attempt < 5:
                    time.sleep(wait)
                    continue
                raise SystemExit(f"Cannot reach Gemini: {e}")
        return ""

    def ask(self, system, prompt, json_mode=False, **meta):
        key = Cache.key(self.model, system, prompt, str(json_mode))
        if key in self.cache.data:
            self.hits += 1
            return self.cache.data[key]
        reply = self._post(system, prompt, json_mode)
        self.calls += 1
        self.cache.put(key, reply, model=self.model, **meta)
        return reply

    # the interfaces vector_rag_baseline/rag/generate.py and rag/judge.py expect
    def generate(self, prompt, system=None):
        return self.ask(system or "", prompt, role="answer")

    def chat(self, system, user, json_mode=False):
        return self.ask(system, user, json_mode, role="judge")


class FakeGemini:
    """For --dry-run: no API calls. Answers with the first Value (or passage) number it is given, cites it,
    and the judge says 'correct'. Only for checking that the pipeline runs end to end."""
    calls = hits = 0

    def generate(self, prompt, system=None):
        import re
        v = re.search(r"\[(V-[A-Z]+-\d{4})\] .*? = (\S+ [a-z ]*?)\s*\(printed as \"([^\"]+)\"", prompt)
        if v:
            return f"The value is {v.group(3)} [{v.group(1)}]."
        c = re.search(r"\[([A-Z]+_FY\d{4}_[A-Z0-9]+_\d{4})\]\n(?:.*\n)*?.*?(\d{1,3}(?:,\d{3})+)", prompt)
        return f"The value is {c.group(2)} [{c.group(1)}]." if c else "I cannot answer from the provided context."

    def chat(self, system, user, json_mode=False):
        return '{"verdict": "correct", "reason": "dry run"}'
