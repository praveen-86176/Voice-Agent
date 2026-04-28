import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR = STORAGE_DIR / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

TODOS_DB_PATH = STORAGE_DIR / "todos.db"
MEMORIES_DB_PATH = STORAGE_DIR / "memories.db"

# LLM (use Groq only)
# LLM_PROVIDER: groq | local
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Common Groq choices: llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")



# Memory backend: sqlite | json
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "sqlite")

# Embeddings (local only for now)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
