"""POST /api/generate-design — the core text/sketch/photo -> jewellery
design flow, now routed through the OpenRouter fallback chain instead of
a single hardcoded provider."""

import random
import re
from datetime import datetime
from typing import Optional

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
    
    "🚨 CRITICAL RULE #1: EXACTLY MATCH THE USER'S REQUESTED JEWELRY TYPE 🚨\n"
    "  - If the user mentions 'brooch' → output a BROOCH\n"
    "  - If the user mentions 'ring' → output a RING\n"
    "  - If the user mentions 'necklace' → output a NECKLACE\n"
    "  - If the user mentions 'bracelet' → output a BRACELET\n"
    "  - If the user mentions 'earrings' → output EARRINGS\n"
    "  - If the user mentions 'pendant' → output a PENDANT\n"
    "  - If the user mentions 'tiara' or 'crown' → output a TIARA\n"
    "  - NEVER change the jewelry type. If the user wants a BROOCH, do NOT output a RING.\n"
    "  - The type field in your JSON MUST exactly match what the user requested.\n\n"
    
    "🚨 CRITICAL RULE #2: Match the budget tier 🚨\n"
    "  - 'Value': Sterling Silver or 14K Gold, moderate gemstone (0.5-1.0 ct), secure settings. ($300-$1,000)\n"
    "  - 'Balanced': 18K Gold, sparkling gemstones (1.0-2.0 ct), shimmering settings. ($1,000-$3,500)\n"
    "  - 'Premium': Platinum or 18K Gold, spectacular gem sizes (2.0-4.0+ ct), intricate settings. ($4,000-$15,000+)\n\n"
    
    "In corporate branding, remember we are 'Velaris — From Inspiration to Jewelry Design'. Keep descriptions beautiful, warm, romantic, and extremely easy for ordinary clients to understand (no complex engineering terms, no confusing technical acronyms). Focus on the beauty, shimmer, shape, and sentiment.\n\n"
    
    "Adhere strictly to standard enum options:\n"
    "  - Type: Ring, Earrings, Necklace, Bracelet, Brooch, Pendant, Tiara\n"
    "  - Metal: 18K Yellow Gold, 18K White Gold, 18K Rose Gold, Platinum, 14K Yellow Gold, Sterling Silver\n"
    "  - Gemstone: Diamond, Emerald, Sapphire, Ruby, Garnet, Moissanite, Aquamarine, Opal, Amethyst, Pearl, Morganite\n"
    "  - Gemstone Cut: Round, Oval, Emerald-Cut, Pear, Cushion, Princess, Marquise\n"
    "  - Setting Type: Prong, Bezel, Halo, Pavé, Channel, Tension, Cathedral\n"
    "  - Occasion: Engagement, Wedding, Anniversary, Birthday, Graduation, Self-Gift\n\n"
    
    "Provide clear, friendly feedback for Casting, Setting, and Polishing, as well as distinct warm instructions for multi-perspective views (Front View, Side View, Perspective View).\n\n"
    
    "Respond ONLY with JSON matching the provided schema. No prose, no markdown fences, no commentary outside the JSON object."
)


def extract_design_type(prompt: str) -> str:
    """
    Extract the design type from the user's prompt.
    Returns the type in proper case.
    """
    prompt_lower = prompt.lower()
    
    # Check for specific design types (ordered by specificity)
    if "brooch" in prompt_lower:
        return "Brooch"
    elif "necklace" in prompt_lower or "chain" in prompt_lower:
        return "Necklace"
    elif "bracelet" in prompt_lower or "bangle" in prompt_lower:
        return "Bracelet"
    elif "earring" in prompt_lower or "ear ring" in prompt_lower or "stud" in prompt_lower:
        return "Earrings"
    elif "pendant" in prompt_lower:
        return "Pendant"
    elif "tiara" in prompt_lower or "crown" in prompt_lower:
        return "Tiara"
    elif "ring" in prompt_lower:
        return "Ring"
    else:
        # Default to Ring if no type is specified
        return "Ring"


def _build_prompt(req: DesignRequest) -> str:
    """
    Build a prompt that strongly enforces the design type.
    """
    # Extract the design type from the user's prompt
    design_type = extract_design_type(req.prompt)
    
    # Build a type-specific emphasis
    type_emphasis = f"""
    🚨 IMPORTANT: The user requested a {design_type}. 
    Your response MUST have type = "{design_type}".
    Do NOT output any other type. 
    If the user said "{design_type}", you MUST output "{design_type}".
    """
    
    if req.inputType == "text":
        return f"""
        DESIGN REQUEST: Create a {design_type} based on this description.
        
        {type_emphasis}
        
        User description: "{req.prompt}"
        Style orientation: {req.style}
        Budget tier: {req.budget}
        
        Create a beautiful, detailed {design_type} that matches the user's description.
        Make sure the design is manufacturable and follows the budget constraints.
        """
    
    if req.inputType == "sketch":
        return f"""
        DESIGN REQUEST: Refine this sketch into a {design_type}.
        
        {type_emphasis}
        
        The user uploaded a sketch of a {design_type}.
        User additional description: "{req.prompt or f'Refine my {design_type.lower()} sketch into an artistic piece'}"
        Style orientation: {req.style}
        Budget tier: {req.budget}
        
        Refine the sketch into a polished, manufacturable {design_type}.
        """
    
    if req.inputType == "photo":
        return f"""
        DESIGN REQUEST: Reimagine this photo into a {design_type}.
        
        {type_emphasis}
        
        The user uploaded an inspiration photo for a {design_type}.
        User custom requests: "{req.prompt or f'Reimagine this beautiful {design_type.lower()} layout'}"
        Style orientation: {req.style}
        Budget tier: {req.budget}
        
        Create an original {design_type} inspired by the photo.
        Make sure it is not a direct copy, but a sophisticated reimagining.
        """
    
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

    # 🚨 VALIDATE: Check if the AI returned the correct design type
    expected_type = extract_design_type(req.prompt)
    actual_type = raw_data.type
    
    if expected_type != actual_type:
        # Log the mismatch
        print(f"⚠️ Design type mismatch: User requested '{expected_type}', AI returned '{actual_type}'")
        print(f"⚠️ Overriding with expected type: '{expected_type}'")
        
        # Override with the expected type
        # Create a new RawDesignResponse with the corrected type
        raw_data_dict = raw_json.copy()
        raw_data_dict['type'] = expected_type
        try:
            raw_data = RawDesignResponse.model_validate(raw_data_dict)
        except ValidationError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to override design type: {exc}"
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
