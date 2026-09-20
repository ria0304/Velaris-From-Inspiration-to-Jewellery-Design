# Velaris — From Inspiration to Jewelry Design
# Python backend entrypoint. Run with: python main.py
# or: uvicorn main:app --reload --port 3000

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import advisor, design, storage, trends
from backend.svg_generator import router as svg_router
from backend.cad.router import router as cad_router
from backend.render.router import router as realistic_router
from backend.presentation import router as presentation_router
from backend.beauty.router import router as beauty_router
from backend.pdf_generator import generate_design_pdf
from backend.schemas import PDFExportRequest, PDFExportResponse
from backend.storage import get_design_by_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("velaris")

try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    limiter = Limiter(key_func=lambda request: request.client.host if request.client else "anon")
    RATE_LIMIT_AVAILABLE = True
except ImportError:
    limiter = None
    RATE_LIMIT_AVAILABLE = False
    logger.warning("slowapi not installed — rate limiting disabled")

# ─── NEW: Import sketch processor ─────────────────────────────────────────────
try:
    from backend.sketch_processor import router as sketch_router
    SKETCH_AVAILABLE = True
except ImportError:
    SKETCH_AVAILABLE = False
    logger.warning(" sketch_processor not available. OpenCV may not be installed.")

# ─── NEW: Import Module 1 type classifier ─────────────────────────────────────
try:
    from backend.classify import router as classify_router
    from backend.ml.type_classifier import JewelryTypeClassifier
    CLASSIFY_AVAILABLE = True
except ImportError:
    CLASSIFY_AVAILABLE = False
    logger.warning(" type classifier not available. torch/torchvision may not be installed.")

# ─── NEW: Import Module 2 style classifier ────────────────────────────────────
try:
    from backend.style import router as style_router
    from backend.ml.style_classifier import JewelryStyleClassifier
    STYLE_AVAILABLE = True
except ImportError:
    STYLE_AVAILABLE = False
    logger.warning(" style classifier not available. torch/torchvision may not be installed.")

# ─── NEW: Import Module 3 gemstone detector ───────────────────────────────────
try:
    from backend.detect import router as detect_router
    from backend.ml.gemstone_detector import GemstoneDetector
    DETECT_AVAILABLE = True
except ImportError:
    DETECT_AVAILABLE = False
    logger.warning(" gemstone detector not available. ultralytics may not be installed.")

# ─── NEW: Import Module 4 similarity search ───────────────────────────────────
try:
    from backend.similar import router as similar_router
    from backend.ml.similarity_search import SimilaritySearch
    SIMILAR_AVAILABLE = True
except ImportError:
    SIMILAR_AVAILABLE = False
    logger.warning(" similarity search not available. transformers may not be installed.")

app = FastAPI(
    title="Velaris Jewelry Design Engine",
    description="FastAPI backend powered by an OpenRouter multi-model fallback chain",
    version="2.0.0",
)

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if RATE_LIMIT_AVAILABLE:
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    app.add_middleware(SlowAPIMiddleware)

# ─── Include all routers ──────────────────────────────────────────────────────
app.include_router(design.router)
app.include_router(advisor.router)
app.include_router(trends.router)
app.include_router(storage.router)
app.include_router(svg_router)
app.include_router(cad_router)
app.include_router(realistic_router)
app.include_router(presentation_router)
app.include_router(beauty_router)

# ─── Include sketch router if available ──────────────────────────────────────
if SKETCH_AVAILABLE:
    app.include_router(sketch_router)
    logger.info(" Sketch processor router loaded successfully")
else:
    logger.warning("  Sketch processor router NOT loaded (OpenCV missing)")

# ─── Include Module 1 classify router if available ────────────────────────────
if CLASSIFY_AVAILABLE:
    app.include_router(classify_router)
    _classifier_ready = JewelryTypeClassifier.get().available
    if _classifier_ready:
        logger.info(" Type classifier (Module 1) router loaded — checkpoint found")
    else:
        logger.warning("  Type classifier (Module 1) router loaded, but no checkpoint found yet")
else:
    logger.warning("  Type classifier router NOT loaded (torch/torchvision missing)")

# ─── Include Module 2 style router if available ───────────────────────────────
if STYLE_AVAILABLE:
    app.include_router(style_router)
    _style_ready = JewelryStyleClassifier.get().available
    print(
        "✅ Style classifier (Module 2) router loaded"
        + ("" if _style_ready else " — no checkpoint found yet")
    )
else:
    logger.warning("  Style classifier router NOT loaded (torch/torchvision missing)")

# ─── Include Module 3 gemstone detector router if available ───────────────────
if DETECT_AVAILABLE:
    app.include_router(detect_router)
    _detector_ready = GemstoneDetector.get().available
    print(
        "✅ Gemstone detector (Module 3) router loaded"
        + ("" if _detector_ready else " — no weights found yet")
    )
else:
    logger.warning("  Gemstone detector router NOT loaded (ultralytics missing)")

# ─── Include Module 4 similarity search router if available ───────────────────
if SIMILAR_AVAILABLE:
    app.include_router(similar_router)
    _similarity_ready = SimilaritySearch.get().available
    print(
        "✅ Similarity search (Module 4) router loaded"
        + ("" if _similarity_ready else " — no index found yet")
    )
else:
    logger.warning("  Similarity search router NOT loaded (transformers missing)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    logger.info("Velaris startup complete")
    yield


app.router.lifespan_context = lifespan


# ─── Health Check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """Check if the API is running and all dependencies are available."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "sketch_processor": SKETCH_AVAILABLE,
        "type_classifier": CLASSIFY_AVAILABLE and JewelryTypeClassifier.get().available,
        "style_classifier": STYLE_AVAILABLE and JewelryStyleClassifier.get().available,
        "gemstone_detector": DETECT_AVAILABLE and GemstoneDetector.get().available,
        "similarity_search": SIMILAR_AVAILABLE and SimilaritySearch.get().available,
        "services": {
            "design": True,
            "advisor": True,
            "trends": True,
            "storage": True,
            "svg_generator": True,
            "pdf_generator": True,
            "type_classifier": CLASSIFY_AVAILABLE,
            "style_classifier": STYLE_AVAILABLE,
            "gemstone_detector": DETECT_AVAILABLE,
            "similarity_search": SIMILAR_AVAILABLE,
        }
    }


# ─── PDF Export Endpoint ──────────────────────────────────────────────────────

@app.post("/api/export-pdf", response_model=PDFExportResponse)
async def export_design_pdf(request: PDFExportRequest, raw_request: Request):
    """Generate a comprehensive PDF for a saved design."""
    try:
        saved_design = get_design_by_id(request.design_id)
        if not saved_design:
            raise HTTPException(
                status_code=404,
                detail=f"Design with ID '{request.design_id}' not found"
            )

        pdf_base64, filename = generate_design_pdf(saved_design)

        return PDFExportResponse(
            success=True,
            pdf_base64=pdf_base64,
            message="PDF generated successfully",
            design_name=saved_design.get('name', 'Untitled'),
            filename=filename
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("PDF export failed")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


if RATE_LIMIT_AVAILABLE and limiter is not None:
    export_design_pdf = limiter.limit("20/minute")(export_design_pdf)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
