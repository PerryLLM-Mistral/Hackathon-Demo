from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Type

from mistralai import Mistral
from pydantic import BaseModel, ValidationError

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

    async def complete_json(self, messages: List[Dict[str, str]], schema: Type[BaseModel], temperature: float = 0.2) -> BaseModel:
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
            )

        raw = res.choices[0].message.content.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Model did not return valid JSON.\nRaw:\n{raw}") from e

        try:
            return schema.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"JSON does not match schema.\nErrors:\n{e}\nRaw:\n{raw}") from e