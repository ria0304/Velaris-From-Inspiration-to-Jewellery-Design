# Velaris — From Inspiration to Jewelry Design
# Python backend entrypoint. Run with: python main.py
# or: uvicorn main:app --reload --port 3000

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import advisor, design, storage, trends
from backend.svg_generator import router as svg_router
from backend.pdf_generator import generate_design_pdf
from backend.schemas import PDFExportRequest, PDFExportResponse
from backend.storage import get_design_by_id

app = FastAPI(
    title="Velaris Jewelry Design Engine",
    description="FastAPI backend powered by an OpenRouter multi-model fallback chain",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(design.router)
app.include_router(advisor.router)
app.include_router(trends.router)
app.include_router(storage.router)
app.include_router(svg_router)


# ---------------------------------------------------------------------------
# PDF Export Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/export-pdf", response_model=PDFExportResponse)
async def export_design_pdf(request: PDFExportRequest):
    """
    Generate a comprehensive PDF for a saved design including:
    - Front View
    - Artistic/Perspective View
    - Profile/Side View
    - Full specifications
    - Cost breakdown
    - Manufacturing details
    - Design narrative

    The PDF will be named after the design (e.g., "Aurum_Bloom.pdf")
    """
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
