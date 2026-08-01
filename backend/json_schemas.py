"""Raw JSON Schema dicts passed to OpenRouter's response_format for
structured output. Separate from the Pydantic models in schemas.py because
this is what we send to the model, while schemas.py validates what comes
back — keeping the two distinct makes it obvious which one to edit when
the API contract changes vs. when the model's expected output changes.
"""

from typing import Any, Dict

DESIGN_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "type": {"type": "string", "enum": ["Ring", "Earrings", "Necklace", "Bracelet", "Brooch"]},
        "metal": {"type": "string", "enum": ["18K Yellow Gold", "18K White Gold", "18K Rose Gold", "Platinum", "14K Yellow Gold", "Sterling Silver"]},
        "stone": {"type": "string", "enum": ["Diamond", "Emerald", "Sapphire", "Ruby", "Garnet", "Moissanite", "Aquamarine", "Opal", "Amethyst", "Pearl", "Morganite"]},
        "shape": {"type": "string", "enum": ["Round", "Oval", "Emerald-Cut", "Pear", "Cushion", "Princess", "Marquise"]},
        "setting": {"type": "string", "enum": ["Prong", "Bezel", "Halo", "Pavé", "Channel", "Tension", "Cathedral"]},
        "occasion": {"type": "string", "enum": ["Engagement", "Wedding", "Anniversary", "Birthday", "Graduation", "Self-Gift"]},
        "stoneSize": {"type": "string"},
        "bandWidth": {"type": "string"},
        "details": {"type": "string"},
        "notes": {"type": "string"},
        "metalCost": {"type": "integer"},
        "stoneCost": {"type": "integer"},
        "laborCost": {"type": "integer"},
        "castingComplexity": {"type": "integer"},
        "settingComplexity": {"type": "integer"},
        "polishingComplexity": {"type": "integer"},
        "multiView": {
            "type": "object",
            "properties": {
                "front": {"type": "string"},
                "side": {"type": "string"},
                "perspective": {"type": "string"},
            },
            "required": ["front", "side", "perspective"],
        },
    },
    "required": [
        "name", "type", "metal", "stone", "shape", "setting", "occasion",
        "stoneSize", "bandWidth", "details", "notes",
        "metalCost", "stoneCost", "laborCost",
        "castingComplexity", "settingComplexity", "polishingComplexity", "multiView"
    ],
}

ADVISOR_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "gemstone": {"type": "string"},
                    "suitability": {"type": "string"},
                    "explanation": {"type": "string"},
                    "approxCost": {"type": "integer"},
                },
                "required": ["gemstone", "suitability", "explanation", "approxCost"],
            },
        },
        "suggestedMetal": {"type": "string"},
        "designIdea": {"type": "string"},
        "pricingStrategy": {"type": "string"},
    },
    "required": ["recommendations", "suggestedMetal", "designIdea", "pricingStrategy"],
}

TRENDS_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "trendingStyles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "style": {"type": "string"},
                    "growth": {"type": "string"},
                    "popularity": {"type": "integer"},
                    "season": {"type": "string"},
                },
                "required": ["style", "growth", "popularity", "season"],
            },
        },
        "seasonalGemstones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "season": {"type": "string"},
                    "stone": {"type": "string"},
                    "reason": {"type": "string"},
                    "hotFactor": {"type": "integer"},
                },
                "required": ["season", "stone", "reason", "hotFactor"],
            },
        },
        "styleComparisons": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "optionA": {"type": "string"},
                    "optionB": {"type": "string"},
                    "weightA": {"type": "integer"},
                    "weightB": {"type": "integer"},
                },
                "required": ["dimension", "optionA", "optionB", "weightA", "weightB"],
            },
        },
    },
    "required": ["trendingStyles", "seasonalGemstones", "styleComparisons"],
}
