from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from . import beauty_png, build_prompt

router = APIRouter()


class BeautyRequest(BaseModel):
    jewelry_type: str = "Brooch"
    metal: str = "18K Yellow Gold"
    stone: str = "Ruby"
    stone_shape: str = "Oval"
    carat: float = 1.5
    setting: str = "Prong"
    view: str = "front"
    motif: dict | None = None


@router.post("/api/render-beauty")
def render_beauty(req: BeautyRequest):
    png, source = beauty_png(req.jewelry_type, req.metal, req.stone,
                             req.stone_shape, req.carat, req.setting,
                             req.view, req.motif)
    return Response(content=png, media_type="image/png",
                    headers={"X-Render-Source": source})


@router.post("/api/beauty-prompt")
def beauty_prompt(req: BeautyRequest):
    return {"prompt": build_prompt(req.jewelry_type, req.metal, req.stone,
                                   req.stone_shape, req.carat, req.setting,
                                   req.view, req.motif)}
