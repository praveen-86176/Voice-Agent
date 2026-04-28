# ARIA Voice Agent

ARIA is a voice-enabled personal AI agent that can manage a to-do list using tool calls and remember important user interactions across sessions.

## What it does

- Voice input → text (STT) and spoken replies (TTS)
- Tool-based to-do management: add, update, delete, list
- Long-term memory saved in SQLite, with semantic recall via Chroma + embeddings
- A web UI that supports both typing and voice dictation

## Project structure

- `frontend_server.py`: Main web server (FastAPI) handling chat, memory, and to-do APIs
- `main.py`: Terminal-based agent loop (microphone input + spoken replies)
- `agent/`: Agent logic, tool schemas, and LLM provider (Groq)
- `tools/`: Todo and memory managers (SQLite + Chroma)
- `voice/`: Local STT (Google) and TTS (pyttsx3/ElevenLabs) modules
- `web/`: Frontend source (index.html)
- `storage/`: Local databases and vector index persistence

## Quick start (Web UI)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Fill in your `GROQ_API_KEY` in the `.env` file.

3. **Start the server**:
   ```bash
   python frontend_server.py
   ```

4. **Open**:
   - `http://127.0.0.1:8000`

3. Use:

- Type in the input box and press **Send**
- Click **Start Voice** to dictate (it converts speech to text and fills the input)
- Toggle **Auto-send Voice** to send immediately or let you edit first
- Toggle **Voice Reply** to enable/disable spoken replies in the browser

## Quick start (terminal voice mode)

```bash
cd "/Users/praveenkumar/Desktop/Voice Agent"
.venv/bin/python main.py
```

If your microphone is available, it listens and transcribes; otherwise it falls back to typed input.

## Install dependencies

This project uses a local virtual environment at `./.venv`.

```bash
cd "/Users/praveenkumar/Desktop/Voice Agent"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### Microphone support (macOS)

If installing `pyaudio` fails, install PortAudio first:

```bash
brew install portaudio
CPPFLAGS='-I/opt/homebrew/include' LDFLAGS='-L/opt/homebrew/lib' .venv/bin/pip install pyaudio
```

### Microphone support (Linux / Render)

If your deploy fails building `pyaudio` with `portaudio.h: No such file or directory`, install the system dependency first:

```bash
apt-get update && apt-get install -y portaudio19-dev
```

Then install the optional mic requirements:

```bash
.venv/bin/pip install -r requirements-voice-mic.txt
```

## Environment variables

Copy `.env.example` to `.env` and fill what you need.

Key options:

- `LLM_PROVIDER`: `local` (default) or `openai`
- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `STT_PROVIDER`: `google_stt` (default) or `whisper_local`
- `TTS_PROVIDER`: `pyttsx3` (default), `elevenlabs`, or `google_tts`
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`
- `EMBEDDING_PROVIDER`: `sentence_transformers` (default) or `openai`

## Notes on voice performance

- Browser voice is usually fastest because it uses the built-in Web Speech API.
- Terminal voice depends on microphone + network (Google STT) or Whisper configuration.
- For best results in browser: use Chrome/Edge and allow microphone permissions.

## Troubleshooting

- **“Voice Unsupported” in the web UI**: use Chrome or Edge; Safari often lacks Web Speech recognition.
- **Mic permission blocked**: allow microphone access for `http://127.0.0.1:8000` in your browser settings.
- **Port 8000 already in use**: stop the old server process or change the port in `frontend_server.py`.

