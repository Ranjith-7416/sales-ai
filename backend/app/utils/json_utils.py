import json
import re
from typing import Any


def parse_json_response(response: str) -> Any:
    """Parse JSON returned with optional Markdown fences, conversational preambles, or surrounding text."""
    content = response.strip()

    # Extract content inside markdown code fence if present
    fence_match = re.search(r"```(?:json)?\s*\n([\s\S]*?)\n\s*```", content)
    if fence_match:
        content = fence_match.group(1).strip()
    elif content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1]).strip()

    # Find first { or [
    obj_start = content.find("{")
    arr_start = content.find("[")

    if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
        # Object starts first - find last matching }
        obj_end = content.rfind("}")
        if obj_end != -1:
            candidate = content[obj_start:obj_end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                return json.JSONDecoder().raw_decode(candidate)[0]
    elif arr_start != -1:
        # Array starts first
        arr_end = content.rfind("]")
        if arr_end != -1:
            candidate = content[arr_start:arr_end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                return json.JSONDecoder().raw_decode(candidate)[0]

    # Fallback to direct raw_decode
    object_start = content.find("{")
    if object_start > 0:
        content = content[object_start:]

    return json.JSONDecoder().raw_decode(content)[0]