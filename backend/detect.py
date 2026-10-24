"""backend/detect.py

Standalone endpoint for Module 3 (gemstone detection). Returns bounding
boxes + labels + confidence for any gemstones YOLO finds in the image —
useful on its own for the DL course demo, and also called from design.py
to pass detected stones into the LLM prompt as a hint.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .ml.gemstone_detector import GemstoneDetector

router = APIRouter()


class DetectRequest(BaseModel):
    image: str  # base64 image data


class Detection(BaseModel):
    label: str
    confidence: float
    box: List[float]  # [x1, y1, x2, y2] in pixels
    backend: Optional[str] = None  # "yolo" (finetuned) or "owlvit" (zero-shot)


class DetectResponse(BaseModel):
    available: bool
    detections: Optional[List[Detection]] = None
    message: str


@router.post("/api/detect-gemstones", response_model=DetectResponse)
def detect_gemstones_endpoint(request: DetectRequest) -> DetectResponse:
    """Detect and localize gemstones (Diamond/Emerald/Ruby/Sapphire) in an image."""
    detector = GemstoneDetector.get()

    if not detector.available:
        return DetectResponse(
            available=False,
            message=(
                "Gemstone detector weights not found. Train it with "
                "'python ml_training/train_gemstone_detector.py', then restart the backend."
            ),
        )

    result = detector.predict(request.image)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to run detection — check that the image is valid base64.",
        )

    return DetectResponse(
        available=True,
        detections=result,
        message=f"Found {len(result)} gemstone(s)" if result else "No gemstones detected",
    )
