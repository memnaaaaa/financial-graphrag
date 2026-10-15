"""Check a stage1 graph folder the same way gfmrag reads it, and print coverage numbers.

    python data/graph/validate_graph.py data/graph/fin10k_v0/processed/stage1
"""
import ast
import collections
import csv
import sys

d = sys.argv[1] if len(sys.argv) > 1 else "data/graph/fin10k_v0/processed/stage1"
ok = True


def fail(msg):
    global ok
    ok = False
    print("FAIL:", msg)


def rows(name):
    # gfmrag uses pandas.read_csv(keep_default_na=False); csv.DictReader gives the same strings
    return list(csv.DictReader(open(f"{d}/{name}", encoding="utf-8")))


nodes, rels, edges = rows("nodes.csv"), rows("relations.csv"), rows("edges.csv")
for name, rs, cols in (("nodes", nodes, ["name", "type", "attributes"]),
                       ("relations", rels, ["name", "attributes"]),
                       ("edges", edges, ["source", "relation", "target", "attributes"])):
    if list(rs[0].keys()) != cols:
        fail(f"{name}.csv columns {list(rs[0].keys())} != {cols}")
    for r in rs:
        try:
            a = ast.literal_eval(r["attributes"]) if r["attributes"] else {}
            assert isinstance(a, dict)
        except Exception as e:                                  # noqa: BLE001
            fail(f"{name}.csv attributes not a Python dict literal: {r} ({e})")
            break

names = [r["name"] for r in nodes]
if len(set(names)) != len(names):
    fail(f"{len(names) - len(set(names))} duplicate node names")
if any(not n.strip() for n in names):
    fail("empty node name")
node_type = {r["name"]: r["type"] for r in nodes}
kind = {r["name"]: ast.literal_eval(r["attributes"]).get("kind", r["type"]) for r in nodes}
relset = {r["name"] for r in rels}
bad = [e for e in edges if e["source"] not in node_type or e["target"] not in node_type
       or e["relation"] not in relset]
if bad:
    fail(f"{len(bad)} edges point to unknown nodes/relations (gfmrag would drop them), e.g. {bad[0]}")
trip = [(e["source"], e["relation"], e["target"]) for e in edges]
if len(set(trip)) != len(trip):
    fail("duplicate edges")
unused = relset - {e["relation"] for e in edges}
if unused:
    print("note: relations with no edges:", unused)

deg = collections.Counter()
for s, _, t in trip:
    deg[s] += 1
    deg[t] += 1
by_kind = collections.defaultdict(list)
for n in names:
    by_kind[kind[n]].append(n)
mention = collections.Counter(s for s, r, _ in trip if r == "is_mentioned_in")
docs_hit = {t for s, r, t in trip if r == "is_mentioned_in"}

print(f"nodes {len(nodes)}, relations {len(rels)}, edges {len(edges)}")
print(f"{'kind':<14}{'count':>7}{'isolated':>10}{'linked to a chunk':>20}{'max degree':>12}")
for k, ns in sorted(by_kind.items(), key=lambda x: -len(x[1])):
    iso = sum(1 for n in ns if deg[n] == 0)
    if k == "document":
        linked = sum(1 for n in ns if n in docs_hit)
    else:
        linked = sum(1 for n in ns if mention[n])
    top = max(ns, key=lambda n: deg[n])
    print(f"{k:<14}{len(ns):>7}{iso:>10}{linked:>13} ({linked / len(ns):4.0%}){deg[top]:>12}  {top[:50]}")
print("PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
