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

_IMG_SIZE = 300  # increased for larger model

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
    # RandAugment augmentation policy (N=2, M=10)
    _RAND_AUGMENT = transforms.RandAugment(num_ops=2, magnitude=10)
    _BASE_TRANSFORM = transforms.Compose(
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

    def predict(self, image_b64: str, tta: bool = True) -> Optional[Dict]:
        """Returns {type, confidence, probabilities} or None if unavailable/failed.
        
        tta: if True, applies Test-Time Augmentation by averaging predictions
        over 5 transformations (original + 4 rotations: 90, 180, 270, flip).
        """
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

        if tta:
            # Test-Time Augmentation: average predictions over 5 transformations
            probs_sum = None
            for angle in [0, 90, 180, 270]:
                transformed = self._rotate_image(image, angle)
                tensor = _TRANSFORM(transformed).unsqueeze(0)
                with torch.no_grad():
                    logits = self.model(tensor)
                    probs = torch.softmax(logits, dim=1).squeeze(0)
                if probs_sum is None:
                    probs_sum = probs
                else:
                    probs_sum = probs_sum + probs
            # Also include horizontal flip
            flipped = self._flip_image(image)
            tensor = _TRANSFORM(flipped).unsqueeze(0)
            with torch.no_grad():
                logits = self.model(tensor)
                probs = torch.softmax(logits, dim=1).squeeze(0)
            if probs_sum is None:
                probs_sum = probs
            else:
                probs_sum = probs_sum + probs
            avg_probs = probs_sum / 5.0
        else:
            # Single inference without TTA
            tensor = _TRANSFORM(image).unsqueeze(0)
            with torch.no_grad():
                logits = self.model(tensor)
                avg_probs = torch.softmax(logits, dim=1).squeeze(0)

        top_idx = int(torch.argmax(avg_probs).item())
        top_label = self.idx_to_class[top_idx]
        confidence = float(avg_probs[top_idx].item())

        # Apply temperature scaling for confidence calibration
        # Temperature of 1.5 slightly lowers overconfident predictions
        temp = 1.5
        calibrated_probs = torch.softmax(avg_probs / temp, dim=0)
        confidence = float(calibrated_probs[top_idx].item())

        return {
            "type": _LABEL_TO_VELARIS_TYPE.get(top_label, top_label.title()),
            "confidence": confidence,
            "probabilities": {
                _LABEL_TO_VELARIS_TYPE.get(self.idx_to_class[i], self.idx_to_class[i].title()): float(p)
                for i, p in enumerate(calibrated_probs.tolist())
            },
        }

    @staticmethod
    def _rotate_image(image: Image.Image, angle: int) -> Image.Image:
        """Rotate image by angle and expand to avoid cropping."""
        return image.rotate(angle, expand=True)

    @staticmethod
    def _flip_image(image: Image.Image) -> Image.Image:
        """Horizontal flip for augmentation."""
        return image.transpose(Image.FLIP_LEFT_RIGHT)


def classify_type_from_image(image_b64: str, tta: bool = True) -> Optional[Dict]:
    """Convenience function used by design.py and the /api/classify-type endpoint."""
    classifier = JewelryTypeClassifier.get()
    return classifier.predict(image_b64, tta=tta)
