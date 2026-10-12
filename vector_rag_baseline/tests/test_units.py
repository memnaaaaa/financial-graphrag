import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag import metrics
from rag.data import check_gold_ids, load_chunks, load_questions
from rag.judge import parse_verdict

D = Path(__file__).resolve().parent.parent / "data"


def test_precision_recall():
    ret, gold = ["a", "b", "c", "d", "e"], ["a", "c", "z"]
    assert metrics.precision_at_k(ret, gold, 5) == pytest.approx(2 / 5)
    assert metrics.recall_at_k(ret, gold, 5) == pytest.approx(2 / 3)
    assert metrics.precision_at_k(ret, gold, 1) == 1.0
    assert metrics.recall_at_k(ret, gold, 2) == pytest.approx(1 / 3)


def test_judge_parse():
    assert parse_verdict('{"verdict": "Correct", "reason": "x"}')["verdict"] == "correct"
    assert parse_verdict('Sure! {"verdict": "missing", "reason": "x"}')["verdict"] == "missing"
    assert parse_verdict("garbage")["verdict"] == "invalid"
    assert parse_verdict('{"verdict": "maybe"}')["verdict"] == "invalid"


def test_rates_sum_to_one():
    r = metrics.judge_rates(["correct", "correct", "hallucination", "missing", "invalid"])
    assert r["correct_rate"] == 0.4 and r["invalid_rate"] == 0.2


def test_dummy_data_consistent():
    c, q = load_chunks(D / "dummy_chunks.jsonl"), load_questions(D / "dummy_questions.jsonl")
    check_gold_ids(q, c)


def test_loader_aliases_and_errors(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text(json.dumps({"id": 7, "content": "hello", "page": 2}) + "\n")
    c = load_chunks(p)[0]
    assert (c.chunk_id, c.text, c.meta) == ("7", "hello", {"page": 2})
    p.write_text(json.dumps({"foo": 1}) + "\n")
    with pytest.raises(KeyError):
        load_chunks(p)
    p.write_text(json.dumps({"chunk_id": "a", "text": "x"}) + "\n" + json.dumps({"chunk_id": "a", "text": "y"}) + "\n")
    with pytest.raises(ValueError):
        load_chunks(p)


def test_hit_at_k():
    assert metrics.hit_at_k(["a", "b"], ["b"], 1) == 0
    assert metrics.hit_at_k(["a", "b"], ["b"], 2) == 1
