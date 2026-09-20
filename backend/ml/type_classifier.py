"""
backend/ml/type_classifier.py

Module 1 — Jewelry Type Classification (CNN, transfer learning)

Wraps a fine-tuned EfficientNet-B0 model that classifies a jewelry image
into one of the four classes it was trained on: Bracelet, Earrings,
Necklace, Ring.

The model is trained offline — see ml_training/train_type_classifier.py.
The checkpoint is NOT bundled with the repo (weights are too large for
git); train it locally first, then either drop the resulting files at
backend/ml/checkpoints/, or point TYPE_CLASSIFIER_CHECKPOINT /
TYPE_CLASSIFIER_CLASSES at wherever you saved them.

Velaris only trusts this classifier for the four types it was trained on.
Brooch / Pendant / Tiara requests still fall back to the existing
keyword-based extraction in design.py, since no labeled training data
exists for those classes (see README, "Module 1" section, for why).

Loading is lazy and fails soft: if the checkpoint isn't there, or torch
isn't installed, `available` is False and callers fall back to the
text-based type extraction that already exists in design.py. Nothing
breaks if this module was never trained.
"""

import base64
import io
import json
import os
from pathlib import Path
from typing import Dict, Optional

_MODULE_DIR = Path(__file__).parent

CHECKPOINT_PATH = os.getenv(
    "TYPE_CLASSIFIER_CHECKPOINT", str(_MODULE_DIR / "checkpoints" / "type_classifier.pt")
)
CLASS_MAP_PATH = os.getenv(
    "TYPE_CLASSIFIER_CLASSES", str(_MODULE_DIR / "checkpoints" / "class_to_idx.json")
)

# Below this, design.py should not trust the prediction and should fall
# back to the text-based heuristic instead.
CONFIDENCE_THRESHOLD = 0.55

_IMG_SIZE = 224

# Maps the dataset's raw class folder names to the exact enum strings
# Velaris already uses in schemas.py / src/types.ts, so no other file
# needs to change to consume this.
_LABEL_TO_VELARIS_TYPE = {
    "ring": "Ring",
    "necklace": "Necklace",
    "bracelet": "Bracelet",
    "earring": "Earrings",
    "earrings": "Earrings",
}

try:
    import torch
    from torch import nn
    from torchvision import models, transforms
    from PIL import Image

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    print(
        "[type_classifier] torch/torchvision not installed — Module 1 disabled. "
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


class JewelryTypeClassifier:
    """Loads once per process, reused across requests. Fails soft."""

    _instance: Optional["JewelryTypeClassifier"] = None

    def __init__(self):
        self.available = False
        self.model = None
        self.idx_to_class: Dict[int, str] = {}

        if not _TORCH_AVAILABLE:
            return

        if not (os.path.exists(CHECKPOINT_PATH) and os.path.exists(CLASS_MAP_PATH)):
            print(
                f"[type_classifier] Checkpoint not found at {CHECKPOINT_PATH}. "
                "Module 1 disabled — falling back to text-based type extraction. "
                "Train it with: python ml_training/train_type_classifier.py"
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
            print(f"[type_classifier] Loaded checkpoint. Classes: {list(class_to_idx.keys())}")
        except Exception as exc:
            print(f"[type_classifier] Failed to load checkpoint: {exc}")

    @classmethod
    def get(cls) -> "JewelryTypeClassifier":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, image_b64: str) -> Optional[Dict]:
        """Returns {type, confidence, probabilities} or None if unavailable/failed."""
        if not self.available:
            return None

        try:
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as exc:
            print(f"[type_classifier] Failed to decode image: {exc}")
            return None

        tensor = _TRANSFORM(image).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0)

        top_idx = int(torch.argmax(probs).item())
        top_label = self.idx_to_class[top_idx]
        confidence = float(probs[top_idx].item())

        return {
            "type": _LABEL_TO_VELARIS_TYPE.get(top_label, top_label.title()),
            "confidence": confidence,
            "probabilities": {
                _LABEL_TO_VELARIS_TYPE.get(self.idx_to_class[i], self.idx_to_class[i].title()): float(p)
                for i, p in enumerate(probs.tolist())
            },
        }


def classify_type_from_image(image_b64: str) -> Optional[Dict]:
    """Convenience function used by design.py and the /api/classify-type endpoint."""
    classifier = JewelryTypeClassifier.get()
    return classifier.predict(image_b64)
