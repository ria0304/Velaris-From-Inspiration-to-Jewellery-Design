"""Hugging Face Inference API client - Free tier fallback for OpenRouter."""

import json
import httpx
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from .config import get_huggingface_key

# Hugging Face free inference API endpoint
HF_API_URL = "https://api-inference.huggingface.co/models/"

# Free models that work well for text generation
FREE_MODELS = [
    "google/gemma-2-2b-it",           # Small, fast, free
    "microsoft/phi-2",                # Great for instructions
    "meta-llama/Llama-3.2-1B",        # Tiny Llama, very fast
    "mistralai/Mistral-7B-Instruct-v0.3",  # Larger, good quality
]

async def call_huggingface(
    prompt: str,
    system_instruction: str = "You are a jewellery design assistant.",
    model: str = "google/gemma-2-2b-it",
    max_tokens: int = 1500,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Call Hugging Face Inference API with a free model."""
    
    api_key = get_huggingface_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Hugging Face API key not configured")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Build the prompt (Hugging Face models don't use the same chat format)
    full_prompt = f"{system_instruction}\n\nUser request: {prompt}\n\nGenerate a jewellery design specification in JSON format."
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.7,
            "return_full_text": False,
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{HF_API_URL}{model}",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 503:
                # Model is loading, retry with a delay or try different model
                raise Exception("Model is warming up. Try again or use a different model.")
            
            if response.status_code != 200:
                raise Exception(f"Hugging Face API error: {response.status_code} - {response.text[:200]}")
            
            result = response.json()
            
            # Different models return different formats
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                generated_text = result.get("generated_text", "")
            else:
                generated_text = str(result)
            
            # Try to parse JSON from the response
            return parse_json_from_response(generated_text, model)
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Hugging Face API timeout")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Hugging Face error: {str(e)}")


async def call_huggingface_with_fallback(
    prompt: str,
    system_instruction: str = "You are a jewellery design assistant.",
    max_tokens: int = 1500,
) -> Dict[str, Any]:
    """Try multiple Hugging Face models in order."""
    
    last_error = None
    
    for model in FREE_MODELS:
        try:
            return await call_huggingface(
                prompt=prompt,
                system_instruction=system_instruction,
                model=model,
                max_tokens=max_tokens
            )
        except Exception as e:
            last_error = str(e)
            continue
    
    raise HTTPException(
        status_code=502,
        detail=f"All Hugging Face models failed. Last error: {last_error}"
    )


def parse_json_from_response(text: str, model: str) -> Dict[str, Any]:
    """Extract JSON from Hugging Face model responses (they're often messy)."""
    
    # Try to find JSON in the response
    import re
    
    # Look for JSON-like content between ```json and ``` or just plain JSON
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, text, re.DOTALL)
    
    if match:
        json_str = match.group(1)
    else:
        # Try to find any JSON object
        json_pattern = r'(\{.*\})'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # If no JSON found, create a basic response
            return {
                "description": text.strip(),
                "type": "ring",  # fallback
                "metal": "18K Yellow Gold",
                "stone_type": "Diamond",
                "setting": "Prong",
            }
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, return a structured fallback
        return {
            "description": text.strip()[:500],
            "type": "ring",
            "metal": "18K Yellow Gold", 
            "stone_type": "Diamond",
            "setting": "Prong",
        }
