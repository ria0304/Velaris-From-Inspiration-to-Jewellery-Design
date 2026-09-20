from fastapi import APIRouter
from pydantic import BaseModel
from . import render_cad_svg, to_dxf_entities, CadParams

router = APIRouter()


class CadRequest(BaseModel):
    jewelry_type: str = "Ring"
    metal: str = "18K Yellow Gold"
    stone: str = "Diamond"
    stone_shape: str = "Round"
    stone_size: str = "1.0 carat"
    setting: str = "Prong"
    band_width: str | None = None
    view: str = "perspective"
    design_id: str = "cad"


@router.post("/api/cad-svg")
def cad_svg(req: CadRequest):
    svg, p = render_cad_svg(req.jewelry_type, req.metal, req.stone,
                            req.stone_shape, req.stone_size, req.setting,
                            req.band_width, req.view, req.design_id)
    return {"svg": svg, "params": {"carat": p.carat, "stone_r_mm": round(p.stone_r, 3),
                                   "band_w_mm": p.band_w, "band_r_mm": p.band_r}}


@router.post("/api/cad-dxf")
def cad_dxf(req: CadRequest):
    _, p = render_cad_svg(req.jewelry_type, req.metal, req.stone,
                          req.stone_shape, req.stone_size, req.setting,
                          req.band_width, "front", req.design_id)
    import base64
    dxf = to_dxf_entities(p)
    return {"dxf_base64": base64.b64encode(dxf.encode()).decode(),
            "filename": f"{req.design_id}.dxf"}
