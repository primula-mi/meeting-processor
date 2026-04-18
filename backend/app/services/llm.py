import json
import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_client(provider: str) -> OpenAI:
    if provider == "ollama":
        return OpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
        )
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _get_default_model(provider: str) -> str:
    if provider == "ollama":
        return settings.OLLAMA_DEFAULT_MODEL
    return settings.OPENAI_MODEL


def process_transcript(
    transcript: str,
    system_prompt: str,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    """Send transcript to LLM and return structured JSON result."""
    provider = provider or settings.LLM_PROVIDER
    model = model or _get_default_model(provider)
    client = _get_client(provider)

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
        "temperature": 0.3,
    }

    if provider == "openai":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = (response.choices[0].message.content or "").strip()

    result = _parse_json_response(content)
    result.setdefault("summary", "")
    result.setdefault("tasks", [])
    result.setdefault("decisions", [])

    return result


def _parse_json_response(content: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences and extra text."""
    if not content:
        return {}

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` fences
    import re
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { ... last }
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(content[start:end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse JSON from LLM response: %s", content[:200])
    return {"summary": content}


def list_ollama_models() -> list[dict]:
    """Fetch available models from Ollama."""
    import httpx

    try:
        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("models", [])
    except httpx.ConnectError:
        logger.warning("Ollama is not reachable at %s", settings.OLLAMA_BASE_URL)
    return []
