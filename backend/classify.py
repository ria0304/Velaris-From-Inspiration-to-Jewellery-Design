"""backend/classify.py

Standalone endpoint for Module 1 (jewelry type classification). Useful
for the DL course demo/evaluation independent of the full design-generation
flow — hit this directly with any jewelry image to see the CNN's raw
prediction and per-class confidence, without touching OpenRouter at all.

design.py also calls into backend.ml.type_classifier directly to use this
model as a pre-processing step ahead of the LLM design generation call.
"""

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .ml.type_classifier import JewelryTypeClassifier

router = APIRouter()


class ClassifyRequest(BaseModel):
    image: str  # base64 image data, with or without the data:image/... prefix


class ClassifyResponse(BaseModel):
    available: bool
    type: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    message: str


@router.post("/api/classify-type", response_model=ClassifyResponse)
def classify_type(request: ClassifyRequest) -> ClassifyResponse:
    """Classify a jewelry image as Ring / Necklace / Bracelet / Earrings."""
    classifier = JewelryTypeClassifier.get()

    if not classifier.available:
        return ClassifyResponse(
            available=False,
            message=(
                "Type classifier checkpoint not found. Train it with "
                "'python ml_training/train_type_classifier.py', then restart the backend."
            ),
        )

    result = classifier.predict(request.image)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to classify image — check that it's a valid base64-encoded image.",
        )

    return ClassifyResponse(
        available=True,
        type=result["type"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        message=f"Predicted {result['type']} with {result['confidence']:.1%} confidence",
    )
