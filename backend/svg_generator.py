"""POST /api/generate-svg
Generates a bespoke jewellery SVG illustration for a given design and view
using OpenRouter FREE models only — no paid API required.

Free model chain (tried in order, first success wins):
  1. meta-llama/llama-4-maverick:free
  2. google/gemma-3-27b-it:free
  3. mistralai/mistral-7b-instruct:free

Returns: { "svg": "<svg ...>...</svg>", "model_used": "..." }
"""

import json
import re
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .config import OPENROUTER_API_URL, get_app_url, get_openrouter_key

router = APIRouter()

# ── Free-only model chain ─────────────────────────────────────────────────────
FREE_MODEL_CHAIN = [
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-12b-it:free",
    "mistralai/devstral-small:free",
    "openrouter/auto",               # catch-all: OpenRouter picks best available free model
]

# ── Color palettes (kept backend-side so frontend sends none) ─────────────────
METAL_PALETTE = {
    "platinum":        {"stroke": "#C8D8D0", "fill": "#1C2E28", "highlight": "#E2EDE8", "shadow": "#0A1410"},
    "white gold":      {"stroke": "#B8CEC8", "fill": "#182420", "highlight": "#D4E4DE", "shadow": "#080E0C"},
    "yellow gold":     {"stroke": "#DFBE8B", "fill": "#2A1E08", "highlight": "#F5D8A0", "shadow": "#120C02"},
    "14k yellow":      {"stroke": "#C8A870", "fill": "#221808", "highlight": "#E0C080", "shadow": "#0E0A02"},
    "rose gold":       {"stroke": "#C4847A", "fill": "#2A1010", "highlight": "#DFA090", "shadow": "#120404"},
    "sterling silver": {"stroke": "#A8C0B8", "fill": "#141E1A", "highlight": "#C8DCD4", "shadow": "#060E0A"},
}

GEM_PALETTE = {
    "diamond":    {"primary": "#E8F4F8", "facet": "#B0D8E8", "glow": "#FFFFFF",  "deep": "#4A7890"},
    "moissanite": {"primary": "#E0ECFA", "facet": "#90C0E0", "glow": "#F8FCFF",  "deep": "#3A6888"},
    "emerald":    {"primary": "#10B981", "facet": "#059669", "glow": "#6EE7B7",  "deep": "#064E3B"},
    "ruby":       {"primary": "#EF4444", "facet": "#B91C1C", "glow": "#FCA5A5",  "deep": "#450A0A"},
    "sapphire":   {"primary": "#3B82F6", "facet": "#1D4ED8", "glow": "#93C5FD",  "deep": "#172554"},
    "garnet":     {"primary": "#DC2626", "facet": "#991B1B", "glow": "#FCA5A5",  "deep": "#450A0A"},
    "aquamarine": {"primary": "#22D3EE", "facet": "#0891B2", "glow": "#A5F3FC",  "deep": "#083344"},
    "opal":       {"primary": "#C084FC", "facet": "#9333EA", "glow": "#F5D0FE",  "deep": "#3B0764"},
    "amethyst":   {"primary": "#8B5CF6", "facet": "#6D28D9", "glow": "#DDD6FE",  "deep": "#2E1065"},
    "pearl":      {"primary": "#FEF3C7", "facet": "#D97706", "glow": "#FFFBEB",  "deep": "#451A03"},
    "morganite":  {"primary": "#FB923C", "facet": "#EA580C", "glow": "#FFEDD5",  "deep": "#431407"},
}


def _get_palette(mapping: dict, key: str, default_key: str) -> dict:
    key_lower = key.lower()
    for k, v in mapping.items():
        if k in key_lower:
            return v
    return mapping[default_key]


# ── Request / Response schemas ─────────────────────────────────────────────────
class SVGRequest(BaseModel):
    design_id: str
    design_name: str
    prompt: str          # original user prompt
    notes: str           # AI design narrative
    view: str            # "perspective" | "front" | "side"
    view_description: str
    jewelry_type: str
    metal: str
    stone: str
    stone_shape: str
    stone_size: str
    setting: str
    details: str         # spec.details from AI


class SVGResponse(BaseModel):
    svg: str
    model_used: str


