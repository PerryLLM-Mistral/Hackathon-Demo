from __future__ import annotations

import re
import json
import os
from typing import Dict, List, Optional, Type

from mistralai import Mistral
from pydantic import BaseModel, ValidationError

@staticmethod
def _extract_json(text: str) -> str:
    """
    Extracts a JSON object from model output.

    Supports:
    - Markdown fences: ```json ... ```
    - Plain JSON
    - Extra commentary around JSON (best effort)
    """
    s = text.strip()

    # Case 1: Markdown fenced block
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    # Case 2: Try to find the first JSON object in the text (best effort)
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start:end + 1].strip()

    return s

class MistralProvider:
    """
    Mistral chat wrapper.
    Reads MISTRAL_API_KEY from environment (load .env with python-dotenv for local runs).
    """

    def __init__(self, model: str = "mistral-small-latest", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY not found in environment")

    async def complete_json(self, messages: List[Dict[str, str]], schema: Type[BaseModel], temperature: float = 0.2, top_p: float = 0.9) -> BaseModel:
        """
        Ask model for strict JSON, then validate with Pydantic schema.
        """
        messages = messages + [{
            "role": "system",
            "content": "Return ONLY valid JSON. No markdown. No extra keys.",
        }]

        async with Mistral(api_key=self.api_key) as client:
            res = await client.chat.complete_async(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                )

        raw = res.choices[0].message.content.strip()
        json_str = _extract_json(raw)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Model did not return valid JSON.\nRaw:\n{raw}\n\nExtracted:\n{json_str}") from e

        try:
            return schema.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"JSON does not match schema.\nErrors:\n{e}\nRaw:\n{raw}") from e