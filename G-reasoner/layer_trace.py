"""Node scores after every GNN layer of G-reasoner, for the hop analysis (E7: "one layer = one hop").

G-reasoner-34M (gfmrag 2.0.0, `GraphReasoner` + `QueryNBFNet`) runs 6 message-passing layers with residual
connections and scores nodes from the LAST layer only:

    score = predict_mlp([h_6, q, e])        h_6 = node states after layer 6, q = question, e = node text embedding

Scoring each layer's states h_0..h_6 with the same head gives "the score the model would give if it stopped
after layer l" (a logit-lens readout). h_0 is the input (question embedding on the start nodes); information
from a start node can reach nodes at most l hops away by layer l. Caveat for the write-up: the head is trained
on h_6 only, so scores at early layers are a readout of the states, not something the model was trained to
produce; ranks and "which nodes rise" are more meaningful than raw values.

Implemented with forward hooks (gfmrag is not modified). The last layer's readout must equal the model's own
output: LayerTrace checks this on every question (`max_abs_diff`).

    with LayerTrace(retriever) as tr:
        res = retriever.retrieve(question, top_k=10)
    rec = tr.summarize(retriever, start_ids, gold_doc_ids, top_n=10)
"""
from __future__ import annotations

import torch

MAX_HOPS = 20   # hop distances are searched this far; beyond it (or not connected) they are None


class LayerTrace:
    def __init__(self, retriever):
        self.gr = retriever.graph_retriever                    # GraphReasoner
        self.em = self.gr.entity_model                         # QueryNBFNet
        cfg = (self.gr.use_ent_emb, self.em.concat_hidden, self.em.return_hidden)
        if cfg != ("early-late-fusion", False, True):
            raise ValueError(f"LayerTrace assumes G-reasoner-34M's head (early-late-fusion, concat_hidden=False, "
                             f"return_hidden=True); this model has {cfg}")
        self.scores: list[torch.Tensor] = []                   # per layer: (num_nodes,) on CPU, float32
        self.final: torch.Tensor | None = None
        self._handles = []

    def _readout(self, h):
        n = h.size(1)
        q = self._query.unsqueeze(1).expand(-1, n, -1)
        x = torch.cat([h, q, self._ent.unsqueeze(0).expand(h.size(0), -1, -1)], dim=-1)
        return self.gr.predict_mlp(x).squeeze(-1)[0].float().cpu()

    def _pre(self, module, args):
        data, node_features, _rel, query = args
        self._query = query
        self._ent = self.gr.ent_mlp(data.x)                    # same as GraphReasoner.forward (early_fuse input)
        self.scores = [self._readout(node_features)]           # layer 0 = input states

    def _layer(self, module, args, out):
        h = out + args[0] if self.em.short_cut and out.shape == args[0].shape else out   # residual, as in bellmanford
        self.scores.append(self._readout(h))

    def _post(self, module, args, out):
        self.final = self.gr.predict_mlp(torch.cat(
            [out, self._ent.unsqueeze(0).expand(out.size(0), -1, -1)], dim=-1)).squeeze(-1)[0].float().cpu()

    def __enter__(self):
        self._handles = [self.em.register_forward_pre_hook(self._pre), self.em.register_forward_hook(self._post)]
        self._handles += [layer.register_forward_hook(self._layer) for layer in self.em.layers]
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []

    # ------------------------------------------------------------------------------------------------------
    def summarize(self, retriever, start_ids: list[int], gold_doc_ids: list[str], top_n: int = 10) -> dict:
        """Per layer: top nodes of each type (with hop distance from the nearest start node) and the rank of
        every gold chunk among document nodes (1 = best). Hop distances above the model's 6 layers are kept,
        since "gold chunk 8 hops away" explains a miss. JSON-ready."""
        if len(self.scores) != len(self.em.layers) + 1:
            raise RuntimeError("no trace captured; call retrieve() inside `with LayerTrace(...)`")
        g, id2node = retriever.graph, retriever.qa_data.id2node
        hops = hop_distance(g.edge_index, g.num_nodes, start_ids, MAX_HOPS)
        diff = float((self.scores[-1] - self.final).abs().max()) if self.final is not None else None
        node2id = retriever.qa_data.node2id
        doc_ids = g.nodes_by_type["document"].cpu()
        gold_idx = [node2id[d] for d in gold_doc_ids if d in node2id]
        layers = []
        for layer, s in enumerate(self.scores):
            rec = {"layer": layer, "top": {}}
            for t, ids in g.nodes_by_type.items():
                ids = ids.cpu()
                top = torch.topk(s[ids], min(top_n, len(ids)))
                rec["top"][t] = [{"id": id2node[int(i)], "score": round(float(v), 4), "hops": _h(hops[int(i)])}
                                 for i, v in zip(ids[top.indices], top.values)]
            doc_scores = s[doc_ids]
            rec["gold_doc_rank"] = {id2node[i]: int((doc_scores > s[i]).sum()) + 1 for i in gold_idx}
            layers.append(rec)
        return {"max_abs_diff_last_layer": diff,
                "gold_doc_hops": {id2node[i]: _h(hops[i]) for i in gold_idx},
                "layers": layers}

    def track(self, retriever, names: list[str]) -> dict:
        """Score and rank of the named nodes after every layer, whether or not they reach the top. Rank is
        among nodes of the same type (1 = best), as summarize() ranks gold chunks among documents. Names not
        in the graph map to None. JSON-ready."""
        if len(self.scores) != len(self.em.layers) + 1:
            raise RuntimeError("no trace captured; call retrieve() inside `with LayerTrace(...)`")
        g, node2id = retriever.graph, retriever.qa_data.node2id
        type_ids = {t: ids.cpu() for t, ids in g.nodes_by_type.items()}
        type_of = {int(i): t for t, ids in type_ids.items() for i in ids}
        out = {}
        for name in names:
            i = node2id.get(name)
            if i is None or i not in type_of:
                out[name] = None
                continue
            ids = type_ids[type_of[i]]
            out[name] = {"type": type_of[i], "of": len(ids),
                         "layers": [{"layer": layer, "score": round(float(s[i]), 4),
                                     "rank": int((s[ids] > s[i]).sum()) + 1}
                                    for layer, s in enumerate(self.scores)]}
        return out


def hop_distance(edge_index: torch.Tensor, num_nodes: int, start_ids: list[int], max_hops: int) -> torch.Tensor:
    """Shortest number of edges from any start node (edge_index already holds inverse edges, so this is
    undirected). Nodes not reached within max_hops get -1."""
    dist = torch.full((num_nodes,), -1, dtype=torch.long)
    if not start_ids:
        return dist
    src, dst = edge_index[0].cpu(), edge_index[1].cpu()
    frontier = torch.zeros(num_nodes, dtype=torch.bool)
    frontier[start_ids] = True
    dist[frontier] = 0
    for h in range(1, max_hops + 1):
        nxt = torch.zeros(num_nodes, dtype=torch.bool)
        nxt[dst[frontier[src]]] = True
        nxt &= dist < 0
        if not nxt.any():
            break
        dist[nxt] = h
        frontier = nxt
    return dist


def _h(d) -> int | None:
    d = int(d)
    return d if d >= 0 else None
