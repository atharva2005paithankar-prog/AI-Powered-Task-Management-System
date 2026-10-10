"""Turns the raw text from the AI into a Python dict.

Models sometimes wrap JSON in ```json fences or add a sentence before it,
so we clean that up before parsing. No third-party imports on purpose.
"""
import json


def extract_json(raw_text: str) -> dict:
    """Return the JSON object found in raw_text, or raise ValueError."""
    text = (raw_text or "").strip()

    # Remove markdown code fences such as ```json ... ```
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: take everything from the first "{" to the last "}".
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("No JSON object found in the AI response")
        data = json.loads(text[start : end + 1])  # raises ValueError if still invalid

    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object from the AI")
    return data
