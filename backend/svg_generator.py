"""POST /api/generate-svg
Generates a bespoke jewellery SVG illustration for a given design and view
using OpenRouter FREE models only — no paid API required.

Free model chain (tried in order, first success wins):
  1. qwen/qwen3-coder:free
  2. meta-llama/llama-3.3-70b-instruct:free
  3. google/gemma-3-12b-it:free
  4. mistralai/devstral-small:free
  5. openrouter/auto

Returns: { "svg": "<svg>...</svg>", "model_used": "..." }
"""

import json
import re
from typing import Optional, Dict, Any, List

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

# ── Color palettes ─────────────────────────────────────────────────────────────
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


# ─── NEW: Motif to SVG instructions ────────────────────────────────────────────
def _get_motif_instructions(motif: Optional[Dict[str, Any]]) -> str:
    """Generate specific SVG drawing instructions based on motif type."""
    
    if not motif:
        return """
CRITICAL: No specific motif was provided. Draw a generic but elegant representation of the jewelry type.
"""
    
    motif_type = motif.get('type', 'abstract')
    description = motif.get('description', '')
    elements = motif.get('elements', [])
    visual_keywords = motif.get('visualKeywords', [])
    
    instructions = []
    
    # ─── ANIMAL MOTIFS ──────────────────────────────────────────────────────────
    if motif_type == 'animal':
        instructions.append("""
=== ANIMAL MOTIF: DRAW THE SPECIFIC ANIMAL/CREATURE ===
DO NOT draw a generic star, starburst, or abstract shape.
Draw the ACTUAL animal or creature described.""")

        # Phoenix specific
        if 'phoenix' in description.lower() or any('phoenix' in kw.lower() for kw in visual_keywords):
            instructions.append("""
PHOENIX DRAWING INSTRUCTIONS:
- Draw a majestic phoenix bird at the center
- Spread wings: large sweeping curves rising upward and outward
- Tail feathers: flowing downward with multiple plumes
- Distinct head with a beak and crest
- Ruby eye: use the gem colour for a prominent eye
- Feather details: overlapping curved lines on wings and body
- Body should be graceful with a curved neck""")

        # Butterfly specific
        elif 'butterfly' in description.lower() or any('butterfly' in kw.lower() for kw in visual_keywords):
            instructions.append("""
BUTTERFLY DRAWING INSTRUCTIONS:
- Draw a symmetrical butterfly with 4 wings (2 upper, 2 lower)
- Upper wings: larger, rounded triangular shapes
- Lower wings: smaller, teardrop shapes
- Body: thin elongated oval with antennae
- Wing patterns: circular or teardrop decorative elements on wings
- Use the gem colour for wing accents""")

        # Eagle/Hawk specific
        elif 'eagle' in description.lower() or 'hawk' in description.lower():
            instructions.append("""
EAGLE/HAWK DRAWING INSTRUCTIONS:
- Draw a powerful bird in flight or perched
- Strong curved beak
- Sharp, angular wings with distinct feather tips
- Tail feathers in a fan shape
- Keen eye (use gem colour)
- Muscular, commanding posture""")

        # Serpent/Snake specific
        elif 'serpent' in description.lower() or 'snake' in description.lower():
            instructions.append("""
SERPENT/SNAKE DRAWING INSTRUCTIONS:
- Draw an elegant coiled snake
- Curved, flowing body with defined segments
- Distinct head with eyes (use gem colour)
- Tongue: forked, extending outward
- Scales: overlapping pattern along the body""")

        # Generic animal
        else:
            instructions.append("""
GENERIC ANIMAL DRAWING INSTRUCTIONS:
- Draw a stylized animal silhouette
- Make it clearly recognizable as the animal mentioned
- Include key features: head, body, limbs
- Use flowing, organic curves
- Add decorative elements that match the jewelry style""")

    # ─── FLORAL MOTIFS ──────────────────────────────────────────────────────────
    elif motif_type == 'floral':
        instructions.append("""
=== FLORAL MOTIF: DRAW FLOWERS AND PLANT ELEMENTS ===
DO NOT draw a generic star or abstract shape.
Draw ACTUAL flowers, petals, leaves, and stems.""")

        if 'rose' in description.lower() or any('rose' in kw.lower() for kw in visual_keywords):
            instructions.append("""
ROSE DRAWING INSTRUCTIONS:
- Draw a layered rose flower at the center
- Outer petals: large, overlapping curved shapes
- Inner petals: smaller, tightly packed, spiraling inward
- Leaves: pointed, serrated edges on stems
- Use flowing, organic curves for petals
- The gem can be the center of the rose or an accent""")

        elif 'lotus' in description.lower() or any('lotus' in kw.lower() for kw in visual_keywords):
            instructions.append("""
LOTUS DRAWING INSTRUCTIONS:
- Draw a blooming lotus flower
- Petals: pointed, arranged in layers (bottom petals wider, top petals pointed)
- Center: visible seed pod or gem
- Leaves: large, circular with cleft
- Use symmetrical, elegant curves""")

        else:
            instructions.append("""
GENERIC FLORAL DRAWING INSTRUCTIONS:
- Draw multiple layers of petals
- Center: use the gem as the flower center
- Add leaves branching outward
- Use organic, flowing curves
- Make it lush and decorative""")

    # ─── GEOMETRIC MOTIFS ──────────────────────────────────────────────────────
    elif motif_type == 'geometric':
        instructions.append("""
=== GEOMETRIC MOTIF: DRAW PRECISE GEOMETRIC PATTERNS ===
Draw clean, precise geometric shapes and patterns.""")

        if 'art deco' in description.lower() or any('deco' in kw.lower() for kw in visual_keywords):
            instructions.append("""
ART DECO DRAWING INSTRUCTIONS:
- Use angular, symmetrical geometric patterns
- Include: chevrons, zigzags, stepped shapes, fans
- Clean lines with sharp corners
- Symmetrical composition
- Use repeating geometric elements""")

        else:
            instructions.append("""
GENERIC GEOMETRIC DRAWING INSTRUCTIONS:
- Use concentric shapes (circles, diamonds, polygons)
- Include repeating patterns
- Symmetrical composition
- Clean, precise lines
- Layer different geometric shapes""")

    # ─── CELESTIAL MOTIFS ──────────────────────────────────────────────────────
    elif motif_type == 'celestial':
        instructions.append("""
=== CELESTIAL MOTIF: DRAW STARS, MOON, AND COSMIC ELEMENTS ===
Draw celestial bodies and cosmic patterns.""")

        instructions.append("""
CELESTIAL DRAWING INSTRUCTIONS:
- Draw a prominent star or moon as the focal point
- Add smaller stars radiating outward
- Use curved, flowing cosmic lines
- Gem can be the center of a star or moon
- Add sparkling effects with small diamonds""")

    # ─── ABSTRACT / OTHER ──────────────────────────────────────────────────────
    else:
        instructions.append("""
=== ABSTRACT MOTIF: DRAW ARTISTIC, FLOWING SHAPES ===
Draw organic, flowing abstract shapes.""")

        instructions.append("""
ABSTRACT DRAWING INSTRUCTIONS:
- Use flowing, organic curves
- Layer multiple abstract shapes
- Create a sense of movement
- Use the gem as a focal point
- Add decorative swirls and spirals""")

    # ─── COMMON INSTRUCTIONS FOR ALL MOTIFS ──────────────────────────────────
    instructions.append(f"""
MOTIF SUMMARY:
- Type: {motif_type}
- Description: {description}
- Elements: {', '.join(elements) if elements else 'none specified'}
- Visual Keywords: {', '.join(visual_keywords) if visual_keywords else 'none'}

CRITICAL REMINDER:
- DRAW THE SPECIFIC {motif_type.upper()} MOTIF
- DO NOT draw a generic star, starburst, or placeholder shape
- The motif should be the MAIN FOCAL POINT of the illustration
- Make it clearly recognizable as {description}
""")

    return '\n'.join(instructions)


