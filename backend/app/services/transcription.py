import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str) -> str:
    """Extract audio track from video file using ffmpeg."""
    audio_path = tempfile.mktemp(suffix=".wav")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path, "-y",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr}")
    return audio_path


def transcribe_audio(audio_path: str, model_name: str = "large-v3") -> str:
    """Transcribe audio using OpenAI Whisper."""
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, language=None)
    return result["text"]


def diarize_audio(audio_path: str) -> list[dict]:
    """Perform speaker diarization using pyannote.audio.

    Returns list of segments: [{"speaker": "SPEAKER_01", "start": 0.0, "end": 5.0}, ...]
    """
    from pyannote.audio import Pipeline

    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    diarization = pipeline(audio_path)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end,
        })
    return segments


def transcribe_with_diarization(audio_path: str, model_name: str = "large-v3") -> str:
    """Transcribe audio and align with speaker diarization."""
    import whisper

    model = whisper.load_model(model_name)
    whisper_result = model.transcribe(audio_path, language=None)
    whisper_segments = whisper_result.get("segments", [])

    try:
        diarization_segments = diarize_audio(audio_path)
    except Exception:
        logger.warning("Diarization failed, returning plain transcript")
        return whisper_result["text"]

    lines: list[str] = []
    for ws in whisper_segments:
        seg_mid = (ws["start"] + ws["end"]) / 2
        speaker = _find_speaker(diarization_segments, seg_mid)
        lines.append(f"[{speaker}]: {ws['text'].strip()}")

    return "\n".join(lines)


def _find_speaker(segments: list[dict], time_point: float) -> str:
    for seg in segments:
        if seg["start"] <= time_point <= seg["end"]:
            return seg["speaker"]
    return "Неизвестный"


def read_text_file(file_path: str) -> str:
    """Read text from .txt or .docx file."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
