import numpy as np

from .judge import LABELS


def precision_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    return len(set(retrieved[:k]) & set(gold)) / k


def recall_at_k(retrieved: list[str], gold: list[str], k: int) -> float:
    return len(set(retrieved[:k]) & set(gold)) / len(set(gold))


def hit_at_k(retrieved: list[str], gold: list[str], k: int) -> int:
    return int(bool(set(retrieved[:k]) & set(gold)))


def judge_rates(verdicts: list[str]) -> dict:
    n = len(verdicts)
    out = {f"{l}_rate": sum(v == l for v in verdicts) / n for l in LABELS}
    out["invalid_rate"] = sum(v == "invalid" for v in verdicts) / n
    return out


def latency_stats(ms: list[float]) -> dict:
    a = np.asarray(ms, dtype=float)
    return {"mean_ms": float(a.mean()), "p95_ms": float(np.percentile(a, 95))}
