import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_OLLAMA_LLM_MODEL = os.getenv(
    "DEFAULT_LLM_MODEL", "deepseek-r1:1.5b-qwen-distill-q8_0"
)
DEFAULT_OPENAI_LLM_MODEL = os.getenv("DEFAULT_OPENAI_LLM_MODEL", "gpt-4.1-2025-04-14")
DEFAULT_ANTHROPIC_LLM_MODEL = os.getenv(
    "DEFAULT_ANTHROPIC_LLM_MODEL", "claude-sonnet-4-20250514"
)
DEFAULT_HF_LLM_MODEL = os.getenv("DEFAULT_HF_LLM_MODEL", "Qwen/Qwen2.5-14B-Instruct:featherless-ai")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

BASE_DIR = pathlib.Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPT_TEMPLATES_DIR = BASE_DIR / "config" / "prompt_templates"

PLANNER_PROMPT = PROMPT_TEMPLATES_DIR / "planner" / "prompt.txt"
PLANNER_EXAMPLES = PROMPT_TEMPLATES_DIR / "planner" / "examples.json"

EXPLORER_PROMPT = PROMPT_TEMPLATES_DIR / "explorer" / "prompt.txt"
EXPLORER_EXAMPLES = PROMPT_TEMPLATES_DIR / "explorer" / "examples.json"

PLAYBOOK_PROMPT = PROMPT_TEMPLATES_DIR / "playbook" / "prompt.txt"
PLAYBOOK_EXAMPLES = PROMPT_TEMPLATES_DIR / "playbook" / "examples.json"

UCO_NAMESPACE = "https://unifiedcyberontology.org/ontology/uco/"
