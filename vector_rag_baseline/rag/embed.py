import numpy as np
from sentence_transformers import SentenceTransformer

from . import config


class Encoder:
    def __init__(self, key: str):
        spec = config.ENCODERS[key]
        self.key, self.name, self.query_prefix = key, spec["name"], spec["query_prefix"]
        self.model = SentenceTransformer(self.name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def _enc(self, texts, batch_size=32):
        v = self.model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True
        )
        return np.ascontiguousarray(v, dtype="float32")

    def encode_docs(self, texts):
        return self._enc(texts)

    def encode_queries(self, queries):
        return self._enc([self.query_prefix + q for q in queries])
