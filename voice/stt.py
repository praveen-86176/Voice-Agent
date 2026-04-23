import io
from typing import Any

from config import OPENAI_API_KEY, STT_PROVIDER

_recognizer = None
_calibrated = False


def _get_recognizer():
    global _recognizer
    if _recognizer is not None:
        return _recognizer
    try:
        import speech_recognition as sr  # type: ignore

        _recognizer = sr.Recognizer()
        _recognizer.dynamic_energy_threshold = True
        _recognizer.pause_threshold = 0.6
        _recognizer.non_speaking_duration = 0.25
        return _recognizer
    except Exception:
        return None


def capture_microphone_input() -> Any:
    """
    Capture microphone audio when speech_recognition is available.
    Falls back to typed input for environments without mic support.
    """
    recognizer = _get_recognizer()
    if recognizer is None:
        try:
            return input("You (type fallback): ").strip()
        except EOFError:
            return ""

    try:
        import speech_recognition as sr  # type: ignore

        with sr.Microphone() as source:
            print("Listening...")
            global _calibrated
            if not _calibrated:
                recognizer.adjust_for_ambient_noise(source, duration=0.25)
                _calibrated = True
            try:
                # Shorter phrase limit improves perceived responsiveness.
                return recognizer.listen(source, timeout=6, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return ""
    except Exception:
        try:
            return input("You (type fallback): ").strip()
        except EOFError:
            return ""


def speech_to_text(audio: Any) -> str:
    """
    Convert captured audio to text.
    Supports speech_recognition audio or already-typed fallback strings.
    """
    if isinstance(audio, str):
        return audio.strip()

    if STT_PROVIDER == "whisper_local" and OPENAI_API_KEY:
        try:
            from openai import OpenAI  # type: ignore

            wav_bytes = audio.get_wav_data()
            file_obj = io.BytesIO(wav_bytes)
            file_obj.name = "audio.wav"
            client = OpenAI(api_key=OPENAI_API_KEY)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=file_obj,
            )
            return (transcript.text or "").strip()
        except Exception:
            pass

    recognizer = _get_recognizer()
    if recognizer is None:
        return ""

    try:
        return recognizer.recognize_google(audio).strip()
    except Exception:
        return ""
