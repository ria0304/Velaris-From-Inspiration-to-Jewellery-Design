"""
backend/ml/similarity_search.py

Module 4 — Similarity Search (CLIP embeddings)

No training involved here — this uses a pretrained CLIP model
(openai/clip-vit-base-patch32) purely for inference. What you build is the
index: embed a pool of reference jewelry images once (offline, see
ml_training/build_similarity_index.py), then at request time embed the
user's uploaded image and return the closest matches by cosine similarity.

This is the cheapest module to implement correctly and the one that most
directly demonstrates "transformers in practice" for the report, since
CLIP's image encoder is a ViT (Vision Transformer).

Fails soft like the others: no index file / no torch+transformers ->
`available = False`.
"""

import base64
import io
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

_MODULE_DIR = Path(__file__).parent

INDEX_EMBEDDINGS_PATH = os.getenv(
    "SIMILARITY_INDEX_EMBEDDINGS", str(_MODULE_DIR / "checkpoints" / "similarity_embeddings.npy")
)
INDEX_METADATA_PATH = os.getenv(
    "SIMILARITY_INDEX_METADATA", str(_MODULE_DIR / "checkpoints" / "similarity_metadata.json")
)
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

try:
    import torch
    from transformers import CLIPModel, CLIPProcessor
    from PIL import Image

    _CLIP_AVAILABLE = True
except ImportError:
    _CLIP_AVAILABLE = False
    print(
        "[similarity_search] transformers/torch not installed — Module 4 disabled. "
        "pip install transformers to enable it."
    )


class SimilaritySearch:
    """Loads once per process, reused across requests. Fails soft."""

    _instance: Optional["SimilaritySearch"] = None

    def __init__(self):
        self.available = False
        self.model = None
        self.processor = None
        self.embeddings: Optional[np.ndarray] = None  # shape (N, D), L2-normalized
        self.metadata: List[Dict] = []  # parallel list, e.g. [{"path": ..., "type": ...}, ...]

        if not _CLIP_AVAILABLE:
            return

        if not (os.path.exists(INDEX_EMBEDDINGS_PATH) and os.path.exists(INDEX_METADATA_PATH)):
            print(
                f"[similarity_search] Index not found at {INDEX_EMBEDDINGS_PATH}. "
                "Module 4 disabled. Build it with: python ml_training/build_similarity_index.py"
            )
            return

        try:
            self.model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
            self.processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
            self.model.eval()

            self.embeddings = np.load(INDEX_EMBEDDINGS_PATH)
            with open(INDEX_METADATA_PATH) as f:
                self.metadata = json.load(f)

            self.available = True
            print(f"[similarity_search] Loaded index with {len(self.metadata)} reference images")
        except Exception as exc:
            print(f"[similarity_search] Failed to load: {exc}")

    @classmethod
    def get(cls) -> "SimilaritySearch":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _embed(self, image: "Image.Image") -> np.ndarray:
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            features = self.model.get_image_features(**inputs)
        # transformers>=5 returns an output object instead of a tensor —
        # unwrap whichever embedding field the installed version provides.
        embeds = features
        for attr in ("image_embeds", "pooler_output"):
            if hasattr(embeds, attr):
                embeds = getattr(embeds, attr)
                break
        else:
            if hasattr(embeds, "last_hidden_state"):
                embeds = embeds.last_hidden_state.mean(dim=1)
        vec = embeds.squeeze(0) if isinstance(embeds, torch.Tensor) else torch.as_tensor(embeds).squeeze(0)
        vec = vec.detach().cpu().numpy()
        return vec / (np.linalg.norm(vec) + 1e-8)

    def search(self, image_b64: str, top_k: int = 5) -> Optional[List[Dict]]:
        if not self.available:
            return None

        try:
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as exc:
            print(f"[similarity_search] Failed to decode image: {exc}")
            return None

        query_vec = self._embed(image)
        similarities = self.embeddings @ query_vec  # cosine similarity, both sides L2-normalized

        top_indices = np.argsort(-similarities)[:top_k]
        return [
            {**self.metadata[i], "similarity": float(similarities[i])}
            for i in top_indices
        ]


def find_similar(image_b64: str, top_k: int = 5) -> Optional[List[Dict]]:
    searcher = SimilaritySearch.get()
    return searcher.search(image_b64, top_k=top_k)
