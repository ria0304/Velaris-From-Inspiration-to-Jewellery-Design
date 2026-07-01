"""POST /api/generate-svg
Generates a bespoke jewellery SVG illustration for a given design and view
using OpenRouter FREE models only — no paid API required.

Free model chain (tried in order, first success wins):
  1. google/gemini-2.0-flash-exp
  2. google/gemma-2-2b-it:free
  3. microsoft/phi-2:free
  4. qwen/qwen3-coder:free
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

# Free-only model chain - using reliable, working models
FREE_MODEL_CHAIN = [
    "google/gemini-2.0-flash-exp",
    "google/gemma-2-2b-it:free",
    "microsoft/phi-2:free",
    "qwen/qwen3-coder:free",
    "openrouter/auto",
]

# Color palettes
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
    
    # Animal motifs
    if motif_type == 'animal':
        instructions.append("""
=== ANIMAL MOTIF: DRAW THE SPECIFIC ANIMAL/CREATURE ===
DO NOT draw a generic star, starburst, or abstract shape.
Draw the ACTUAL animal or creature described.""")

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

        elif 'butterfly' in description.lower() or any('butterfly' in kw.lower() for kw in visual_keywords):
            instructions.append("""
BUTTERFLY DRAWING INSTRUCTIONS:
- Draw a symmetrical butterfly with 4 wings (2 upper, 2 lower)
- Upper wings: larger, rounded triangular shapes
- Lower wings: smaller, teardrop shapes
- Body: thin elongated oval with antennae
- Wing patterns: circular or teardrop decorative elements on wings
- Use the gem colour for wing accents""")

        elif 'eagle' in description.lower() or 'hawk' in description.lower():
            instructions.append("""
EAGLE/HAWK DRAWING INSTRUCTIONS:
- Draw a powerful bird in flight or perched
- Strong curved beak
- Sharp, angular wings with distinct feather tips
- Tail feathers in a fan shape
- Keen eye (use gem colour)
- Muscular, commanding posture""")

        elif 'serpent' in description.lower() or 'snake' in description.lower():
            instructions.append("""
SERPENT/SNAKE DRAWING INSTRUCTIONS:
- Draw an elegant coiled snake
- Curved, flowing body with defined segments
- Distinct head with eyes (use gem colour)
- Tongue: forked, extending outward
- Scales: overlapping pattern along the body""")

        else:
            instructions.append("""
