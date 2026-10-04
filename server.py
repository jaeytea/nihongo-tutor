import shutil
import tempfile
import unicodedata
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from faster_whisper import WhisperModel
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pykakasi import kakasi


BASE_DIR = Path(__file__).resolve().parent
KANA_CONVERTER = kakasi()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.whisper_model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8",
    )
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/audio", StaticFiles(directory=BASE_DIR / "audio"), name="audio")


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html", media_type="text/html")


@app.get("/lesson.json", include_in_schema=False)
def serve_lessons() -> FileResponse:
    return FileResponse(BASE_DIR / "lesson.json", media_type="application/json")


def normalize_text(text: str) -> str:
    hiragana = "".join(part["hira"] for part in KANA_CONVERTER.convert(text))
    normalized = unicodedata.normalize("NFKC", hiragana)
    return "".join(
        character
        for character in normalized
        if not character.isspace()
        and not unicodedata.category(character).startswith("P")
    )


@app.post("/check")
def check_pronunciation(
    request: Request,
    audio: UploadFile = File(...),
    expected: str = Form(...),
    accepted: list[str] | None = Form(default=None),
) -> dict[str, str | bool]:
    expected_normalized = normalize_text(expected)
    if not expected_normalized:
        raise HTTPException(status_code=422, detail="expected must contain a word")

    suffix = Path(audio.filename or "audio.wav").suffix or ".audio"
    with tempfile.NamedTemporaryFile(suffix=suffix) as temporary_audio:
        shutil.copyfileobj(audio.file, temporary_audio)
        temporary_audio.flush()
        segments, _ = request.app.state.whisper_model.transcribe(
            temporary_audio.name,
            language="ja",
        )
        transcript = "".join(segment.text for segment in segments).strip()

    print(f"Raw transcript: {transcript}", flush=True)
    transcript_normalized = normalize_text(transcript)
    accepted_normalized = [normalize_text(word) for word in accepted or []]
    # Check the primary spelling and any lesson-specific alternatives.
    correct = any(
        word and word in transcript_normalized
        for word in [expected_normalized, *accepted_normalized]
    )

    return {
        "transcript": transcript,
        "expected_normalized": expected_normalized,
        "transcript_normalized": transcript_normalized,
        "correct": correct,
    }