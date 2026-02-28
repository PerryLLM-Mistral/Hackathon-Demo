"""
llm package

Optional LLM integration layer:
- provider.py: talks to a model (OpenAI/Ollama/etc.) OR a stub for hackathon
- parser.py: parses model output into structured Action
- guardrails.py: enforces safety/validity constraints on Action
"""

from .provider import MistralProvider

__all__ = ["MistralProvider"]