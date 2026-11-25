"""Set up the fine-tuning dataset fin10k_v1_sft in the gfmrag data root: the same graph as fin10k_v1 plus the
synthetic pairs as train.json (J&J + Apple) and test.json (Microsoft, used for picking the best epoch).
gfmrag reads these from processed/stage1/, next to the graph files (GraphIndexDataset.raw_dir), not from raw/.

Kept separate from fin10k_v1 so that evaluation (evaluate.py on fin10k_v1) never loads training questions.
Run prepare_data.py (and ideally index_graph.py) for fin10k_v1 first: its stage1, documents.json and stage2
embedding cache are copied, so the graph is not embedded twice. The cache can be shared because gfmrag keys it
by the embedding settings, not the dataset name.

Relation pairs (templates relation*, ~2% of train) are repeated --relation-repeat times so they are not drowned
out by ~1,800 lookup/change/... pairs. Repeats get new ids ("...-rep2").

gfmrag reuses processed/.../train.pt whenever it exists, even if raw/train.json changed. So when the pairs
change, the old train.pt/test.pt are deleted here and rebuilt by the next index_graph.py run.

    python prepare_sft.py --root <data root> --synthetic synthetic/fin10k_v1 --relation-repeat 5

Standard library only.
"""
import argparse
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE1 = ["nodes.csv", "relations.csv", "edges.csv"]


def same(path, data):
    return os.path.exists(path) and open(path, encoding="utf-8").read() == data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="gfmrag data root (prepare_data.py --root)")
    ap.add_argument("--src", default="fin10k_v1", help="prepared dataset whose graph is used")
    ap.add_argument("--dst", default="fin10k_v1_sft")
    ap.add_argument("--synthetic", default=os.path.join(HERE, "synthetic", "fin10k_v1"))
    ap.add_argument("--relation-repeat", type=int, default=5, help="copies of each relation pair in train (1 = none)")
    a = ap.parse_args()

    src, dst = os.path.join(a.root, a.src), os.path.join(a.root, a.dst)
    for f in [os.path.join(src, "processed", "stage1", n) for n in STAGE1] + [os.path.join(src, "raw", "documents.json")]:
        if not os.path.exists(f):
            sys.exit(f"missing {f}: run prepare_data.py --graph {a.src} first")

    os.makedirs(os.path.join(dst, "processed", "stage1"), exist_ok=True)
    os.makedirs(os.path.join(dst, "raw"), exist_ok=True)
    graph_changed = False
    for n in STAGE1:
        s, d = os.path.join(src, "processed", "stage1", n), os.path.join(dst, "processed", "stage1", n)
        if not os.path.exists(d) or open(s, "rb").read() != open(d, "rb").read():
            shutil.copyfile(s, d)
            graph_changed = True
    shutil.copyfile(os.path.join(src, "raw", "documents.json"), os.path.join(dst, "raw", "documents.json"))

    stage2_src, stage2_dst = os.path.join(src, "processed", "stage2"), os.path.join(dst, "processed", "stage2")
    if graph_changed and os.path.isdir(stage2_dst):
        shutil.rmtree(stage2_dst)                     # graph changed: old embeddings no longer match
        print("graph changed: removed old", stage2_dst)
    if not os.path.isdir(stage2_dst) and os.path.isdir(stage2_src):
        shutil.copytree(stage2_src, stage2_dst, ignore=shutil.ignore_patterns("train.pt", "test.pt"))
        print("copied the embedding cache from", a.src)

    train = json.load(open(os.path.join(a.synthetic, "train.json"), encoding="utf-8"))
    test = json.load(open(os.path.join(a.synthetic, "test.json"), encoding="utf-8"))
    rel = [r for r in train if r["template"].startswith("relation")]
    for k in range(2, a.relation_repeat + 1):
        train += [{**r, "id": f"{r['id']}-rep{k}"} for r in rel]

    qa_changed = False
    for name in ("train.json", "test.json"):          # left in raw/ by the first version of this script
        stale = os.path.join(dst, "raw", name)
        if os.path.exists(stale):
            os.remove(stale)
    for name, recs in (("train.json", train), ("test.json", test)):
        path, data = os.path.join(dst, "processed", "stage1", name), json.dumps(recs, ensure_ascii=False, indent=1)
        if not same(path, data):
            open(path, "w", encoding="utf-8").write(data)
            qa_changed = True
    if qa_changed or graph_changed:
        old = glob.glob(os.path.join(stage2_dst, "*", "train.pt")) + glob.glob(os.path.join(stage2_dst, "*", "test.pt"))
        for f in old:
            os.remove(f)
        if old:
            print(f"pairs changed: removed {len(old)} old processed QA file(s); index_graph.py rebuilds them")

    print(f"{dst}: train {len(train)} pairs ({len(rel)} relation pairs x {a.relation_repeat}), "
          f"test {len(test)} pairs (Microsoft)")
    print(f"next: index_graph.py --data-name {a.dst}  (embeds the {len(train) + len(test)} questions)")


if __name__ == "__main__":
    main()
