import numpy as np

from .judge import LABELS


def precision_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    return len(set(retrieved[:k]) & set(gold)) / k


def recall_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    return len(set(retrieved[:k]) & set(gold)) / len(set(gold))


def hit_at_k(retrieved: list[str], gold: list[str], k: int) -> int:
    return int(bool(set(retrieved[:k]) & set(gold)))


def facts_found(retrieved: list[str], fact_chunks: dict, k: int) -> dict:
    """Fact-by-fact retrieval check. A gold fact is found if ANY chunk that states it is in the top-k. A question is
    fully retrieved only if every fact it needs is found (one missing hop is enough to fail a multi-hop question)."""
    top = set(retrieved[:k])
    found = [f for f, ids in fact_chunks.items() if top & set(ids)]
    return {"facts_total": len(fact_chunks), "facts_found": len(found),
            "missing_facts": [f for f in fact_chunks if f not in found], "all_facts": int(len(found) == len(fact_chunks))}


def judge_rates(verdicts: list[str]) -> dict:
    n = len(verdicts)
    out = {f"{l}_rate": sum(v == l for v in verdicts) / n for l in LABELS}
    out["invalid_rate"] = sum(v == "invalid" for v in verdicts) / n
    return out


def latency_stats(ms: list[float]) -> dict:
    a = np.asarray(ms, dtype=float)
    return {"mean_ms": float(a.mean()), "p95_ms": float(np.percentile(a, 95))}


# ---------------------------------------------------------------------------------------------------------------
# Hallucination / traceability measures (project plan, Nov 2026).
#   unsupported-number rate : numbers in an answer that appear in none of its cited chunks
#   citation accuracy       : share of numeric claims whose cited chunk holds the number, in the right filing
# Both are string checks: no LLM involved, so they are cheap, deterministic and can be rerun exactly.
# ---------------------------------------------------------------------------------------------------------------
import itertools
import re

CHUNK_ID_RE = re.compile(r"\b[A-Z]{1,5}_FY\d{4}_[A-Z0-9]+_\d{4}\b")
_NUM_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
_SCALES = (1.0, 1e3, 1e-3, 1e6, 1e-6)  # "$416.2 billion" in the answer vs "416,161" (millions) in the chunk


def cited_ids(text: str) -> list[str]:
    """Chunk ids cited in an answer, in order, without duplicates."""
    return list(dict.fromkeys(CHUNK_ID_RE.findall(text)))


def _strip_citations(text: str) -> str:
    return re.sub(r"\[[^\]]*\]", " ", CHUNK_ID_RE.sub(" ", text))


def extract_numbers(text: str, drop: str = "") -> list[tuple[float, int]]:
    """Numbers in `text` as (value, decimals). Citation ids are removed first; 4-digit years (1900-2100 written
    without a comma) and any number that also appears in `drop` (usually the question) are skipped."""
    skip = {v for v, _ in extract_numbers(drop)} if drop else set()
    out = []
    for m in _NUM_RE.finditer(_strip_citations(text)):
        tok = m.group(0).rstrip(",")
        if "," not in tok and "." not in tok and 1900 <= float(tok) <= 2100:
            continue
        val = float(tok.replace(",", ""))
        if val in skip:
            continue
        out.append((val, len(tok.split(".")[1]) if "." in tok else 0))
    return out


def _supported(x: float, dec: int, evidence: list[float]) -> bool:
    """x matches an evidence number up to the rounding the answer used (and a thousand/million rescale)."""
    tol = 0.5 * 10 ** (-dec)
    return any(abs(x * s - e) <= tol * s + 1e-9 for e in evidence for s in _SCALES)


def _derived(evidence: list[float]) -> list[float]:
    """Values a model may legitimately compute from two evidence numbers: sum, difference, ratio, percent change."""
    out = []
    for a, b in itertools.permutations(evidence[:60], 2):
        out += [a + b, abs(a - b)]
        if b:
            out += [a / b, (a / b) * 100, (a / b - 1) * 100]
    return out


def unsupported_numbers(answer: str, evidence_texts: list[str], question: str = "", allow_derived: bool = False) -> dict:
    """Numbers in `answer` that appear in none of `evidence_texts` (the chunks the answer cites).
    allow_derived=True also accepts numbers computable from two evidence numbers (sum, difference, ratio, % change)."""
    nums = extract_numbers(answer, drop=question)
    ev = [v for t in evidence_texts for v, _ in extract_numbers(t)]
    if allow_derived:
        ev = ev + _derived(ev)
    bad = [v for v, d in nums if not _supported(v, d, ev)]
    return {"n_numbers": len(nums), "n_unsupported": len(bad), "unsupported": bad}


def citation_accuracy(answer: str, chunk_text: dict, chunk_filing: dict, gold_filings: set, question: str = "",
                      allow_derived: bool = False) -> dict:
    """Claim-level citation check. The answer is split into sentences; a sentence with a number is a claim. A claim is
    correct iff it cites >=1 chunk, every number in it appears in one of ITS cited chunks, and every cited chunk is
    from a filing in gold_filings (e.g. {"JNJ FY2025"}). chunk_text / chunk_filing map chunk id -> text / "JNJ FY2025"."""
    claims = [s for s in re.split(r"(?<=[.;!?])\s+|\n+", answer) if extract_numbers(s, drop=question)]
    n_cited = n_ok = 0
    for s in claims:
        ids = [i for i in cited_ids(s) if i in chunk_text]
        if ids:
            n_cited += 1
        ok = bool(ids) and all(chunk_filing.get(i) in gold_filings for i in ids) and \
            unsupported_numbers(s, [chunk_text[i] for i in ids], question, allow_derived)["n_unsupported"] == 0
        n_ok += ok
    return {"n_claims": len(claims), "n_cited": n_cited, "n_correct": n_ok}


def aggregate_traceability(per_q: list[dict]) -> dict:
    """per_q: dicts with n_numbers, n_unsupported, n_claims, n_cited, n_correct. Micro = pooled over all numbers /
    claims; the unsupported rate is also given per answer (share of answers with >=1 unsupported number)."""
    nn, nu = sum(r["n_numbers"] for r in per_q), sum(r["n_unsupported"] for r in per_q)
    nc, nk, nr = sum(r["n_claims"] for r in per_q), sum(r["n_cited"] for r in per_q), sum(r["n_correct"] for r in per_q)
    with_nums = [r for r in per_q if r["n_numbers"]]
    return {
        "unsupported_number_rate": nu / nn if nn else 0.0,
        "answers_with_unsupported_rate": sum(r["n_unsupported"] > 0 for r in with_nums) / len(with_nums) if with_nums else 0.0,
        "citation_rate": nk / nc if nc else 0.0,
        "citation_accuracy": nr / nc if nc else 0.0,
    }
