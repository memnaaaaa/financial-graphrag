"""Copy a team graph (data/graph/<name>/processed/stage1) into a gfmrag data root and add the
raw/documents.json file gfmrag needs.

gfmrag opens <root>/<name>/raw/documents.json every time it loads a dataset, even when stage1
already exists (GraphIndexDataset.load_qa_data). The team graph folder does not have it, so it
is written here from the document nodes ({chunk_id: content}).

The repo copy is never written to: gfmrag also saves its stage2 cache next to stage1, so it
must run on a copy.

    python prepare_data.py --repo /content/financial-graphrag --root /content/drive/MyDrive/fin_greasoner_cache/data

Standard library only (runs locally and in Colab).
"""
import argparse
import ast
import csv
import json
import os
import shutil
import sys

STAGE1 = ["nodes.csv", "relations.csv", "edges.csv"]

csv.field_size_limit(sys.maxsize)  # document nodes hold whole chunks in their attributes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="clone of financial-graphrag")
    ap.add_argument("--graph", default="fin10k_v1", help="folder under data/graph/ in the repo")
    ap.add_argument("--root", required=True, help="gfmrag data root (data_dir) to copy into")
    a = ap.parse_args()

    src = os.path.join(a.repo, "data", "graph", a.graph, "processed", "stage1")
    dst = os.path.join(a.root, a.graph, "processed", "stage1")
    raw = os.path.join(a.root, a.graph, "raw")
    os.makedirs(dst, exist_ok=True)
    os.makedirs(raw, exist_ok=True)

    changed = False
    for name in STAGE1:
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if not os.path.exists(s):
            sys.exit(f"missing {s}")
        if not os.path.exists(d) or open(s, "rb").read() != open(d, "rb").read():
            shutil.copyfile(s, d)
            changed = True
    if changed:
        # stage2 is keyed by the embedding config, not by the stage1 contents, so a new graph
        # would silently reuse old embeddings. Remove it so the next index run rebuilds it.
        stage2 = os.path.join(a.root, a.graph, "processed", "stage2")
        if os.path.isdir(stage2):
            shutil.rmtree(stage2)
            print("stage1 changed: removed old stage2 cache", stage2)

    docs = {}
    for r in csv.DictReader(open(os.path.join(dst, "nodes.csv"), encoding="utf-8")):
        if r["type"] == "document":
            attrs = ast.literal_eval(r["attributes"]) if r["attributes"] else {}
            if "content" not in attrs:
                sys.exit(f"document node {r['name']} has no 'content' attribute")
            docs[r["name"]] = attrs["content"]
    if not docs:
        sys.exit("no document nodes found")
    with open(os.path.join(raw, "documents.json"), "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)

    print(f"{'copied' if changed else 'unchanged'} stage1 -> {dst}")
    print(f"wrote {len(docs)} documents -> {os.path.join(raw, 'documents.json')}")


if __name__ == "__main__":
    main()
