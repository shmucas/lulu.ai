from faster_whisper import WhisperModel

_model = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> str:
    segments, _ = get_model().transcribe(audio_path)
    return "".join(seg.text for seg in segments).strip()
