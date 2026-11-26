"""The graph side of the answer step: load the graph, give Value nodes short citable ids, and build the
context a graph retriever hands to Gemini (Value lines and the connected subgraph between retrieved nodes)."""
import ast
import collections
import csv
import json
import os
import re

csv.field_size_limit(2**31 - 1)
VALUE_ID_RE = re.compile(r"\bV-[A-Z]{1,5}-\d{4}\b")      # never matches the chunk-id pattern in rag/metrics.py
SKIP_RELS = {"is_mentioned_in", "of_metric", "for_period"}  # chunks are given as passages; Value lines say metric and year
HUB_DEGREE = 60                                            # nodes with more links than this are not used as connectors


class Graph:
    def __init__(self, stage1_dir):
        self.nodes = {r["name"]: (r["type"], ast.literal_eval(r["attributes"]))
                      for r in csv.DictReader(open(os.path.join(stage1_dir, "nodes.csv"), encoding="utf-8"))}
        self.edges = []
        self.adj = collections.defaultdict(list)            # node -> [(neighbour, (s, r, t))]
        for r in csv.DictReader(open(os.path.join(stage1_dir, "edges.csv"), encoding="utf-8")):
            e = (r["source"], r["relation"], r["target"])
            self.edges.append(e)
            if e[1] in SKIP_RELS:
                continue
            self.adj[e[0]].append((e[2], e))
            self.adj[e[2]].append((e[0], e))
        # Value ids: V-<ticker>-<nnnn>, numbered by node name within each company (stable for a given graph)
        self.value_id, self.value_of = {}, {}
        by_ticker = collections.defaultdict(list)
        for n, (t, a) in self.nodes.items():
            if a.get("kind") == "Value":
                by_ticker[a["ticker"]].append(n)
        for tk, names in by_ticker.items():
            for i, n in enumerate(sorted(names), 1):
                vid = f"V-{tk}-{i:04d}"
                self.value_id[n], self.value_of[vid] = vid, n

    def kind(self, n):
        t, a = self.nodes.get(n, ("", {}))
        return a.get("kind", t)

    def is_value(self, n):
        return self.kind(n) == "Value"

    def value_line(self, n):
        a = self.nodes[n][1]
        return (f"[{self.value_id[n]}] {n} (printed as \"{a['printed_value']}\" in {a['source_filing']} 10-K, "
                f"{a['source_section']}, passage {a['source_chunk_id']})")

    def subgraph(self, seeds, cap=40):
        """Triples between retrieved nodes, plus, for each pair of retrieved nodes with no direct link, one
        2-hop path through another node (the least-connected one; hubs such as 'United States' or a Metric
        are never used)."""
        seeds = [s for s in dict.fromkeys(seeds) if s in self.nodes]
        seed_set = set(seeds)
        nbrs = {s: collections.defaultdict(list) for s in seeds}
        for s in seeds:
            for nb, e in self.adj[s]:
                nbrs[s][nb].append(e)
        direct = [e for s in seeds for nb, es in nbrs[s].items() if nb in seed_set for e in es]
        linked = {frozenset((e[0], e[2])) for e in direct}
        bridged = []
        for i, a in enumerate(seeds):
            for b in seeds[i + 1:]:
                if frozenset((a, b)) in linked:
                    continue
                common = [c for c in nbrs[a] if c in nbrs[b] and c not in seed_set and len(self.adj[c]) <= HUB_DEGREE]
                if common:
                    c = min(common, key=lambda c: (len(self.adj[c]), c))
                    bridged += [nbrs[a][c][0], nbrs[b][c][0]]
        return list(dict.fromkeys(direct + bridged))[:cap]


SUBJECT_KINDS = {"Company", "Segment", "BusinessLine", "Product"}


def select_values(g, nodes, cap=10):
    """Item 2: Values chosen by rule from the question's linked nodes instead of the retriever's ranking.

    nodes: start nodes and retrieved entities. A Value is kept if its subject is one of these nodes
    (Company, Segment, BusinessLine or Product), its metric is one of the linked Metric nodes, and its fiscal
    year is one of the linked FiscalYear nodes of that company (any year if none is linked for that company).
    Values limited to a region (U.S., Europe, ...) come after company-wide ones. Returns [] when no Metric
    node is linked (the question names no measurable figure), so the caller can fall back."""
    nodes = [n for n in dict.fromkeys(nodes) if n in g.nodes]
    metrics = {n for n in nodes if g.kind(n) == "Metric"}
    if not metrics:
        return []
    years = collections.defaultdict(set)
    for n in nodes:
        if g.kind(n) == "FiscalYear":
            a = g.nodes[n][1]
            years[a["ticker"]].add(n.split(" ")[0])
    regional = {s for s, r, t in g.edges if r == "in_location"} if not hasattr(g, "_regional") else g._regional
    g._regional = regional
    out = []
    for subj in nodes:
        if g.kind(subj) not in SUBJECT_KINDS:
            continue
        for nb, (s, r, t) in g.adj[subj]:
            if r != "has_value" or s != subj:
                continue
            a = g.nodes[t][1]
            if a["metric"] in metrics and (not years[a["ticker"]] or a["fiscal_year"] in years[a["ticker"]]):
                out.append(t)
    out = sorted(dict.fromkeys(out), key=lambda v: (v in regional, nodes.index(next(
        s for s, r, t in [(x[1][0], x[1][1], x[1][2]) for x in g.adj[v]] if r == "has_value")), v))
    return out[:cap]


def triple_text(g, e):
    s, r, t = e
    show = lambda n: f"{n} [{g.value_id[n]}]" if g.is_value(n) else n
    return f"{show(s)} --{r}--> {show(t)}"


def load_chunks(path):
    return {c["chunk_id"]: c for c in map(json.loads, open(path, encoding="utf-8"))}
