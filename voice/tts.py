import subprocess
import tempfile
from threading import Lock
from pathlib import Path

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, GOOGLE_TTS_LANG, TTS_PROVIDER

_pyttsx3_engine = None
_tts_lock = Lock()


def _play_file(path: str) -> None:
    try:
        subprocess.run(["afplay", path], check=False, capture_output=True)
    except Exception:
        return


def _speak_elevenlabs(text: str) -> bool:
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        return False
    try:
        import requests  # type: ignore

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        }
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}
        response = requests.post(url, json=payload, headers=headers, timeout=40)
        if response.status_code != 200:
            return False
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        _play_file(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _speak_google_tts(text: str) -> bool:
    try:
        from gtts import gTTS  # type: ignore

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name
        gTTS(text=text, lang=GOOGLE_TTS_LANG).save(tmp_path)
        _play_file(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        return True
    except Exception:
        return False


def speak(text: str) -> None:
    """
    Provider-based speech output with local fallback.
    """
    print(f"ARIA: {text}")
    if TTS_PROVIDER == "elevenlabs" and _speak_elevenlabs(text):
        return
    if TTS_PROVIDER == "google_tts" and _speak_google_tts(text):
        return
    try:
        import pyttsx3  # type: ignore

        global _pyttsx3_engine
        with _tts_lock:
            if _pyttsx3_engine is None:
                _pyttsx3_engine = pyttsx3.init()
                _pyttsx3_engine.setProperty("rate", 175)
            _pyttsx3_engine.say(text)
            _pyttsx3_engine.runAndWait()
    except Exception:
        return
