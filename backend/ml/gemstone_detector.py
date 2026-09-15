"""
backend/ml/gemstone_detector.py

Module 3 — Gemstone Detection (YOLOv8 object detection)

Detects and localizes gemstones (Diamond, Emerald, Ruby, Sapphire) in an
uploaded jewelry image. Unlike Modules 1 and 2 (whole-image classification),
this is object detection — it returns bounding boxes, not just a single
label, which is the actual reason YOLO instead of a CNN classifier here.

Trained offline on a Roboflow gemstone dataset (see
ml_training/prepare_gemstone_dataset.py and train_gemstone_detector.py).
Fails soft exactly like Modules 1 and 2: no checkpoint / no ultralytics ->
`available = False`.
"""

import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional

_MODULE_DIR = Path(__file__).parent

WEIGHTS_PATH = os.getenv(
    "GEMSTONE_DETECTOR_WEIGHTS", str(_MODULE_DIR / "checkpoints" / "gemstone_detector.pt")
)
CONFIDENCE_THRESHOLD = float(os.getenv("GEMSTONE_DETECTOR_CONF", "0.35"))

try:
    from ultralytics import YOLO
    from PIL import Image

    _ULTRALYTICS_AVAILABLE = True
except ImportError:
    _ULTRALYTICS_AVAILABLE = False
    print(
        "[gemstone_detector] ultralytics not installed — Module 3 disabled. "
        "pip install ultralytics to enable it."
    )


class GemstoneDetector:
    """Loads once per process, reused across requests. Fails soft."""

    _instance: Optional["GemstoneDetector"] = None

    def __init__(self):
        self.available = False
        self.model = None

        if not _ULTRALYTICS_AVAILABLE:
            return

        if not os.path.exists(WEIGHTS_PATH):
            print(
                f"[gemstone_detector] Weights not found at {WEIGHTS_PATH}. "
                "Module 3 disabled. Train it with: python ml_training/train_gemstone_detector.py"
            )
            return

        try:
            self.model = YOLO(WEIGHTS_PATH)
            self.available = True
            print(f"[gemstone_detector] Loaded weights from {WEIGHTS_PATH}")
        except Exception as exc:
            print(f"[gemstone_detector] Failed to load weights: {exc}")

    @classmethod
    def get(cls) -> "GemstoneDetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, image_b64: str) -> Optional[List[Dict]]:
        """Returns a list of {label, confidence, box: [x1,y1,x2,y2]} or None if unavailable/failed."""
        if not self.available:
            return None

        try:
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as exc:
            print(f"[gemstone_detector] Failed to decode image: {exc}")
            return None

        results = self.model.predict(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
        detections = []
        for result in results:
            names = result.names
            for box in result.boxes:
                cls_id = int(box.cls.item())
                confidence = float(box.conf.item())
                xyxy = box.xyxy.squeeze().tolist()
                detections.append(
                    {
                        "label": names[cls_id].title(),
                        "confidence": confidence,
                        "box": [round(v, 1) for v in xyxy],
                    }
                )

        return detections


def detect_gemstones(image_b64: str) -> Optional[List[Dict]]:
    detector = GemstoneDetector.get()
    return detector.predict(image_b64)
