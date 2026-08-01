"""Thin OpenRouter client with a multi-model fallback chain.

One API key gives access to many providers (Claude, GPT-4o, Gemini, etc.)
through a single OpenAI-compatible endpoint. We try each model in
config.get_model_chain() in order; on any failure (network error, non-2xx
response, or a body we can't parse as JSON) we move to the next model.
The caller never has to know which model actually produced the result.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from .config import OPENROUTER_API_URL, get_app_url, get_model_chain, get_openrouter_key

from fastapi import HTTPException


def build_design_messages(
    system_instruction: str,
    prompt_str: str,
    image_b64: Optional[str],
) -> List[Dict[str, Any]]:
    """Builds an OpenAI-style chat message list. OpenRouter normalizes this
    format across providers, including vision-capable ones, so the same
    payload shape works whether the active model is Claude, GPT-4o, or
    Gemini under the hood."""
    user_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt_str}]

    if image_b64:
        clean_b64 = image_b64.split(",")[1] if "," in image_b64 else image_b64
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{clean_b64}"}
        })

    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_content},
    ]


def clean_json_content(content: str) -> str:
    """Clean JSON content from markdown, extra text, and whitespace."""
    if not content:
        return "{}"
    
    # Remove markdown code blocks
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```\s*', '', content)
    
    # Try to find JSON object in the text
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return content.strip()


def call_openrouter_with_fallback(
    messages: List[Dict[str, Any]],
    schema_name: str,
    json_schema: Dict[str, Any],
    timeout: int = 60,
    max_tokens: int = 2000,
) -> Tuple[Dict[str, Any], str]:
    """Tries each model in the fallback chain in order. Returns the parsed
    JSON body plus the model slug that succeeded. Raises HTTPException only
    if every model in the chain fails."""
    api_key = get_openrouter_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": get_app_url(),
        "X-Title": "Velaris Jewelry Design Engine",
    }

    last_error: Optional[str] = None

    for model_slug in get_model_chain():
        payload = {
            "model": model_slug,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            },
            "max_tokens": max_tokens,
            "temperature": 0.8,
        }

        try:
            print(f"🔄 Trying OpenRouter model: {model_slug}")
            resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=timeout)
            
            if resp.status_code != 200:
                last_error = f"{model_slug} returned HTTP {resp.status_code}: {resp.text[:300]}"
                print(f"⚠️ {last_error}")
                continue

            body = resp.json()
            
            # Check if choices exist
            if "choices" not in body or len(body["choices"]) == 0:
                last_error = f"{model_slug} returned no choices: {body}"
                print(f"⚠️ {last_error}")
                continue
            
            # Check if message exists
            message = body["choices"][0].get("message")
            if not message:
                last_error = f"{model_slug} returned no message: {body}"
                print(f"⚠️ {last_error}")
                continue
            
            # Check if content exists and is not None
            content = message.get("content")
            if not content:
                last_error = f"{model_slug} returned empty content: {body}"
                print(f"⚠️ {last_error}")
                continue
            
            # Try to parse JSON, with cleaning if needed
            try:
                parsed = json.loads(content)
                print(f"✅ {model_slug} succeeded!")
                return parsed, model_slug
            except json.JSONDecodeError:
                # Try cleaning the content
                cleaned_content = clean_json_content(content)
                try:
                    parsed = json.loads(cleaned_content)
                    print(f"✅ {model_slug} succeeded (with cleaning)!")
                    return parsed, model_slug
                except json.JSONDecodeError as json_err:
                    last_error = f"{model_slug} invalid JSON: {json_err}. Content: {content[:200]}"
                    print(f"⚠️ {last_error}")
                    continue

        except requests.RequestException as exc:
            last_error = f"{model_slug} request failed: {exc}"
            print(f"⚠️ {last_error}")
            continue
        except Exception as exc:
            last_error = f"{model_slug} unexpected error: {exc}"
            print(f"⚠️ {last_error}")
            continue

    # If we've exhausted all models, raise an exception
    raise HTTPException(
        status_code=502,
        detail=f"All models in the fallback chain failed. Last error: {last_error}"
    )
