# app/multi_llm/agents/registry.py

from app.multi_llm.agents.country_agent import CountryAgent

AGENTS = [
    CountryAgent(country_id="USA", country_name="United States", prompt_path="app/multi_llm/agents/prompts/usa.txt"),
    CountryAgent(country_id="CHI", country_name="China",         prompt_path="app/multi_llm/agents/prompts/china.txt"),
    CountryAgent(country_id="RUS", country_name="Russia",        prompt_path="app/multi_llm/agents/prompts/russia.txt"),
]