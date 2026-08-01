"""backend/similar.py

Standalone endpoint for Module 4 (CLIP similarity search). Given an
uploaded image, returns the top-k most visually similar reference images
from the index built by ml_training/build_similarity_index.py — useful for
"here's what's already out there" in the differentiate-mode flow, and as
a standalone demo of transformer-based (ViT) embeddings for the report.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .ml.similarity_search import SimilaritySearch

router = APIRouter()


class SimilarRequest(BaseModel):
    image: str  # base64 image data
    top_k: int = 5


class SimilarMatch(BaseModel):
    path: str
    type: str
    similarity: float


class SimilarResponse(BaseModel):
    available: bool
    matches: Optional[List[SimilarMatch]] = None
    message: str


@router.post("/api/find-similar", response_model=SimilarResponse)
def find_similar_endpoint(request: SimilarRequest) -> SimilarResponse:
    """Find visually similar reference jewelry images using CLIP embeddings."""
    searcher = SimilaritySearch.get()

    if not searcher.available:
        return SimilarResponse(
            available=False,
            message=(
                "Similarity index not found. Build it with "
                "'python ml_training/build_similarity_index.py', then restart the backend."
            ),
        )

    result = searcher.search(request.image, top_k=request.top_k)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to run similarity search — check that the image is valid base64.",
        )

    return SimilarResponse(
        available=True,
        matches=result,
        message=f"Found {len(result)} similar image(s)",
    )
