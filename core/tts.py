import os
import subprocess
import tempfile

PIPER_BIN = os.path.expanduser("~/piper/piper")
VOICE_MODEL = os.path.expanduser("~/piper/en_US-lessac-medium.onnx")

_proc: subprocess.Popen | None = None


def stop() -> None:
    global _proc
    if _proc and _proc.poll() is None:
        _proc.terminate()
    _proc = None


def speak(text: str) -> None:
    global _proc
    stop()

    if os.path.exists(PIPER_BIN) and os.path.exists(VOICE_MODEL):
        _speak_piper(text)
    else:
        _speak_say(text)

    _proc = None


def _speak_piper(text: str) -> None:
    global _proc
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        subprocess.run(
            [PIPER_BIN, "--model", VOICE_MODEL, "--output_file", wav_path],
            input=text.encode(),
            check=True,
            capture_output=True,
        )
        _proc = subprocess.Popen(["afplay", wav_path])
        _proc.wait()
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


def _speak_say(text: str) -> None:
    global _proc
    _proc = subprocess.Popen(["say", text])
    _proc.wait()