# ── Prompt builder ─────────────────────────────────────────────────────────────
def _build_prompt(req: SVGRequest) -> str:
    metal = _get_palette(METAL_PALETTE, req.metal, "yellow gold")
    gem   = _get_palette(GEM_PALETTE,   req.stone, "diamond")

    view_label = {
        "perspective": "artistic 3/4 angle",
        "front":       "front face / head-on",
        "side":        "side profile",
    }.get(req.view, "artistic 3/4 angle")

    return f"""You are an expert SVG illustrator specialising in fine jewellery technical drawings with a blueprint aesthetic.

Generate ONE complete self-contained SVG that illustrates this specific piece from the {view_label} view.

=== DESIGN BRIEF (READ CAREFULLY) ===
Name: {req.design_name}
Original customer prompt: "{req.prompt}"
Design narrative: {req.notes}
View description: {req.view_description}
Type: {req.jewelry_type}
Metal: {req.metal}
Gemstone: {req.stone} ({req.stone_shape} cut, {req.stone_size})
Setting: {req.setting}
Design details: {req.details}

=== COLOUR TOKENS (use EXACTLY these hex values, no others) ===
Metal stroke: {metal['stroke']}
Metal body fill: {metal['fill']}
Metal highlight: {metal['highlight']}
Metal shadow: {metal['shadow']}
Gem primary: {gem['primary']}
Gem facet: {gem['facet']}
Gem glow: {gem['glow']}
Gem deep: {gem['deep']}
Background: #050C08
Blueprint grid lines: #0D2018
Dimension annotation: #10B981

=== STRICT RULES ===
1. MOTIF FIRST: Draw the SPECIFIC subject from the prompt. "phoenix brooch" → phoenix bird with spread wings and feathers. "floral ring" → petals and stems. "dragon pendant" → dragon form. "art deco" → geometric fans and chevrons. NEVER draw a generic starburst, star, or placeholder shape.
2. viewBox must be exactly: 0 0 200 200
3. Output ONLY raw SVG. Start with <svg and end with </svg>. Zero prose, zero markdown, zero code fences.
4. Include a <defs> section with: (a) a radialGradient id="gemGlow" for the stone, (b) a linearGradient id="metalSheen" for metal surfaces.
5. Draw a subtle blueprint grid background: thin lines every 25px in #0D2018 at opacity 0.4.
6. Add ONE dimension annotation in #10B981 — a dashed line with two tick marks and a small label showing a key measurement (e.g. "18mm span").
7. The gemstone must show internal facet lines using the gem facet colour.
8. Add a soft drop-shadow or glow effect on the main subject using a feGaussianBlur filter.
9. Minimum 12 distinct SVG elements — this is a premium technical illustration, not a sketch.
10. The piece must be centred in the 200×200 canvas with adequate padding (min 15px from edges).

Draw the jewellery now:"""


# ── Core generation function ───────────────────────────────────────────────────
def _call_free_model(prompt: str, timeout: int = 90) -> tuple[str, str]:
    """Try each free model in order. Returns (raw_text, model_slug)."""
    api_key = get_openrouter_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  get_app_url(),
        "X-Title":       "Velaris Jewelry Design Engine",
    }

    last_error: str = "No models tried"

    for model_slug in FREE_MODEL_CHAIN:
        payload = {
            "model":    model_slug,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens":  3500,
        }
        try:
            resp = requests.post(
                OPENROUTER_API_URL, headers=headers, json=payload, timeout=timeout
            )
            if resp.status_code != 200:
                last_error = f"{model_slug} → HTTP {resp.status_code}: {resp.text[:200]}"
                continue

            body    = resp.json()
            content = body["choices"][0]["message"]["content"]
            if content and "<svg" in content:
                return content, model_slug

            last_error = f"{model_slug} → response contained no SVG"

        except (requests.RequestException, KeyError, IndexError) as exc:
            last_error = f"{model_slug} → {exc}"
            continue

    raise HTTPException(
        status_code=502,
        detail=f"All free models failed. Last error: {last_error}",
    )


def _extract_svg(raw: str) -> Optional[str]:
    """Pull the first complete <svg…</svg> block out of arbitrary text."""
    start = raw.find("<svg")
    end   = raw.rfind("</svg>")
    if start == -1 or end == -1:
        return None
    svg = raw[start : end + 6]
    # Basic sanity: must have closing tag and at least one path/rect/circle/polygon
    if not re.search(r"<(path|rect|circle|ellipse|polygon|polyline|line|g)\b", svg):
        return None
    return svg


# ── FastAPI route ──────────────────────────────────────────────────────────────
@router.post("/api/generate-svg", response_model=SVGResponse)
def generate_svg_endpoint(req: SVGRequest) -> SVGResponse:
    prompt = _build_prompt(req)
    raw, model_used = _call_free_model(prompt)
    svg = _extract_svg(raw)

    if not svg:
        raise HTTPException(
            status_code=502,
            detail=f"Model ({model_used}) responded but returned no valid SVG content.",
        )

    return SVGResponse(svg=svg, model_used=model_used)
