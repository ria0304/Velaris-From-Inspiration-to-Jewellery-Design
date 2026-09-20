from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
import io
from . import render_realistic

router = APIRouter()


class RealRequest(BaseModel):
    jewelry_type: str = "Ring"
    metal: str = "18K Yellow Gold"
    stone: str = "Diamond"
    stone_shape: str = "Round"
    carat: float = 1.0
    view: str = "front"
    motif: dict | None = None


@router.post("/api/render-realistic")
def render_png(req: RealRequest):
    img = render_realistic(req.jewelry_type, req.metal, req.stone,
                           req.stone_shape, req.carat, req.view, req.motif)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
