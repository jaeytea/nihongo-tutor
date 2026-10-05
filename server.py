import shutil
import tempfile
import unicodedata
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from faster_whisper import WhisperModel
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pykakasi import kakasi
from llm import ask_llm


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


class ExplainRequest(BaseModel):
    expected: str
    meaning_hi: str
    heard: str


EXPLAIN_SYSTEM_PROMPT = (
    "You are a kind Japanese tutor for a 6th grade child whose first language is Hindi. "
    "The child tried to say a Japanese word and said something different. "
    "In at most 2 short sentences, in simple Hindi, tell them what to listen for or fix. "
    "Write any Japanese only in hiragana. Be encouraging and never harsh. "
    "If you are not sure, say so instead of guessing."
)
EXPLAIN_FALLBACK = "थोड़ा और ध्यान से सुनो और फिर से कोशिश करो!"
ASK_SYSTEM_PROMPT = (
    "You are a friendly Japanese tutor for a 6th grade child whose first language is Hindi. "
    "Answer only in simple Hindi in at most 3 short sentences. "
    "Write Japanese only in hiragana, with english/romaji. "
    "Only answer questions about learning Japanese; for anything else, kindly say you can only help with Japanese. "
    "If you are not sure, say so instead of guessing. Never invent words. "
    "Only talk about learning Japanese. Never talk about real people, celebrities, music, games or news. Never guess."
)
ASK_FALLBACK = "अभी जवाब नहीं मिल पाया। चलो, जापानी सीखते रहें!"
SAVED_QUESTION_MESSAGE = "यह सवाल मैंने सेव कर लिया है, भैया/दीदी से पूछना!"


@app.post("/explain")
def explain_pronunciation(payload: ExplainRequest) -> dict[str, str]:
    user_message = (
        f"Expected Japanese word: {payload.expected}\n"
        f"Hindi meaning: {payload.meaning_hi}\n"
        f"Whisper heard: {payload.heard}"
    )
    reply = ask_llm(EXPLAIN_SYSTEM_PROMPT, user_message)
    if reply and reply.strip():
        return {"message": reply.strip(), "source": "llm"}
    return {"message": EXPLAIN_FALLBACK, "source": "fallback"}


class AskRequest(BaseModel):
    question: str = Field(max_length=200)


def is_japanese_question(question: str) -> bool:
    has_kana = any(
        "\u3041" <= character <= "\u3096"
        or "\u309d" <= character <= "\u309f"
        or "\u30a1" <= character <= "\u30fa"
        or "\u30fd" <= character <= "\u30ff"
        or "\u31f0" <= character <= "\u31ff"
        for character in question
    )
    if has_kana:
        return True

    keywords = (
        "japanese",
        "hiragana",
        "katakana",
        "pronounce",
        "say",
        "word",
        "sound",
        "meaning",
        "जापानी",
        "हिरागाना",
        "उच्चारण",
        "बोलते",
        "कहते",
        "शब्द",
        "मतलब",
    )
    lowered_question = question.casefold()
    return any(keyword in lowered_question for keyword in keywords)


@app.post("/ask")
def ask_question(payload: AskRequest) -> dict[str, str]:
    if not is_japanese_question(payload.question):
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        saved_question = payload.question.replace("\r", " ").replace("\n", " ")
        with (BASE_DIR / "questions.txt").open("a", encoding="utf-8") as questions_file:
            questions_file.write(f"[{timestamp}] {saved_question}\n")
        return {"message": SAVED_QUESTION_MESSAGE, "source": "saved"}

    reply = ask_llm(
        ASK_SYSTEM_PROMPT,
        payload.question,
        temperature=0.2,
        max_tokens=120,
    )
    if reply and reply.strip():
        return {"message": reply.strip(), "source": "llm"}
    return {"message": ASK_FALLBACK, "source": "fallback"}


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