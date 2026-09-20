"""Velaris beauty layer — diffusion presentation renders with graceful fallback.

Chain: HuggingFace text-to-image (FLUX/SDXL, free tier) -> PIL offline render.
Disk cache keyed by spec-hash so beauty images are never paid for twice.
Without an HF key, everything falls back to the PIL renderer transparently.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path

import requests

CACHE_DIR = Path(os.getenv("BEAUTY_CACHE_DIR", "/tmp/velaris_beauty"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HF_T2I_MODEL = os.getenv("BEAUTY_HF_MODEL", "black-forest-labs/FLUX.1-schnell")
HF_API = f"https://api-inference.huggingface.co/models/{HF_T2I_MODEL}"

VIEW_STYLE = {
    "front": "straight-on front view, symmetric, centered",
    "perspective": "three-quarter artistic angle, depth and dimension",
    "side": "side profile view, silhouette and depth",
    "back": "back view showing clasp and findings",
}


def build_prompt(jewelry_type: str, metal: str, stone: str, shape: str,
                 carat: float, setting: str, view: str,
                 motif: dict | None = None) -> str:
    motif_txt = ""
    if motif and motif.get("description"):
        motif_txt = f", motif: {motif['description']}"
    return (
        f"Luxury jewellery product photography: a {carat} carat {shape}-cut {stone} "
        f"{jewelry_type.lower()} in {metal} with {setting} setting{motif_txt}, "
        f"{VIEW_STYLE.get(view, VIEW_STYLE['front'])}. Macro studio shot on dark silk, "
        f"soft spotlight, brilliant gemstone fire, polished metal reflections, "
        f"ultra-detailed pavé work, shallow depth of field, high-end catalog style."
    )


def spec_hash(*parts) -> str:
    h = hashlib.sha256("|".join(str(p) for p in parts).encode())
    return h.hexdigest()[:16]


def _hf_generate(prompt: str, timeout: int = 90) -> bytes | None:
    key = os.getenv("HUGGINGFACE_API_KEY", "")
    if not key:
        return None
    try:
        r = requests.post(
            HF_API, headers={"Authorization": f"Bearer {key}"},
            json={"inputs": prompt}, timeout=timeout)
        if r.status_code != 200:
            return None
        ctype = r.headers.get("content-type", "")
        if "image" not in ctype:
            return None
        return r.content
    except Exception:
        return None


def beauty_png(jewelry_type: str, metal: str, stone: str, shape: str,
               carat: float, setting: str, view: str,
               motif: dict | None = None) -> tuple[bytes, str]:
    """Returns (png_bytes, source) where source is 'diffusion' or 'procedural'."""
    key = spec_hash(jewelry_type, metal, stone, shape, carat, setting, view,
                    json.dumps(motif or {}, sort_keys=True), HF_T2I_MODEL)
    cached = CACHE_DIR / f"{key}.png"
    if cached.exists():
        return cached.read_bytes(), "diffusion-cached"
    raw = _hf_generate(build_prompt(jewelry_type, metal, stone, shape,
                                    carat, setting, view, motif))
    if raw:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            img.save(cached, format="PNG")
            return cached.read_bytes(), "diffusion"
        except Exception:
            pass
    # fallback: procedural PIL renderer
    from backend.render import render_realistic
    img = render_realistic(jewelry_type, metal, stone, shape, carat, view, motif)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), "procedural"
