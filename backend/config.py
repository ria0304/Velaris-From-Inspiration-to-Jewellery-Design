"""Configuration: environment variables and the model fallback chain."""

import os
from typing import List

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

# Ordered fallback chain. First entry is tried first; on failure (network
# error, non-2xx response, or a body that fails schema validation) we move
# to the next model.
DEFAULT_MODEL_CHAIN = [
    "google/gemini-2.0-flash-lite",      # Free! 🆓
    "meta-llama/llama-3.2-3b-instruct",  # Free! 🆓
    "mistralai/mistral-7b-instruct",     # Free! 🆓
    "google/gemini-2.5-flash",           # Cheap fallback
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


def get_huggingface_key() -> str:
    """Get Hugging Face API key for free tier fallback."""
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        # Don't raise an exception here - Hugging Face is optional
        # Just return empty string and the client will handle it
        return ""
    return api_key


def get_app_url() -> str:
    return os.getenv("APP_URL", "http://localhost:3000")


def get_huggingface_models() -> List[str]:
    """Returns the Hugging Face free models to try in order."""
    override = os.getenv("HUGGINGFACE_MODELS")
    if override:
        return [m.strip() for m in override.split(",") if m.strip()]
    return [
        "google/gemma-2-2b-it",           # Small, fast, free
        "microsoft/phi-2",                # Great for instructions
        "meta-llama/Llama-3.2-1B",        # Tiny Llama
        "mistralai/Mistral-7B-Instruct-v0.3",  # Larger, good quality
    ]
