from functools import lru_cache
from threading import Lock

import numpy as np

from backend.config import settings


class Embedder:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        try:
            self.model = SentenceTransformer(settings().embedding_model, local_files_only=True)
        except OSError:
            self.model = SentenceTransformer(settings().embedding_model)
        self.lock = Lock()

    def encode(self, texts: list[str]) -> np.ndarray:
        # No persistent cache of personal document contents.
        with self.lock:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False,
                                     convert_to_numpy=True, batch_size=32)


@lru_cache
def get_embedder() -> Embedder:
    return Embedder()