# ─── NEW: Motif-specific dimension annotation ──────────────────────────────────
def _get_motif_annotation(motif: Optional[Dict[str, Any]]) -> str:
    """Generate motif-appropriate measurement annotation."""
    
    if not motif:
        return '"18mm span"'
    
    motif_type = motif.get('type', '')
    
    if motif_type == 'animal':
        return '"12mm wingspan"'
    elif motif_type == 'floral':
        return '"14mm bloom"'
    elif motif_type == 'geometric':
        return '"12mm pattern"'
    elif motif_type == 'celestial':
        return '"10mm star"'
    else:
        return '"14mm motif"'


# ─── UPDATED: Request schema with motif ────────────────────────────────────────
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
    motif: Optional[Dict[str, Any]] = None  # NEW: Motif data


class SVGResponse(BaseModel):
    svg: str
    model_used: str


# ─── UPDATED: Prompt builder with motif awareness ─────────────────────────────
def _build_prompt(req: SVGRequest) -> str:
    metal = _get_palette(METAL_PALETTE, req.metal, "yellow gold")
    gem   = _get_palette(GEM_PALETTE,   req.stone, "diamond")

    view_label = {
        "perspective": "artistic 3/4 angle",
        "front":       "front face / head-on",
        "side":        "side profile",
    }.get(req.view, "artistic 3/4 angle")

    # ─── Build motif instructions ──────────────────────────────────────────────
    motif_instructions = _get_motif_instructions(req.motif)
    motif_annotation = _get_motif_annotation(req.motif)

    # ─── Check if motif exists ──────────────────────────────────────────────────
    has_motif = req.motif is not None and req.motif.get('type') != 'abstract'
    motif_type = req.motif.get('type', '') if req.motif else ''

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

