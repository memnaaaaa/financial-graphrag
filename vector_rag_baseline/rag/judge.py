import json
import re

LABELS = ("correct", "hallucination", "missing")

SYSTEM = """You grade a RAG system's answer against a reference answer.
Choose exactly one verdict:
- "correct": the answer conveys the reference answer's key facts/numbers, with nothing contradicting it.
- "missing": the answer declines or says the information is not available / cannot be determined.
- "hallucination": the answer asserts facts that are wrong or contradict the reference (including wrong numbers, entities, or invented details).
Partially complete answers with no wrong claims are "correct" only if every key fact in the reference is present; otherwise "missing".
Respond with JSON only: {"verdict": "correct|hallucination|missing", "reason": "<one sentence>"}"""


def parse_verdict(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        d = {}
    v = str(d.get("verdict", "")).strip().lower()
    if v not in LABELS:
        return {"verdict": "invalid", "reason": f"unparseable judge output: {raw[:120]}"}
    return {"verdict": v, "reason": d.get("reason", "")}


def judge(llm, question: str, gold_answer: str, model_answer: str) -> dict:
    user = f"Question: {question}\nReference answer: {gold_answer}\nSystem answer: {model_answer}"
    return parse_verdict(llm.chat(SYSTEM, user, json_mode=True))
