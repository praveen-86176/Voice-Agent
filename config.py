import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR = STORAGE_DIR / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

TODOS_DB_PATH = STORAGE_DIR / "todos.db"
MEMORIES_DB_PATH = STORAGE_DIR / "memories.db"

# Stack selection (recommended defaults + lightweight alternatives).
# LLM: openai | anthropic | gemini | local
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# STT: whisper_local | google_stt
STT_PROVIDER = os.getenv("STT_PROVIDER", "google_stt")

# TTS: elevenlabs | pyttsx3
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "pyttsx3")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
GOOGLE_TTS_LANG = os.getenv("GOOGLE_TTS_LANG", "en")

# Memory backend: sqlite | json
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "sqlite")

# Embeddings: openai | sentence_transformers
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
