"""
backend/ml/style_classifier.py

Module 2 — Jewelry Style Recognition (CNN, transfer learning)

Same architecture pattern as Module 1 (EfficientNet-B0, transfer learning),
but a BINARY classifier: Traditional/Temple vs Modern/Minimal.

Why binary and not the original 5-class plan (Vintage/Minimal/Temple/
Modern/Luxury): there's no public dataset with clean, consistently-applied
style labels — "vintage" vs "luxury" vs "modern" is subjective even to
human labelers, and hand-labeling 5 fuzzy classes is exactly the manual
labeling work we're trying to avoid (see ml_training/prepare_style_dataset.py
for how the binary labels are derived instead, from caption keywords).
Two visually distinct buckets is a much more defensible classification
task, and the low(er) accuracy you'll likely see even on two classes is
itself a legitimate point to raise in the report under CO5 (limitations).

Fails soft exactly like type_classifier.py: no checkpoint / no torch ->
`available = False`, callers should treat style as unknown rather than error.
"""

import base64
import io
import json
import os
from pathlib import Path
from typing import Dict, Optional

_MODULE_DIR = Path(__file__).parent

CHECKPOINT_PATH = os.getenv(
    "STYLE_CLASSIFIER_CHECKPOINT", str(_MODULE_DIR / "checkpoints" / "style_classifier.pt")
)
CLASS_MAP_PATH = os.getenv(
    "STYLE_CLASSIFIER_CLASSES", str(_MODULE_DIR / "checkpoints" / "style_class_to_idx.json")
)

CONFIDENCE_THRESHOLD = 0.55
_IMG_SIZE = 224

try:
    import torch
    from torch import nn
    from torchvision import models, transforms
    from PIL import Image

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    print(
        "[style_classifier] torch/torchvision not installed — Module 2 disabled. "
        "pip install torch torchvision to enable it."
    )

if _TORCH_AVAILABLE:
    _TRANSFORM = transforms.Compose(
        [
            transforms.Resize((_IMG_SIZE, _IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


class JewelryStyleClassifier:
    """Loads once per process, reused across requests. Fails soft."""

    _instance: Optional["JewelryStyleClassifier"] = None

    def __init__(self):
        self.available = False
        self.model = None
        self.idx_to_class: Dict[int, str] = {}

        if not _TORCH_AVAILABLE:
            return

        if not (os.path.exists(CHECKPOINT_PATH) and os.path.exists(CLASS_MAP_PATH)):
            print(
                f"[style_classifier] Checkpoint not found at {CHECKPOINT_PATH}. "
                "Module 2 disabled. Train it with: python ml_training/train_style_classifier.py"
            )
            return

        try:
            with open(CLASS_MAP_PATH) as f:
                class_to_idx = json.load(f)
            self.idx_to_class = {v: k for k, v in class_to_idx.items()}

            model = models.efficientnet_b0(weights=None)
            model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(class_to_idx))
            state_dict = torch.load(CHECKPOINT_PATH, map_location="cpu")
            model.load_state_dict(state_dict)
            model.eval()

            self.model = model
            self.available = True
            print(f"[style_classifier] Loaded checkpoint. Classes: {list(class_to_idx.keys())}")
        except Exception as exc:
            print(f"[style_classifier] Failed to load checkpoint: {exc}")

    @classmethod
    def get(cls) -> "JewelryStyleClassifier":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, image_b64: str) -> Optional[Dict]:
        if not self.available:
            return None

        try:
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as exc:
            print(f"[style_classifier] Failed to decode image: {exc}")
            return None

        tensor = _TRANSFORM(image).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0)

        top_idx = int(torch.argmax(probs).item())
        top_label = self.idx_to_class[top_idx]
        confidence = float(probs[top_idx].item())

        return {
            "style": top_label.replace("_", " ").title(),
            "confidence": confidence,
            "probabilities": {
                self.idx_to_class[i].replace("_", " ").title(): float(p)
                for i, p in enumerate(probs.tolist())
            },
        }


def classify_style_from_image(image_b64: str) -> Optional[Dict]:
    classifier = JewelryStyleClassifier.get()
    return classifier.predict(image_b64)
