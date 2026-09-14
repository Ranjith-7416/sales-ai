import json
from typing import Any


def parse_json_response(response: str) -> Any:
    """Parse JSON returned with optional Markdown fences or surrounding text."""
    content = response.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]).strip()

    object_start = content.find("{")
    if object_start > 0:
        content = content[object_start:]

    return json.JSONDecoder().raw_decode(content)[0]