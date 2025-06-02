import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "tinyllama")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

BASE_DIR = pathlib.Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPT_TEMPLATES_DIR = BASE_DIR / "config" / "prompt_templates"

UCO_NAMESPACE = "https://unifiedcyberontology.org/ontology/uco/"
