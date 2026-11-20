"""Error-stage tagging: every wrong answer is tagged with the FIRST pipeline stage that failed.
Order: graph -> entity_linking -> retrieval -> generation  (see docs/ERROR_STAGES.md for the rules and examples).

The vector-RAG baseline has no graph and no linking step, so for it only retrieval and generation can occur; the graph
and linking flags default to True ("not applicable / passed"). Graph systems pass the two extra flags.
"""
STAGES = ("ok", "graph", "entity_linking", "retrieval", "generation")


def tag(verdict: str, all_facts_found: bool, *, graph_has_fact: bool = True, entities_linked: bool = True) -> str:
    """verdict: judge label (correct / hallucination / missing / invalid); all_facts_found: every gold fact of the question
    (golden set v2 `gold_facts`) is stated by at least one chunk (or gold-sourced Value node) in the evidence given to
    the generator. One missing fact, i.e. one missing hop, is a retrieval failure."""
    if verdict == "correct":
        return "ok"
    if not graph_has_fact:
        return "graph"
    if not entities_linked:
        return "entity_linking"
    if not all_facts_found:
        return "retrieval"
    return "generation"


def generation_subtype(verdict: str, n_unsupported: int, n_cited_correct_claims: int, n_claims: int) -> str:
    """Optional detail for stage == generation."""
    if verdict == "missing":
        return "refused_or_incomplete"
    if n_unsupported:
        return "unsupported_number"
    if n_claims and n_cited_correct_claims < n_claims:
        return "wrong_citation"
    return "wrong_value_or_reasoning"
