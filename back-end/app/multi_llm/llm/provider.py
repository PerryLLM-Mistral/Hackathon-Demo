from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMProvider:
    """
    Minimal LLM provider abstraction.

    For hackathon:
    - Keep it disabled and let agents run heuristics.
    Later:
    - Implement real calls (OpenAI/Ollama/etc.) inside generate().
    """
    enabled: bool = False

    async def generate(self, prompt: str) -> str:
        """
        Returns raw text from the model.
        In stub mode, returns a PASS action as JSON.
        """
        if not self.enabled:
            # In a real implementation, this would never be used
            # because orchestrator.use_llm would be False.
            return '{"type":"PASS","target_id":null,"reason":"LLM disabled","intensity":1}'

        # TODO: integrate real model call here
        # Keep function async to match future providers.
        return '{"type":"PASS","target_id":null,"reason":"Not implemented","intensity":1}'