=== MOTIF INFORMATION ===
{has_motif}
Motif Type: {motif_type}
Motif Instructions:
{motif_instructions}

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
1. MOTIF FIRST: Draw the SPECIFIC subject from the prompt. {"Draw the " + req.motif.get('description', 'motif') if has_motif else "Draw a generic but elegant representation of the jewelry type."}
   - {"MOTIF TYPE: " + motif_type.upper() if has_motif else ""}
   - {"DESCRIPTION: " + req.motif.get('description', '') if has_motif else ""}
   - NEVER draw a generic starburst, star, or placeholder shape. The motif MUST be recognizable.
2. viewBox must be exactly: 0 0 200 200
3. Output ONLY raw SVG. Start with <svg and end with </svg>. Zero prose, zero markdown, zero code fences.
4. Include a <defs> section with: (a) a radialGradient id="gemGlow" for the stone, (b) a linearGradient id="metalSheen" for metal surfaces.
5. Draw a subtle blueprint grid background: thin lines every 25px in #0D2018 at opacity 0.4.
6. Add ONE dimension annotation in #10B981 — a dashed line with two tick marks and a small label showing a key measurement (e.g. {motif_annotation}).
7. The gemstone must show internal facet lines using the gem facet colour.
8. Add a soft drop-shadow or glow effect on the main subject using a feGaussianBlur filter.
9. Minimum 12 distinct SVG elements — this is a premium technical illustration, not a sketch.
10. The piece must be centred in the 200×200 canvas with adequate padding (min 15px from edges).

=== VIEW-SPECIFIC ADJUSTMENTS ===
{_get_view_adjustments(req.view, req.jewelry_type)}

Draw the jewellery now:"""


def _get_view_adjustments(view: str, jewelry_type: str) -> str:
    """Provide view-specific guidance."""
    
    base = f"Draw from the {view} perspective."
    
    if view == 'front':
        return base + " Show the piece head-on. Symmetry is important. Display all major design elements clearly."
    elif view == 'side':
        return base + " Show the side/profile. Focus on the silhouette and depth. Show the band/profile thickness."
    else:  # perspective
        return base + " Show the piece at a 3/4 angle. Give it depth and dimension. Show both front and side elements."


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
