"""NER and entity-linking models for GFMRetriever, backed by entity_index.EntityIndex (no LLM).

GFMRetriever.prepare_input_for_graph_retriever calls ner_model(query) for mention strings, then
el_model(mentions, topk=1), and reads linked[mention][0]["entity"]. Because EntityIndex already
returns exact node names, NER does the matching and EL only passes names through.

EL must never return an empty list (GFMRetriever would raise IndexError on [0]). When nothing is
found, GFMRetriever passes the whole query to EL; we answer with a name that is not in the graph,
which GFMRetriever skips, so the query runs with no start nodes instead of crashing.
"""
import logging

from gfmrag.graph_index_construction.entity_linking_model.base_model import BaseELModel
from gfmrag.graph_index_construction.ner_model.base_model import BaseNERModel

from entity_index import EntityIndex

logger = logging.getLogger(__name__)
NO_MATCH = "<no linked entity>"


class AliasNER(BaseNERModel):
    def __init__(self, index: EntityIndex, **kwargs):
        self.index = index

    def __call__(self, text: str) -> list:
        return self.index.find(text)


class FixedNER(BaseNERModel):
    """Start nodes chosen ahead of time, looked up by question text (e.g. by gemini_ner.py).
    Unknown questions get no start nodes."""

    def __init__(self, start_nodes: dict, **kwargs):
        self.start_nodes = start_nodes

    def __call__(self, text: str) -> list:
        return list(self.start_nodes.get(text, []))


class PassThroughEL(BaseELModel):
    def __init__(self, **kwargs):
        self.known = set()

    def index(self, entity_list: list) -> None:
        self.known = set(entity_list)

    def __call__(self, ner_entity_list: list, topk: int = 1) -> dict:
        out = {}
        for m in ner_entity_list:
            if m in self.known:
                out[m] = [{"entity": m, "score": 1.0}]
            else:
                logger.warning("no graph node for %r; query runs without it", m[:80])
                out[m] = [{"entity": NO_MATCH, "score": 0.0}]
        return out
