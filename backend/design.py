"""POST /api/generate-design — the core text/sketch/photo -> jewellery
design flow, now routed through the OpenRouter fallback chain instead of
a single hardcoded provider."""

import random
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from .json_schemas import DESIGN_JSON_SCHEMA
from .openrouter_client import build_design_messages, call_openrouter_with_fallback
from .schemas import (
    CostStructure,
    DesignRequest,
    DesignSpec,
    FinalDesignPackage,
    ManufacturingSpecs,
    RawDesignResponse,
)

router = APIRouter()

SYSTEM_INSTRUCTION = (
    "You are Velaris AI, a master bespoke jewelry designer, gemologist, and designer. "
    "Your task is to take customer inputs (ideas, sketch drawings, or photos of inspirational designs) and draft a masterfully designed, luxury piece of jewelry.\n\n"
    "In corporate branding, remember we are 'Velaris — From Inspiration to Jewelry Design'. Keep descriptions beautiful, warm, romantic, and extremely easy for ordinary clients to understand (no complex engineering terms, no confusing technical acronyms). Focus on the beauty, shimmer, shape, and sentiment.\n\n"
    "CRITICAL: Tailor pricing, materials, and stone size to the selected budget tier:\n"
    "- 'Value': Select lovely, friendly materials like Sterling Silver or 14K Gold, moderate gemstone (0.5-1.0 ct), secure settings (Prong, Bezel). Total price should be lower ($300 to $1,000).\n"
    "- 'Balanced': Select luxurious 18K Gold, sparkling diamonds, sapphire, or moissanite (1.0-2.0 ct), shimmering settings (Halo, Cathedral). Total price should be mid-range ($1,000 to $3,500).\n"
    "- 'Premium': Select Platinum or 18K Gold, spectacular gem sizes (2.0-4.0+ ct), intricate settings, elegant galleries. Total price should be upper range ($4,000 to $15,000+).\n\n"
    "Respond ONLY with JSON matching the provided schema. No prose, no markdown fences, no commentary outside the JSON object.\n\n"
    "Provide clear, friendly feedback for Casting, Setting, and Polishing, as well as distinct warm instructions for multi-perspective views (Front View, Side View, Perspective View)."
)


def _build_prompt(req: DesignRequest) -> str:
    if req.inputType == "text":
        return f"Design an exquisite custom piece of jewelry with style orientation '{req.style}' and budget tier '{req.budget}' based on the user's inspiration concepts: \"{req.prompt}\"."
    if req.inputType == "sketch":
        return (
            f"The user has supplied a hand-drawn rough sketch or draft doodle. Inspect the layout of this sketch carefully and refine it into an exquisite physical product.\n"
            f"Adhere strictly to style orientation '{req.style}' and budget tier '{req.budget}'.\n"
            f"Customer additional description thoughts: \"{req.prompt or 'Refine my sketch into an artistic piece'}\"."
        )
    if req.inputType == "photo":
        return (
            f"The user has uploaded an inspiration photo. Extract the core metals, gemstone cuts, and general shape of this photo.\n"
            f"Then, adapt and transform them into a bespoke inspired original. Make sure it is not a direct copy, but rather a sophisticated reimagining following style orientation '{req.style}' and budget tier '{req.budget}'.\n"
            f"Customer custom requests: \"{req.prompt or 'Reimagine this beautiful layout'}\"."
        )
    raise HTTPException(status_code=400, detail=f"Unsupported inputType: {req.inputType}")


def _manufacturing_level(avg_complexity: int) -> str:
    """Matches src/types.ts ManufacturingScore['level'] exactly."""
    if avg_complexity < 40:
        return "Easy to Manufacture"
    if avg_complexity > 75:
        return "Complex Design"
    return "Moderate Complexity"


@router.post("/api/generate-design", response_model=FinalDesignPackage)
def generate_design(req: DesignRequest) -> FinalDesignPackage:
    prompt_str = _build_prompt(req)

    messages = build_design_messages(
        SYSTEM_INSTRUCTION,
        prompt_str,
        req.image if req.inputType in ("sketch", "photo") else None,
    )

    raw_json, model_used = call_openrouter_with_fallback(
        messages, schema_name="jewelry_design", json_schema=DESIGN_JSON_SCHEMA
    )

    try:
        raw_data = RawDesignResponse.model_validate(raw_json)
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{model_used} returned a body that didn't match the expected schema: {exc}"
        )

    total_raw = raw_data.metalCost + raw_data.stoneCost + raw_data.laborCost
    markup_pct = 25
    total_cost = round(total_raw * (1 + markup_pct / 100))

    avg_complexity = round(
        (raw_data.castingComplexity + raw_data.settingComplexity + raw_data.polishingComplexity) / 3
    )

    return FinalDesignPackage(
        id=f"vel-{random.randint(100000, 999999)}",
        name=raw_data.name,
        timestamp=datetime.now().strftime("%B %d, %Y"),
        inputType=req.inputType,
        prompt=req.prompt or ("Custom Sketch Conversion" if req.inputType == "sketch" else "Custom Photo Reimagining"),
        inputImage=req.image,
        spec=DesignSpec(
            type=raw_data.type,
            metal=raw_data.metal,
            stone=raw_data.stone,
            shape=raw_data.shape,
            setting=raw_data.setting,
            occasion=raw_data.occasion,
            stoneSize=raw_data.stoneSize,
            bandWidth=raw_data.bandWidth or "1.8 mm",
            details=raw_data.details
        ),
        cost=CostStructure(
            metalCost=raw_data.metalCost,
            stoneCost=raw_data.stoneCost,
            laborCost=raw_data.laborCost,
            markupPercent=markup_pct,
            totalCost=total_cost
        ),
        manufacturing=ManufacturingSpecs(
            score=avg_complexity,
            level=_manufacturing_level(avg_complexity),
            castingNotes="This choice of metal is sturdy, easy to shape into standard curves, and holds a beautiful polish forever without tarnishing.",
            settingNotes="The delicate mount relies on standard prong alignments. The prongs are hand-bent over the gem sides to keep your stone absolutely safe.",
            polishingNotes="Expertly hand-polished to a high luster finish, making every facet shimmer beautifully in standard natural sunlight."
        ),
        multiView=raw_data.multiView,
        notes=raw_data.notes,
        modelUsed=model_used,
    )