GENERIC ANIMAL DRAWING INSTRUCTIONS:
- Draw a stylized animal silhouette
- Make it clearly recognizable as the animal mentioned
- Include key features: head, body, limbs
- Use flowing, organic curves
- Add decorative elements that match the jewelry style""")

    # Floral motifs
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

    # Geometric motifs
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

    # Celestial motifs
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

    # Abstract / other
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


class SVGRequest(BaseModel):
    design_id: str
    design_name: str
    prompt: str
    notes: str
    view: str
    view_description: str
    jewelry_type: str
    metal: str
    stone: str
    stone_shape: str
    stone_size: str
    setting: str
    details: str
    motif: Optional[Dict[str, Any]] = None


class SVGResponse(BaseModel):
    svg: str
    model_used: str


def _build_prompt(req: SVGRequest) -> str:
    metal = _get_palette(METAL_PALETTE, req.metal, "yellow gold")
    gem   = _get_palette(GEM_PALETTE,   req.stone, "diamond")

    view_label = {
        "perspective": "artistic 3/4 angle",
        "front":       "front face / head-on",
        "side":        "side profile",
    }.get(req.view, "artistic 3/4 angle")

    motif_instructions = _get_motif_instructions(req.motif)
    motif_annotation = _get_motif_annotation(req.motif)

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
    else:
        return base + " Show the piece at a 3/4 angle. Give it depth and dimension. Show both front and side elements."


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
                last_error = f"{model_slug} -> HTTP {resp.status_code}: {resp.text[:200]}"
                continue

            body    = resp.json()
            content = body["choices"][0]["message"]["content"]
            if content and "<svg" in content:
                return content, model_slug

            last_error = f"{model_slug} -> response contained no SVG"

        except (requests.RequestException, KeyError, IndexError) as exc:
            last_error = f"{model_slug} -> {exc}"
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


def _generate_fallback_svg(jewelry_type: str, metal: str = "yellow gold") -> str:
    """Generate a simple but beautiful fallback SVG when AI fails."""
    
    metal_palette = {
        "yellow gold": {"stroke": "#DFBE8B", "fill": "#2A1E08"},
        "white gold": {"stroke": "#B8CEC8", "fill": "#182420"},
        "rose gold": {"stroke": "#C4847A", "fill": "#2A1010"},
        "platinum": {"stroke": "#C8D8D0", "fill": "#1C2E28"},
    }
    
    # Find the closest metal match
    metal_key = "yellow gold"
    for key in metal_palette.keys():
        if key in metal.lower():
            metal_key = key
            break
    
    colors = metal_palette.get(metal_key, metal_palette["yellow gold"])
    
    templates = {
        "ring": f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="gemGlow">
                    <stop offset="0%" stop-color="#E8F4F8" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#4A7890" stop-opacity="0.2"/>
                </radialGradient>
                <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{colors['stroke']}" stop-opacity="0.3"/>
                    <stop offset="50%" stop-color="{colors['stroke']}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{colors['fill']}" stop-opacity="0.3"/>
                </linearGradient>
            </defs>
            <rect width="200" height="200" fill="#050C08"/>
            <g stroke="{colors['stroke']}" fill="none" stroke-width="2">
                <ellipse cx="100" cy="100" rx="55" ry="45" stroke="url(#metalSheen)"/>
                <ellipse cx="100" cy="100" rx="35" ry="28" stroke="#0D2018" stroke-width="1"/>
                <circle cx="100" cy="80" r="18" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="100" cy="80" r="12" fill="none" stroke="{colors['stroke']}" stroke-width="1.5"/>
                <line x1="90" y1="80" x2="110" y2="80" stroke="{colors['stroke']}" opacity="0.5"/>
                <line x1="100" y1="70" x2="100" y2="90" stroke="{colors['stroke']}" opacity="0.5"/>
                <circle cx="100" cy="100" r="45" stroke="#0D2018" stroke-width="1" stroke-dasharray="4,4"/>
                <text x="100" y="180" text-anchor="middle" fill="#10B981" font-size="10" font-family="monospace">18mm diameter</text>
                <line x1="45" y1="178" x2="155" y2="178" stroke="#10B981" stroke-width="0.5" stroke-dasharray="2,2"/>
            </g>
        </svg>''',
        
        "necklace": f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="gemGlow">
                    <stop offset="0%" stop-color="#E8F4F8" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#4A7890" stop-opacity="0.2"/>
                </radialGradient>
                <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{colors['stroke']}" stop-opacity="0.3"/>
                    <stop offset="50%" stop-color="{colors['stroke']}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{colors['fill']}" stop-opacity="0.3"/>
                </linearGradient>
            </defs>
            <rect width="200" height="200" fill="#050C08"/>
            <g stroke="{colors['stroke']}" fill="none">
                <path d="M 40 60 Q 100 30 160 60" stroke-width="2" stroke="url(#metalSheen)"/>
                <path d="M 40 60 Q 100 30 160 60" stroke-width="1" stroke="#0D2018" stroke-dasharray="3,3"/>
                <circle cx="100" cy="130" r="16" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="100" cy="130" r="12" stroke-width="1.5"/>
                <line x1="90" y1="130" x2="110" y2="130" stroke="{colors['stroke']}" opacity="0.5"/>
                <line x1="100" y1="120" x2="100" y2="140" stroke="{colors['stroke']}" opacity="0.5"/>
                <text x="100" y="185" text-anchor="middle" fill="#10B981" font-size="10" font-family="monospace">pendant 14mm</text>
                <line x1="45" y1="183" x2="155" y2="183" stroke="#10B981" stroke-width="0.5" stroke-dasharray="2,2"/>
            </g>
        </svg>''',
        
        "earrings": f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="gemGlow">
                    <stop offset="0%" stop-color="#E8F4F8" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#4A7890" stop-opacity="0.2"/>
                </radialGradient>
                <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{colors['stroke']}" stop-opacity="0.3"/>
                    <stop offset="50%" stop-color="{colors['stroke']}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{colors['fill']}" stop-opacity="0.3"/>
                </linearGradient>
            </defs>
            <rect width="200" height="200" fill="#050C08"/>
            <g stroke="{colors['stroke']}" fill="none">
                <line x1="60" y1="40" x2="60" y2="70" stroke-width="2" stroke="url(#metalSheen)"/>
                <circle cx="60" cy="85" r="12" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="60" cy="85" r="8" stroke-width="1.5"/>
                <line x1="140" y1="40" x2="140" y2="70" stroke-width="2" stroke="url(#metalSheen)"/>
                <circle cx="140" cy="85" r="12" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="140" cy="85" r="8" stroke-width="1.5"/>
                <text x="100" y="185" text-anchor="middle" fill="#10B981" font-size="10" font-family="monospace">pair 12mm each</text>
                <line x1="45" y1="183" x2="155" y2="183" stroke="#10B981" stroke-width="0.5" stroke-dasharray="2,2"/>
            </g>
        </svg>''',
        
        "bracelet": f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="gemGlow">
                    <stop offset="0%" stop-color="#E8F4F8" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#4A7890" stop-opacity="0.2"/>
                </radialGradient>
                <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{colors['stroke']}" stop-opacity="0.3"/>
                    <stop offset="50%" stop-color="{colors['stroke']}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{colors['fill']}" stop-opacity="0.3"/>
                </linearGradient>
            </defs>
            <rect width="200" height="200" fill="#050C08"/>
            <g stroke="{colors['stroke']}" fill="none">
                <ellipse cx="100" cy="100" rx="60" ry="40" stroke-width="2" stroke="url(#metalSheen)"/>
                <ellipse cx="100" cy="100" rx="60" ry="40" stroke-width="1" stroke="#0D2018" stroke-dasharray="3,3"/>
                <circle cx="100" cy="70" r="10" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="100" cy="70" r="7" stroke-width="1.5"/>
                <text x="100" y="185" text-anchor="middle" fill="#10B981" font-size="10" font-family="monospace">60mm circumference</text>
                <line x1="45" y1="183" x2="155" y2="183" stroke="#10B981" stroke-width="0.5" stroke-dasharray="2,2"/>
            </g>
        </svg>''',
        
        "brooch": f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="gemGlow">
                    <stop offset="0%" stop-color="#E8F4F8" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#4A7890" stop-opacity="0.2"/>
                </radialGradient>
                <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{colors['stroke']}" stop-opacity="0.3"/>
                    <stop offset="50%" stop-color="{colors['stroke']}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{colors['fill']}" stop-opacity="0.3"/>
                </linearGradient>
            </defs>
            <rect width="200" height="200" fill="#050C08"/>
            <g stroke="{colors['stroke']}" fill="none">
                <polygon points="100,40 130,80 180,90 140,120 150,170 100,145 50,170 60,120 20,90 70,80" stroke-width="2" stroke="url(#metalSheen)"/>
                <polygon points="100,40 130,80 180,90 140,120 150,170 100,145 50,170 60,120 20,90 70,80" stroke-width="1" stroke="#0D2018" stroke-dasharray="3,3"/>
                <circle cx="100" cy="95" r="14" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="100" cy="95" r="10" stroke-width="1.5"/>
                <text x="100" y="185" text-anchor="middle" fill="#10B981" font-size="10" font-family="monospace">starburst 40mm</text>
                <line x1="45" y1="183" x2="155" y2="183" stroke="#10B981" stroke-width="0.5" stroke-dasharray="2,2"/>
            </g>
        </svg>''',
        
        "tiara": f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <radialGradient id="gemGlow">
                    <stop offset="0%" stop-color="#E8F4F8" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#4A7890" stop-opacity="0.2"/>
                </radialGradient>
                <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{colors['stroke']}" stop-opacity="0.3"/>
                    <stop offset="50%" stop-color="{colors['stroke']}" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="{colors['fill']}" stop-opacity="0.3"/>
                </linearGradient>
            </defs>
            <rect width="200" height="200" fill="#050C08"/>
            <g stroke="{colors['stroke']}" fill="none">
                <path d="M 40 160 L 40 100 L 60 50 L 100 30 L 140 50 L 160 100 L 160 160 Z" stroke-width="2" stroke="url(#metalSheen)"/>
                <path d="M 40 160 L 40 100 L 60 50 L 100 30 L 140 50 L 160 100 L 160 160 Z" stroke-width="1" stroke="#0D2018" stroke-dasharray="3,3"/>
                <circle cx="100" cy="60" r="12" fill="url(#gemGlow)" stroke="none"/>
                <circle cx="100" cy="60" r="8" stroke-width="1.5"/>
                <text x="100" y="185" text-anchor="middle" fill="#10B981" font-size="10" font-family="monospace">crown 14mm</text>
                <line x1="45" y1="183" x2="155" y2="183" stroke="#10B981" stroke-width="0.5" stroke-dasharray="2,2"/>
            </g>
        </svg>'''
    }
    
    return templates.get(jewelry_type, templates["ring"])


@router.post("/api/generate-svg", response_model=SVGResponse)
def generate_svg_endpoint(req: SVGRequest) -> SVGResponse:
    try:
        prompt = _build_prompt(req)
        raw, model_used = _call_free_model(prompt)
        svg = _extract_svg(raw)

        if not svg:
            print(f"Model {model_used} returned invalid SVG, using fallback")
            svg = _generate_fallback_svg(req.jewelry_type, req.metal)
            model_used = "fallback"
            
        return SVGResponse(svg=svg, model_used=model_used)
        
    except Exception as e:
        print(f"SVG generation error: {e}")
        svg = _generate_fallback_svg(req.jewelry_type, req.metal)
        return SVGResponse(svg=svg, model_used="fallback")
