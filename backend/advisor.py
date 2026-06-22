"""POST /api/jewellery-advisor — gemstone recommendation and gifting advice."""

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from .json_schemas import ADVISOR_JSON_SCHEMA
from .openrouter_client import call_openrouter_with_fallback
from .schemas import AdvisorRequest, AdvisorResponse

router = APIRouter()

SYSTEM_INSTRUCTION = (
    "You are a high-end luxury Gifting and Gemstone Advisor for 'Velaris'.\n"
    "Your purpose is to review a budget limit, the occasion, style thoughts, and age of the recipient to recommend 3 exquisite gemstones that match beautifully.\n"
    "For each option, explain why it provides the ultimate sentimental value or fits the budget framework beautifully. Make sure to estimate approximate costs. Keep suggestions romantic, warm, and simple.\n"
    "Respond ONLY with JSON matching the provided schema."
)


@router.post("/api/jewellery-advisor", response_model=AdvisorResponse)
def jewelry_advisor(req: AdvisorRequest) -> AdvisorResponse:
    prompt_text = (
        f"Generate customized jewelry advisor recommendations:\n"
        f"Recipient age: {f'{req.age} years old' if req.age else 'N/A'}.\n"
        f"Occasion of gift: {req.occasion}.\n"
        f"User budget amount: {req.budget} {req.currency}.\n"
        f"Recipient's style taste: {req.stylePreferences}."
    )

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt_text},
    ]

    raw_json, _ = call_openrouter_with_fallback(
        messages, schema_name="jewelry_advisor", json_schema=ADVISOR_JSON_SCHEMA
    )

    try:
        return AdvisorResponse.model_validate(raw_json)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail=f"Advisor response failed validation: {exc}")
