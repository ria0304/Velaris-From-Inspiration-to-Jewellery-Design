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


def _casting_note(metal: str, jewelry_type: str) -> str:
    """Dynamic casting note based on metal choice and jewelry type."""
    m = metal.lower()
    t = jewelry_type.lower()

    if "platinum" in m:
        base = (
            "Platinum is one of the densest, most demanding metals to cast — "
            "it requires a high-temperature torch and specialist equipment to reach its 1,768 °C melting point. "
            "The result is an exceptionally weighty, hypoallergenic piece that will never tarnish or fade."
        )
    elif "rose gold" in m:
        base = (
            "18K Rose Gold is alloyed with copper to achieve its warm blush tone, "
            "which also makes it slightly harder and more scratch-resistant than yellow gold. "
            "The casting is straightforward for an experienced goldsmith, and the copper content "
            "gives the metal a beautiful, rosy character that deepens attractively with wear."
        )
    elif "white gold" in m:
        base = (
            "18K White Gold is alloyed with palladium or nickel and finished with a rhodium plating "
            "that gives it a crisp, mirror-bright surface. Casting is standard, but the piece will "
            "benefit from rhodium re-plating every few years to maintain its brilliant white lustre."
        )
    elif "yellow gold" in m and "14k" in m:
        base = (
            "14K Yellow Gold offers an ideal balance of durability and affordability. "
            "Its lower gold content (58.3%) makes it harder and more resistant to everyday knocks "
            "than 18K, and it casts cleanly with minimal porosity — ideal for fine detail work."
        )
    elif "yellow gold" in m:
        base = (
            "18K Yellow Gold is the classic choice of master jewellers worldwide. "
            "At 75% pure gold it casts with exceptional fluidity, capturing fine surface detail beautifully. "
            "It is softer than 14K, so prongs and settings should be checked annually."
        )
    elif "sterling silver" in m:
        base = (
            "Sterling Silver (92.5% pure silver) is one of the easiest metals to cast and work — "
            "it has a low melting point, flows beautifully into moulds, and takes a mirror polish effortlessly. "
            "It is an ideal choice for intricate sculptural work, though it will develop a natural patina over time."
        )
    else:
        base = (
            "This metal casts cleanly and holds its form well through the lost-wax casting process. "
            "A skilled goldsmith will finish the raw casting by filing, grinding, and refining the surface "
            "before any stone setting begins."
        )

    # Add type-specific note
    if t in ("brooch", "pendant"):
        base += (
            f" For a {jewelry_type.lower()}, the casting also includes a structural pin or bail — "
            "these load-bearing elements are cast as part of the main body and reinforced before finishing."
        )
    elif t == "earrings":
        base += (
            " Earrings are cast as a matched pair from the same pour to guarantee colour and weight consistency between the two pieces."
        )
    elif t == "bracelet":
        base += (
            " Bracelet links or panels are cast individually and assembled post-casting, "
            "with each join soldered and inspected before the piece moves to setting."
        )
    elif t == "tiara":
        base += (
            " A tiara framework requires multiple cast sections joined with high-temperature solder — "
            "the structural integrity of every join is critical before any stone setting begins."
        )
    return base


