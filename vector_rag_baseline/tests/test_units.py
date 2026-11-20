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


def test_traceability_measures():
    t = "Total net sales | 416,161 | 391,035 Research and development | 34,550"
    cid = "AAPL_FY2025_ITEM8_0000"
    assert metrics.cited_ids(f"x [{cid}] y [{cid}, JNJ_FY2025_ITEM7_0012]") == [cid, "JNJ_FY2025_ITEM7_0012"]
    ok = metrics.unsupported_numbers(f"Net sales were $416.2 billion [{cid}].", [t])
    assert ok["n_numbers"] == 1 and ok["n_unsupported"] == 0  # rounded and rescaled billion vs million
    bad = metrics.unsupported_numbers(f"R&D was $99,999 million [{cid}].", [t])
    assert bad["unsupported"] == [99999.0]
    assert metrics.unsupported_numbers("Sales rose 6.4%.", [t])["n_unsupported"] == 1
    assert metrics.unsupported_numbers("Sales rose 6.4%.", [t], allow_derived=True)["n_unsupported"] == 0
    # years and question numbers are not counted
    assert metrics.unsupported_numbers("In fiscal 2025, 166,000 people.", ["166,000"], "fiscal 2025")["n_unsupported"] == 0
    a = f"Net sales were $416,161 million [{cid}]. R&D was $34,550 million [{cid}]. Staff were 5,000."
    r = metrics.citation_accuracy(a, {cid: t}, {cid: "AAPL FY2025"}, {"AAPL FY2025"})
    assert (r["n_claims"], r["n_cited"], r["n_correct"]) == (3, 2, 2)
    wrong_year = metrics.citation_accuracy(a, {cid: t}, {cid: "AAPL FY2024"}, {"AAPL FY2025"})
    assert wrong_year["n_correct"] == 0


def test_error_stage():
    from rag.error_stage import tag
    assert tag("correct", False) == "ok"
    assert tag("missing", False) == "retrieval"  # a missing fact (hop) is a retrieval failure
    assert tag("hallucination", True) == "generation"
    assert tag("missing", True, entities_linked=False) == "entity_linking"
    assert tag("missing", False, graph_has_fact=False) == "graph"


def test_facts_found():
    fc = {"f1": ["a", "b"], "f2": ["c"]}
    r = metrics.facts_found(["x", "b", "y", "z", "c"], fc, 5)
    assert (r["facts_found"], r["all_facts"], r["missing_facts"]) == (2, 1, [])
    r = metrics.facts_found(["x", "b", "y", "z", "c"], fc, 2)
    assert (r["facts_found"], r["all_facts"], r["missing_facts"]) == (1, 0, ["f2"])


def test_answer_support():
    cid = "JNJ_FY2025_ITEM1_0011"
    txt = {cid: "Genmab A/S owns two patent families related to DARZALEX, and Janssen Biotech has an exclusive license."}
    good = metrics.answer_support(f"Genmab owns two patent families related to DARZALEX [{cid}].", txt)
    assert (good["n_sentences"], good["n_supported_sentences"]) == (1, 1)
    bad = metrics.answer_support(f"Bayer manufactures rivaroxaban tablets in Germany [{cid}].", txt)
    assert bad["n_supported_sentences"] == 0
    nocite = metrics.answer_support("Genmab owns two patent families related to DARZALEX.", txt)
    assert nocite["n_supported_sentences"] == 0
    assert metrics.answer_support("I cannot answer from the provided context.", txt)["n_sentences"] == 0
