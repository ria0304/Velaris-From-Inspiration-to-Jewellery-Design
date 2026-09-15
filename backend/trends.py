"""GET /api/trends — jewellery trend intelligence, with a static fallback
if every model in the chain fails."""

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from .json_schemas import TRENDS_JSON_SCHEMA
from .openrouter_client import call_openrouter_with_fallback
from .schemas import GrowthStyle, SeasonalGem, StyleComparison, TrendsResponse

router = APIRouter()

SYSTEM_INSTRUCTION = (
    "You are the chief Haute Joaillerie trend analyst at Velaris.\n"
    "Formulate a highly reliable, up-to-the-minute trend intel summary report, identifying trending styles, seasonal gemstone focus, and custom style matrices. Provide insightful descriptions.\n"
    "Respond ONLY with JSON matching the provided schema."
)

_STATIC_FALLBACK = TrendsResponse(
    trendingStyles=[
        GrowthStyle(style="Toi et Moi Duet Rings", growth="+68% Quarter-over-Quarter", popularity=89, season="Summer Weddings"),
        GrowthStyle(style="Bespoke Scalloped Halos", growth="+45% YoY", popularity=78, season="Spring Engagement"),
        GrowthStyle(style="Whisper Band Micro-settings", growth="+34% YoY", popularity=82, season="Year Round"),
        GrowthStyle(style="Brushed Celestial Signets", growth="+51% YoY", popularity=70, season="Autumn Releases"),
    ],
    seasonalGemstones=[
        SeasonalGem(season="Summer / Autumn Transition", stone="Peachy-Pink Morganite", reason="Warm pastel shades are replacing typical pure diamonds as couples seek tender, organic tones.", hotFactor=9),
        SeasonalGem(season="Winter Holiday Season", stone="Deep Teal Montana Sapphires", reason="Colder months see a massive spike in green-blue sapphires matching well on platinum frames.", hotFactor=8),
        SeasonalGem(season="Spring Renewal", stone="Chatham Lab Emeralds", reason="Verdant hues are widely favored for anniversaries, conveying fidelity and regrowth.", hotFactor=7),
    ],
    styleComparisons=[
        StyleComparison(dimension="Design Approach", optionA="Luxury Maximalism", optionB="Modern Minimalism", weightA=55, weightB=45),
        StyleComparison(dimension="Aesthetic Era", optionA="Art Deco Vintage", optionB="Ultra Sleek Contemporary", weightA=62, weightB=38),
        StyleComparison(dimension="Band Profiles", optionA="Organic Sculpted", optionB="Perfect Symmetric Edge", weightA=40, weightB=60),
    ],
)


@router.get("/api/trends", response_model=TrendsResponse)
def client_trends() -> TrendsResponse:
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": "Compile a live jewelry trend report with trending styles, seasonal preferences, and contrasting design dimensions."},
    ]

    try:
        raw_json, _ = call_openrouter_with_fallback(
            messages, schema_name="jewelry_trends", json_schema=TRENDS_JSON_SCHEMA
        )
        return TrendsResponse.model_validate(raw_json)
    except (HTTPException, ValidationError):
        return _STATIC_FALLBACK