def _setting_note(setting: str, stone: str, avg_complexity: int) -> str:
    """Dynamic setting note based on setting type, stone, and complexity."""
    s = setting.lower()
    st = stone.lower()

    if "pavé" in s or "pave" in s:
        note = (
            "Pavé setting is one of the most labour-intensive techniques in fine jewellery. "
            "Each tiny accent stone is hand-placed into a drilled seat, then a master setter "
            "raises tiny metal beads (or 'pavé dots') around each stone using a fine graver. "
            "This process is repeated stone by stone across the entire surface — "
            "expect 4–8 hours of setting time from a skilled artisan."
        )
    elif "channel" in s:
        note = (
            "Channel setting holds stones in a continuous groove cut into the metal shank. "
            "All stones must be precisely matched in diameter before they are slid into the channel "
            "and the metal walls are pressed inward to secure them. "
            "It produces a clean, flush look with excellent stone protection."
        )
    elif "bezel" in s:
        note = (
            "Bezel setting wraps a thin collar of metal fully around the girdle of the stone, "
            "securing it without any exposed prongs. It is the most protective setting style — "
            "ideal for softer stones or active wearers — and gives the design a sleek, modern silhouette."
        )
    elif "tension" in s:
        note = (
            "Tension setting suspends the stone between two opposing metal walls using the "
            "spring-force of the shank itself — there are no prongs or bezels. "
            "This requires precision machining to within ±0.01 mm: too loose and the stone falls, "
            "too tight and the stone cracks. Only experienced setters should attempt this technique."
        )
    elif "halo" in s:
        note = (
            "The halo ring of accent stones surrounds the centre gem and is set before the main stone is placed. "
            "Each halo stone is individually prong- or micro-pavé-set, then the centre seat is verified for "
            "level alignment before the primary stone is secured. The finished halo dramatically amplifies "
            f"the apparent size of the {stone}."
        )
    elif "cathedral" in s:
        note = (
            "Cathedral setting arches the metal shank upward on both sides of the centre stone, "
            "elevating it dramatically above the finger. The arched rails are shaped and refined by hand "
            "before the stone seat is drilled and the prongs bent into position."
        )
    else:
        # Prong (default)
        note = (
            f"Prong setting is the most classic and versatile mounting for a {stone}. "
            "Four to six fine metal claws are cast as part of the head, then hand-bent over the "
            "stone's girdle by the setter — allowing maximum light to reach the gem from every angle "
            "and producing the brilliant sparkle this stone is known for."
        )

    # Complexity rider
    if avg_complexity > 75:
        note += (
            " Given the high complexity score for this design, additional quality-control checkpoints "
            "are recommended between casting, setting, and polishing to ensure no stones shift during finishing."
        )
    return note


def _polishing_note(metal: str, avg_complexity: int, total_cost: int) -> str:
    """Dynamic polishing note based on metal and design tier."""
    m = metal.lower()

    if "platinum" in m:
        finish = (
            "Platinum takes a deeper, more lustrous polish than gold — its natural white colour "
            "requires no plating, so the mirror finish goes all the way through the metal. "
            "A rotary polishing wheel with platinum-grade compound is used first, "
            "followed by hand-burnishing of every prong tip and recessed surface."
        )
    elif "rose gold" in m:
        finish = (
            "Rose Gold polishes to a warm, satin-meets-mirror finish that flatters its blush tone beautifully. "
            "The copper alloy can develop micro-scratches more readily than platinum, "
            "so a final hand-buff with a chamois cloth brings out the richest surface lustre."
        )
    elif "sterling silver" in m:
        finish = (
            "Sterling Silver achieves a bright mirror polish quickly but benefits from an anti-tarnish "
            "dip after final buffing to slow oxidation. "
            "A light rhodium flash coat is optional but recommended for long-term brightness."
        )
    else:
        finish = (
            "Gold is polished in two stages: a machine buff removes casting texture and any tool marks, "
            "then a hand-polishing stage with a soft mop and jeweller's rouge brings every surface "
            "to a flawless mirror shine before the stones are set."
        )

    if total_cost > 4000 or avg_complexity > 65:
        finish += (
            " Given the intricacy of this design, each recessed detail, filigree element, "
            "and prong shoulder is finished individually with a flex-shaft tool "
            "to ensure no surface is left matte or dull."
        )
    return finish


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
            castingNotes=_casting_note(raw_data.metal, raw_data.type),
            settingNotes=_setting_note(raw_data.setting, raw_data.stone, avg_complexity),
            polishingNotes=_polishing_note(raw_data.metal, avg_complexity, total_cost),
        ),
        multiView=raw_data.multiView,
        notes=raw_data.notes,
        modelUsed=model_used,
    )
