import hashlib
import json

import faiss
import numpy as np

from . import config


def build_index(vectors: np.ndarray) -> faiss.IndexFlatIP:
    # vectors are L2-normalized, so inner product == cosine similarity
    idx = faiss.IndexFlatIP(vectors.shape[1])
    idx.add(vectors)
    return idx


def _fingerprint(chunks) -> str:
    h = hashlib.sha1()
    for c in chunks:
        h.update(c.chunk_id.encode())
        h.update(c.text.encode())
    return h.hexdigest()[:12]


def load_or_build(encoder, chunks):
    """Cache index on disk keyed by encoder + chunk content, so swapping chunks.jsonl rebuilds automatically."""
    d = config.INDEX_DIR / f"{encoder.key}-{_fingerprint(chunks)}"
    f = d / "index.faiss"
    if f.exists():
        return faiss.read_index(str(f))
    vecs = encoder.encode_docs([c.text for c in chunks])
    idx = build_index(vecs)
    d.mkdir(parents=True, exist_ok=True)
    faiss.write_index(idx, str(f))
    (d / "meta.json").write_text(json.dumps({"encoder": encoder.name, "n": len(chunks)}))
    return idx
