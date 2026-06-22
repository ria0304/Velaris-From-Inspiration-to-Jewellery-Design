"""Configuration: environment variables and the OpenRouter model fallback chain."""

import os
from typing import List

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Ordered fallback chain. First entry is tried first; on failure (network
# error, non-2xx response, or a body that fails schema validation) we move
# to the next model.
DEFAULT_MODEL_CHAIN = [
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-4o",
    "google/gemini-2.5-flash",
]


def get_model_chain() -> List[str]:
    """Returns the fallback chain, overridable via MODEL_FALLBACK_CHAIN
    (comma-separated OpenRouter model slugs) without a code change."""
    override = os.getenv("MODEL_FALLBACK_CHAIN")
    if override:
        return [m.strip() for m in override.split(",") if m.strip()]
    return DEFAULT_MODEL_CHAIN


def get_openrouter_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY environment variable is not configured. Please set your key."
        )
    return api_key


def get_app_url() -> str:
    return os.getenv("APP_URL", "http://localhost:3000")
