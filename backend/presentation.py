"""POST /api/presentation-board — pilot composer for the editorial board.

Frontend-only (no PDF). Composes existing engines:
- realistic PNGs (presentation) via backend.render
- CAD SVG vectors (technical) via backend.cad
- specs/dims via CadParams.dims()
Returns everything the PresentationBoard needs in one call.
"""
from __future__ import annotations
import base64
import io
import re

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class BoardRequest(BaseModel):
    design_id: str = "pilot"
    design_name: str = "Phoenix Brooch"
    tagline: str = "A single piece. Endless beauty."
    jewelry_type: str = "Brooch"
    metal: str = "18K Yellow Gold"
    stone: str = "Ruby"
    stone_shape: str = "Oval"
    stone_size: str = "1.5 carat"
    setting: str = "Prong"
    band_width: Optional[str] = None
    motif: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    view_notes: Optional[Dict[str, str]] = None


def _png_b64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _default_features(jewelry_type: str, stone: str, shape: str,
                      carat: float, setting: str, motif: Dict[str, Any] | None) -> List[str]:
    """Per-type feature bullets — phoenix copy only for phoenix brooches."""
    desc = ((motif or {}).get("description") or "").lower()
    if (motif or {}).get("type") == "animal" and "phoenix" in desc:
        return [
            "Spread wings with layered flight feathers",
            "Hand-set ruby eyes",
            "Rampant hind-leg stance with talons",
            f"{shape} {stone} breast stone ({carat} ct)",
        ]
    base = f"{shape} {stone} ({carat} ct), {setting} setting"
    per_type = {
        "ring": ["Comfort-fit band with pavé shoulders", "Raised head for maximum light",
                 f"Centre stone: {base}"],
        "necklace": ["Hand-linked chain with polished bail", f"Pendant drop: {base}"],
        "pendant": ["Hand-linked chain with polished bail", f"Pendant drop: {base}"],
        "earrings": ["Matched pair, colour-weighed from one pour", f"Drop stones: {base} each"],
        "bracelet": ["Articulated links, individually soldered", f"Hero stone: {base}"],
        "brooch": ["Sculptural frame with pin stem + safety catch", f"Centre stone: {base}"],
        "tiara": ["Multi-section soldered framework", f"Graduated stones, hero: {base}"],
    }
    return per_type.get((jewelry_type or "").lower(), [base])


@router.post("/api/presentation-board")
def presentation_board(req: BoardRequest):
    from .beauty import beauty_png
    from .cad import parse_carat, render_cad_svg

    design_id = re.sub(r"[^a-zA-Z0-9]", "", req.design_id)[:12] or "pilot"
    carat = parse_carat(req.stone_size)
    views: Dict[str, Any] = {}
    for view in ("front", "perspective", "side", "back"):
        svg, params = render_cad_svg(
            req.jewelry_type, req.metal, req.stone, req.stone_shape,
            req.stone_size, req.setting, req.band_width, view,
            design_id, req.motif)
        png_raw, source = beauty_png(
            req.jewelry_type, req.metal, req.stone, req.stone_shape,
            carat, req.setting, view, req.motif)
        views[view] = {"svg": svg,
                       "png_b64": base64.b64encode(png_raw).decode(),
                       "source": source,
                       "note": (req.view_notes or {}).get(view, "")}
    dims = params.dims()
    gems = [{"name": req.stone, "shape": req.stone_shape, "weight": f"{carat} ct",
             "dims": f"{dims['stone_w_mm']} × {dims['stone_h_mm']} mm"}]
    features = req.features or _default_features(
        req.jewelry_type, req.stone, req.stone_shape, carat, req.setting, req.motif)
    return {
        "design_id": req.design_id, "design_name": req.design_name,
        "tagline": req.tagline, "hero": views["front"],
        "front": views["front"], "back": views["back"],
        "strip": [views["front"], views["perspective"], views["side"], views["back"]],
        "features": features, "gems": gems,
        "specs": {"type": req.jewelry_type, "metal": req.metal, **dims},
    }
