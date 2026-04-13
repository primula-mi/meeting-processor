import json
import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


def process_transcript(transcript: str, system_prompt: str) -> dict:
    """Send transcript to LLM and return structured JSON result."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    # Ensure required keys exist
    result.setdefault("summary", "")
    result.setdefault("tasks", [])
    result.setdefault("decisions", [])

    return result
