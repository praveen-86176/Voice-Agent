# Recommended Tech Stack Mapping

This project supports a progressive stack strategy: start lightweight, then switch to production providers with environment variables.

## LLM
- Recommended: GPT-4o or Claude 3.5 Sonnet
- Lightweight: Gemini Flash or local fallback planner
- Set via `LLM_PROVIDER` and provider-specific model variables

## STT
- Recommended: OpenAI Whisper (local) or Google STT API
- Current lightweight default: `SpeechRecognition` with Google recognizer
- Set via `STT_PROVIDER`

## TTS
- Recommended: ElevenLabs API
- Lightweight default: pyttsx3 (offline)
- Set via `TTS_PROVIDER`

## Memory Database
- Recommended: SQLite with embeddings
- Lightweight alternative: JSON (planned toggle through `MEMORY_BACKEND`)
- Current default: SQLite

## Function Calling
- OpenAI tools format is modeled by `agent/tool_schemas.py`
- Router entrypoint: `agent/function_router.py` via `route(tool_name, arguments)`

## Embeddings
- Recommended cloud: `text-embedding-3-small`
- Lightweight local: `all-MiniLM-L6-v2`
- Set via `EMBEDDING_PROVIDER`

## Quick Setup
1. Copy `.env.example` to `.env`
2. Fill only the providers you want to use
3. Keep lightweight defaults for offline/local development
