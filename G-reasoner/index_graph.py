"""Build gfmrag's stage2 cache (node and relation embeddings, graph.pt) for a prepared dataset.

Run once per graph, in its own process, before query.py. GFMRetriever.from_index would also
build it, but then it starts a second vLLM embedding model in the same process for queries,
and two vLLM instances (each reserving most of the GPU) can run out of memory on a T4. Running
the build here means query.py only finds the cache and starts one vLLM.

The embedding model and dataset settings come from the G-reasoner checkpoint's config.json
(Qwen3-Embedding-0.6B, 1024-dim), so the features match what the model was trained on.

    python index_graph.py --root /content/drive/MyDrive/fin_greasoner_cache/data --data-name fin10k_v1
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transformers.utils import cached_file  # noqa: E402

from gfmrag.gfmrag_retriever import GFMRetriever  # noqa: E402
from vllm_limits import limit_vllm_memory  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="gfmrag data root (prepare_data.py --root)")
    ap.add_argument("--data-name", default="fin10k_v1")
    ap.add_argument("--model", default="rmanluo/G-reasoner-34M")
    ap.add_argument("--force", action="store_true", help="rebuild stage2 even if it exists")
    a = ap.parse_args()

    limit_vllm_memory()
    model_config = json.load(open(cached_file(a.model, "config.json")))
    t0 = time.time()
    data = GFMRetriever._load_qa_data_from_model_config(
        data_dir=a.root, data_name=a.data_name, model_config=model_config, force_reindex=a.force)
    g = data.graph
    print(f"stage2 ready in {time.time() - t0:.0f}s: {data.processed_dir}")
    print(f"nodes {g.num_nodes}, edges {g.edge_index.size(1)} (with inverses), "
          f"relations {g.num_relations}, feat_dim {data.feat_dim}")
    print("nodes by type:", {k: len(v) for k, v in g.nodes_by_type.items()})
    print("documents loaded:", len(data.doc))
    print("files:", sorted(os.listdir(data.processed_dir)))
    for split in ("train", "test"):                  # fine-tuning datasets (prepare_sft.py) only
        raw, proc = getattr(data, f"raw_{split}_data", None), getattr(data, f"{split}_data", None)
        if raw is not None and proc is not None:
            print(f"{split} pairs: {len(proc)} of {len(raw)} kept by gfmrag"
                  + ("" if len(proc) == len(raw) else "  <- some skipped (no start or target node); see warnings"))


if __name__ == "__main__":
    main()
