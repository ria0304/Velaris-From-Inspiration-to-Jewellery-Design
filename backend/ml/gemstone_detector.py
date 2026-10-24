"""
backend/ml/gemstone_detector.py

Module 3 — Gemstone Detection (hybrid backend, patent-favourable design)

Detects and localizes gemstones (Diamond, Emerald, Ruby, Sapphire) in an
uploaded jewelry image. Unlike Modules 1 and 2 (whole-image classification),
this is object detection — it returns bounding boxes, not just a single
label.

Two backends, strict preference order:
  1. YOLOv8 (supervised, finetuned) — used when finetuned weights exist at
     GEMSTONE_DETECTOR_WEIGHTS. Highest accuracy on jewelry imagery, but
     requires a labeled bounding-box dataset (see
     ml_training/prepare_gemstone_dataset.py).
  2. OWL-ViT (open-vocabulary, zero-shot) — label-free fallback. Prompts a
     frozen vision-language detector with the four stone names, so the
     module works with zero training data and zero keys. Weaker than a
     finetuned YOLO on niche imagery (report this honestly), but a
     legitimate and increasingly standard technique.

Callers see one contract either way: [{label, confidence, box}].
Fails soft like Modules 1 and 2: neither backend available -> False.
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
# Zero-shot OWL-ViT scores run much lower than a finetuned YOLO's, so the
# default threshold is backend-aware: strict for YOLO, lenient for OWL-ViT.
# Explicit GEMSTONE_DETECTOR_CONF env always wins.
OWL_DEFAULT_THRESHOLD = 0.15


def effective_threshold() -> float:
    """Threshold callers (design.py hint filter) should use. No model load."""
    if os.getenv("GEMSTONE_DETECTOR_CONF"):
        return CONFIDENCE_THRESHOLD
    if os.path.exists(WEIGHTS_PATH):
        return CONFIDENCE_THRESHOLD  # YOLO path — strict is fine
    return OWL_DEFAULT_THRESHOLD  # OWL-ViT path — scores run ~0.15-0.25

OWL_MODEL_NAME = os.getenv("GEMSTONE_OWL_MODEL", "google/owlvit-base-patch32")
# Text prompts per species — descriptive prompts beat bare nouns for OWL-ViT.
OWL_PROMPTS = {
    "Diamond": ["a diamond gemstone", "a clear brilliant-cut gem"],
    "Emerald": ["an emerald green gemstone"],
    "Ruby": ["a ruby red gemstone"],
    "Sapphire": ["a sapphire blue gemstone"],
}

try:
    from ultralytics import YOLO
    from PIL import Image

    _ULTRALYTICS_AVAILABLE = True
except ImportError:
    _ULTRALYTICS_AVAILABLE = False
    print(
        "[gemstone_detector] ultralytics not installed — YOLO backend disabled. "
        "pip install ultralytics to enable it."
    )

try:
    import torch
    from transformers import OwlViTProcessor, OwlViTForObjectDetection

    _OWL_AVAILABLE = True
except ImportError:
    _OWL_AVAILABLE = False
    print(
        "[gemstone_detector] transformers/torch not installed — OWL-ViT backend disabled."
    )

# Class-specific confidence thresholds (lower for OWL-ViT, higher for YOLO)
CLASS_THRESHOLDS = {
    "Diamond": 0.25,
    "Emerald": 0.25,
    "Ruby": 0.25,
    "Sapphire": 0.25,
}


class GemstoneDetector:
    """Loads once per process, reused across requests. Fails soft.

    Backend selection (documented for paper + patent):
      - YOLO weights present -> backend="yolo" (supervised, preferred).
      - Else OWL-ViT zero-shot -> backend="owlvit" (label-free fallback).
      - Else available=False.
    """

    _instance: Optional["GemstoneDetector"] = None

    def __init__(self):
        self.available = False
        self.backend: Optional[str] = None
        self.model = None
        self.owl_processor = None

        # Backend 1 — finetuned YOLO (preferred when weights exist).
        if _ULTRALYTICS_AVAILABLE and os.path.exists(WEIGHTS_PATH):
            try:
                self.model = YOLO(WEIGHTS_PATH)
                self.available = True
                self.backend = "yolo"
                print(f"[gemstone_detector] YOLO backend loaded from {WEIGHTS_PATH}")
                return
            except Exception as exc:
                print(f"[gemstone_detector] YOLO load failed ({exc}) — trying OWL-ViT.")
        elif _ULTRALYTICS_AVAILABLE:
            print(
                f"[gemstone_detector] YOLO weights not found at {WEIGHTS_PATH} — "
                "using OWL-ViT zero-shot backend. Train YOLO with: "
                "python ml_training/train_gemstone_detector.py"
            )

        # Backend 2 — OWL-ViT open-vocabulary, zero training data / keys.
        if _OWL_AVAILABLE:
            try:
                from PIL import Image  # noqa: F401 (ensures PIL present)

                self.owl_processor = OwlViTProcessor.from_pretrained(OWL_MODEL_NAME)
                self.model = OwlViTForObjectDetection.from_pretrained(OWL_MODEL_NAME)
                self.model.eval()
                self.available = True
                self.backend = "owlvit"
                print(f"[gemstone_detector] OWL-ViT backend loaded ({OWL_MODEL_NAME})")
            except Exception as exc:
                print(f"[gemstone_detector] OWL-ViT load failed: {exc}")
                self.model = None

    @classmethod
    def get(cls) -> "GemstoneDetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, image_b64: str) -> Optional[List[Dict]]:
        """Returns a list of {label, confidence, box: [x1,y1,x2,y2], backend}
        or None if unavailable/failed. Same contract for both backends."""
        if not self.available:
            return None

        try:
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(image_b64)
            from PIL import Image

            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as exc:
            print(f"[gemstone_detector] Failed to decode image: {exc}")
            return None

        if self.backend == "yolo":
            return self._predict_yolo(image)
        return self._predict_owl(image)

    def _predict_yolo(self, image) -> List[Dict]:
        import torch
        
        # Test-time augmentation: predict on original + flipped image, average results
        results_orig = self.model.predict(image, conf=CONFIDENCE_THRESHOLD, verbose=False)
        results_flip = self.model.predict(image.transpose(Image.FLIP_LEFT_RIGHT), 
                                         conf=CONFIDENCE_THRESHOLD, verbose=False)
        
        detections: List[Dict] = []
        names = results_orig[0].names if results_orig else {}
        
        # Process original image detections
        if results_orig and len(results_orig) > 0:
            for box in results_orig[0].boxes:
                cls_id = int(box.cls.item())
                confidence = float(box.conf.item())
                xyxy = box.xyxy.squeeze().tolist()
                detections.append(
                    {
                        "label": names[cls_id].title(),
                        "confidence": confidence,
                        "box": [round(v, 1) for v in xyxy],
                        "backend": "yolo",
                    }
                )
        
        # Process flipped image detections (flip back the boxes)
        if results_flip and len(results_flip) > 0:
            w = image.size[0]
            for box in results_flip[0].boxes:
                cls_id = int(box.cls.item())
                confidence = float(box.conf.item())
                xyxy = box.xyxy.squeeze().tolist()
                # Flip the x coordinates back: x1' = w - x2, x2' = w - x1
                xyxy_flipped = [w - xyxy[2], xyxy[1], w - xyxy[0], xyxy[3]]
                detections.append(
                    {
                        "label": names[cls_id].title(),
                        "confidence": confidence,
                        "box": [round(v, 1) for v in xyxy_flipped],
                        "backend": "yolo",
                    }
                )
        
        # Average confidences for duplicate detections (same label + close boxes)
        seen: set = set()
        final: List[Dict] = []
        for det in detections:
            key = (det["label"], tuple(det["box"]))
            if key not in seen:
                seen.add(key)
                # Count how many times this label appears
                count = sum(1 for d in detections if d["label"] == det["label"] 
                           and abs(d["box"][0] - det["box"][0]) < 5 
                           and abs(d["box"][1] - det["box"][1]) < 5)
                # Average confidence
                avg_conf = sum(d["confidence"] for d in detections 
                              if d["label"] == det["label"]) / max(count, 1)
                final.append(
                    {
                        "label": det["label"],
                        "confidence": round(avg_conf, 3),
                        "box": det["box"],
                        "backend": "yolo",
                    }
                )
        return final

    def _predict_owl(self, image) -> Optional[List[Dict]]:
        """Zero-shot: one query per species prompt, keep boxes >= threshold,
        non-max suppression across prompts by keeping the top label per box."""
        import torch

        w, h = image.size
        candidates: List[Dict] = []
        try:
            for label, prompts in OWL_PROMPTS.items():
                # Use class-specific threshold for this gem type
                thr = CLASS_THRESHOLDS.get(label, effective_threshold())
                inputs = self.owl_processor(text=prompts, images=image, return_tensors="pt")
                with torch.no_grad():
                    outputs = self.model(**inputs)
                target_sizes = torch.tensor([[h, w]])
                # transformers>=5 moved post-processing onto image_processor.
                post = getattr(self.owl_processor, "post_process_object_detection", None)
                if post is None and hasattr(self.owl_processor, "image_processor"):
                    post = self.owl_processor.image_processor.post_process_object_detection
                results = post(
                    outputs, threshold=thr, target_sizes=target_sizes
                )[0]
                for score, box in zip(results["scores"], results["boxes"]):
                    x1, y1, x2, y2 = (round(float(v), 1) for v in box.tolist())
                    candidates.append(
                        {"label": label, "confidence": float(score.item()),
                         "box": [x1, y1, x2, y2], "backend": "owlvit"}
                    )
        except Exception as exc:
            print(f"[gemstone_detector] OWL-ViT inference failed: {exc}")
            return None

        # Greedy IoU dedup: overlapping boxes keep the highest-confidence label.
        kept: List[Dict] = []
        for cand in sorted(candidates, key=lambda d: d["confidence"], reverse=True):
            if all(_iou(cand["box"], k["box"]) < 0.5 for k in kept):
                kept.append(cand)
        return kept


def _iou(a: List[float], b: List[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    ua = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / ua if ua > 0 else 0.0


def detect_gemstones(image_b64: str) -> Optional[List[Dict]]:
    detector = GemstoneDetector.get()
    return detector.predict(image_b64)
