"""Sentence embeddings with the official ONNX export of all-MiniLM-L6-v2.

Same weights and same computation as sentence-transformers (mean pooling over the last hidden
state, then L2 normalisation), but run with onnxruntime instead of PyTorch: about 90 MB of
dependencies instead of several GB, so the identical model runs locally and on Vercel.
"""
from functools import lru_cache
from threading import Lock

import numpy as np

from backend.config import settings

MAX_TOKENS = 256  # Same truncation as the sentence-transformers configuration of this model.


def _download(filename: str) -> str:
    from huggingface_hub import hf_hub_download
    try:
        return hf_hub_download(settings().embedding_model, filename, local_files_only=True)
    except (OSError, ValueError):  # LocalEntryNotFoundError: not cached yet: the first launch downloads it once (~90 MB).
        return hf_hub_download(settings().embedding_model, filename)


class Embedder:
    def __init__(self):
        import onnxruntime
        from tokenizers import Tokenizer

        self.tokenizer = Tokenizer.from_file(_download("tokenizer.json"))
        self.tokenizer.enable_truncation(MAX_TOKENS)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = onnxruntime.SessionOptions()
        options.log_severity_level = 3
        self.session = onnxruntime.InferenceSession(_download("onnx/model.onnx"), options,
                                                    providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.session.get_inputs()}
        self.lock = Lock()

    def encode(self, texts: list[str]) -> np.ndarray:
        # No persistent cache of personal document contents.
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        out = []
        with self.lock:
            for start in range(0, len(texts), 32):
                batch = self.tokenizer.encode_batch(texts[start:start + 32])
                ids = np.array([e.ids for e in batch], dtype=np.int64)
                mask = np.array([e.attention_mask for e in batch], dtype=np.int64)
                feeds = {"input_ids": ids, "attention_mask": mask, "token_type_ids": np.zeros_like(ids)}
                hidden = self.session.run(None, {k: v for k, v in feeds.items() if k in self.inputs})[0]
                weights = mask[..., None].astype(np.float32)
                pooled = (hidden * weights).sum(1) / np.clip(weights.sum(1), 1e-9, None)
                out.append(pooled / np.clip(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None))
        return np.vstack(out).astype(np.float32)


@lru_cache
def get_embedder() -> Embedder:
    return Embedder()
