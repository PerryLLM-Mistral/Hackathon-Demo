from pathlib import Path

from .country_agent import CountryAgent

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

AGENTS = [
    CountryAgent(country_id="USA", country_name="United States", prompt_path=str(PROMPTS_DIR / "usa.txt")),
    CountryAgent(country_id="CHI", country_name="China", prompt_path=str(PROMPTS_DIR / "china.txt")),
    CountryAgent(country_id="RUS", country_name="Russia", prompt_path=str(PROMPTS_DIR / "russia.txt")),
]
