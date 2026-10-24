"""backend/style.py

Standalone endpoint for Module 2 (style recognition). Same pattern as
classify.py (Module 1) — useful for demoing/evaluating this model on its
own, independent of the full design-generation flow.
"""

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .ml.style_classifier import JewelryStyleClassifier

router = APIRouter()


class StyleRequest(BaseModel):
    image: str  # base64 image data


class StyleResponse(BaseModel):
    available: bool
    style: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    message: str


@router.post("/api/classify-style", response_model=StyleResponse)
def classify_style(request: StyleRequest) -> StyleResponse:
    """Classify a jewelry image as Traditional or Modern."""
    classifier = JewelryStyleClassifier.get()

    if not classifier.available:
        return StyleResponse(
            available=False,
            message=(
                "Style classifier checkpoint not found. Train it with "
                "'python ml_training/train_style_classifier.py', then restart the backend."
            ),
        )

    result = classifier.predict(request.image)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to classify image — check that it's a valid base64-encoded image.",
        )

    return StyleResponse(
        available=True,
        style=result["style"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        message=f"Predicted {result['style']} with {result['confidence']:.1%} confidence",
    )
