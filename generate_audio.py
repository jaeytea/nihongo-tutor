import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def find_lessons_file() -> Path:
    for name in ("lessons.json", "lesson.json"):
        path = Path(name)
        if path.is_file():
            return path
    raise FileNotFoundError("Could not find lessons.json or lesson.json")


def generate_audio(text: str, destination: Path, api_key: str, voice_id: str) -> None:
    request = Request(
        API_URL.format(voice_id=voice_id),
        data=json.dumps(
            {
                "text": text,
                "model_id": "eleven_multilingual_v2",
            }
        ).encode("utf-8"),
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )

    with urlopen(request) as response:
        audio_data = response.read()

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(audio_data)


def generate_if_missing(
    text: str, destination: Path, api_key: str, voice_id: str
 ) -> None:
    if destination.exists():
        print(f"Skipped existing {destination}")
        return
    generate_audio(text, destination, api_key, voice_id)
    print(f"Generated {destination} for {text}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an MP3 for each lesson using the ElevenLabs API."
    )
    parser.add_argument(
        "lesson",
        nargs="?",
        help="lesson id or unique sound label to generate (e.g. hira_a or a)",
    )
    parser.add_argument(
        "--lessons-file",
        type=Path,
        help="JSON file to read (defaults to lessons.json or lesson.json)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    if not api_key or not voice_id:
        parser.error("set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in the environment")

    try:
        lessons_file = args.lessons_file or find_lessons_file()
        data = json.loads(lessons_file.read_text(encoding="utf-8"))
        lessons = data["lessons"]

        if args.lesson:
            matches = [lesson for lesson in lessons if lesson.get("id") == args.lesson]
            if not matches:
                matches = [lesson for lesson in lessons if lesson.get("sound") == args.lesson]
            if len(matches) > 1:
                hiragana_matches = [
                    lesson for lesson in matches if lesson.get("script") == "hiragana"
                ]
                if len(hiragana_matches) == 1:
                    matches = hiragana_matches
            if not matches:
                raise ValueError(f"No lesson found with id or sound label '{args.lesson}'")
            if len(matches) > 1:
                raise ValueError(f"'{args.lesson}' matches multiple lessons; use a lesson id")
            lessons = matches

        json_updated = False
        for lesson in lessons:
            generate_if_missing(lesson["char"], Path(lesson["audio"]), api_key, voice_id)

            example_word = lesson.get("example_word")
            if example_word:
                example_destination = Path("audio") / "words" / f"{lesson['id']}.mp3"
                example_audio = example_destination.as_posix()
                if lesson.get("example_audio") != example_audio:
                    lesson["example_audio"] = example_audio
                    json_updated = True
                generate_if_missing(
                    example_word,
                    example_destination,
                    api_key,
                    voice_id,
                )

        if json_updated:
            temporary_file = lessons_file.with_name(f".{lessons_file.name}.tmp")
            temporary_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_file.replace(lessons_file)
    except (
        FileNotFoundError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        HTTPError,
        URLError,
        ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())



"""
{
      "id": "kata_a",
      "script": "katakana",
      "char": "ア",
      "sound": "a",
      "hindi_hint": "'अ' जैसा, जैसे 'अब' में",
      "audio": "audio/katakana/a.mp3"
    },
    {
      "id": "kata_i",
      "script": "katakana",
      "char": "イ",
      "sound": "i",
      "hindi_hint": "'इ' जैसा, जैसे 'इधर' में",
      "audio": "audio/katakana/i.mp3"
    },
    {
      "id": "kata_u",
      "script": "katakana",
      "char": "ウ",
      "sound": "u",
      "hindi_hint": "'उ' जैसा, जैसे 'उधर' में (होंठ गोल न करें)",
      "audio": "audio/katakana/u.mp3"
    },
    {
      "id": "kata_e",
      "script": "katakana",
      "char": "エ",
      "sound": "e",
      "hindi_hint": "'ए' जैसा, जैसे 'एक' में",
      "audio": "audio/katakana/e.mp3"
    },
    {
      "id": "kata_o",
      "script": "katakana",
      "char": "オ",
      "sound": "o",
      "hindi_hint": "'ओ' जैसा, जैसे 'ओर' में",
      "audio": "audio/katakana/o.mp3"
    },
    {
      "id": "kata_ka",
      "script": "katakana",
      "char": "カ",
      "sound": "ka",
      "hindi_hint": "'क' जैसा, जैसे 'कल' में",
      "audio": "audio/katakana/ka.mp3"
    },
    {
      "id": "kata_ki",
      "script": "katakana",
      "char": "キ",
      "sound": "ki",
      "hindi_hint": "'कि' जैसा, जैसे 'किताब' में",
      "audio": "audio/katakana/ki.mp3"
    },
    {
      "id": "kata_ku",
      "script": "katakana",
      "char": "ク",
      "sound": "ku",
      "hindi_hint": "'कु' जैसा, जैसे 'कुत्ता' में",
      "audio": "audio/katakana/ku.mp3"
    },
    {
      "id": "kata_ke",
      "script": "katakana",
      "char": "ケ",
      "sound": "ke",
      "hindi_hint": "'के' जैसा, जैसे 'केला' में",
      "audio": "audio/katakana/ke.mp3"
    },
    {
      "id": "kata_ko",
      "script": "katakana",
      "char": "コ",
      "sound": "ko",
      "hindi_hint": "'को' जैसा, जैसे 'कोयल' में",
      "audio": "audio/katakana/ko.mp3"
    },
    {
      "id": "kata_sa",
      "script": "katakana",
      "char": "サ",
      "sound": "sa",
      "hindi_hint": "'स' जैसा, जैसे 'सब' में",
      "audio": "audio/katakana/sa.mp3"
    },
    {
      "id": "kata_shi",
      "script": "katakana",
      "char": "シ",
      "sound": "shi",
      "hindi_hint": "'शि' जैसा, जैसे 'शिकार' में",
      "audio": "audio/katakana/shi.mp3"
    },
    {
      "id": "kata_su",
      "script": "katakana",
      "char": "ス",
      "sound": "su",
      "hindi_hint": "'सु' जैसा, जैसे 'सुबह' में",
      "audio": "audio/katakana/su.mp3"
    },
    {
      "id": "kata_se",
      "script": "katakana",
      "char": "セ",
      "sound": "se",
      "hindi_hint": "'से' जैसा, जैसे 'सेब' में",
      "audio": "audio/katakana/se.mp3"
    },
    {
      "id": "kata_so",
      "script": "katakana",
      "char": "ソ",
      "sound": "so",
      "hindi_hint": "'सो' जैसा, जैसे 'सोना' में",
      "audio": "audio/katakana/so.mp3"
    },
    {
      "id": "kata_ta",
      "script": "katakana",
      "char": "タ",
      "sound": "ta",
      "hindi_hint": "'ता' जैसा, जैसे 'ताला' में",
      "audio": "audio/katakana/ta.mp3"
    },
    {
      "id": "kata_chi",
      "script": "katakana",
      "char": "チ",
      "sound": "chi",
      "hindi_hint": "'ची' जैसा, जैसे 'चीनी' में",
      "audio": "audio/katakana/chi.mp3"
    },
    {
      "id": "kata_tsu",
      "script": "katakana",
      "char": "ツ",
      "sound": "tsu",
      "hindi_hint": "'त्सु' जैसा, जैसे 'मत्स्य' के 'त्स' + 'उ'",
      "audio": "audio/katakana/tsu.mp3"
    },
    {
      "id": "kata_te",
      "script": "katakana",
      "char": "テ",
      "sound": "te",
      "hindi_hint": "'ते' जैसा, जैसे 'तेज़' में",
      "audio": "audio/katakana/te.mp3"
    },
    {
      "id": "kata_to",
      "script": "katakana",
      "char": "ト",
      "sound": "to",
      "hindi_hint": "'तो' जैसा, जैसे 'तोता' में",
      "audio": "audio/katakana/to.mp3"
    },
    {
      "id": "kata_na",
      "script": "katakana",
      "char": "ナ",
      "sound": "na",
      "hindi_hint": "'ना' जैसा, जैसे 'नमक' में",
      "audio": "audio/katakana/na.mp3"
    },
    {
      "id": "kata_ni",
      "script": "katakana",
      "char": "ニ",
      "sound": "ni",
      "hindi_hint": "'नि' जैसा, जैसे 'निशान' में",
      "audio": "audio/katakana/ni.mp3"
    },
    {
      "id": "kata_nu",
      "script": "katakana",
      "char": "ヌ",
      "sound": "nu",
      "hindi_hint": "'नु' जैसा, जैसे 'नुकसान' में",
      "audio": "audio/katakana/nu.mp3"
    },
    {
      "id": "kata_ne",
      "script": "katakana",
      "char": "ネ",
      "sound": "ne",
      "hindi_hint": "'ने' जैसा, जैसे 'नेता' में",
      "audio": "audio/katakana/ne.mp3"
    },
    {
      "id": "kata_no",
      "script": "katakana",
      "char": "ノ",
      "sound": "no",
      "hindi_hint": "'नो' जैसा, जैसे 'नोट' में",
      "audio": "audio/katakana/no.mp3"
    },
    {
      "id": "kata_ha",
      "script": "katakana",
      "char": "ハ",
      "sound": "ha",
      "hindi_hint": "'ह' जैसा, जैसे 'हम' में",
      "audio": "audio/katakana/ha.mp3"
    },
    {
      "id": "kata_hi",
      "script": "katakana",
      "char": "ヒ",
      "sound": "hi",
      "hindi_hint": "'हि' जैसा, जैसे 'हिरन' में",
      "audio": "audio/katakana/hi.mp3"
    },
    {
      "id": "kata_fu",
      "script": "katakana",
      "char": "フ",
      "sound": "fu",
      "hindi_hint": "'फु' और 'हु' के बीच, होंठों से हल्की हवा छोड़ें",
      "audio": "audio/katakana/fu.mp3"
    },
    {
      "id": "kata_he",
      "script": "katakana",
      "char": "ヘ",
      "sound": "he",
      "hindi_hint": "'हे' जैसा, जैसे 'हेलो' में",
      "audio": "audio/katakana/he.mp3"
    },
    {
      "id": "kata_ho",
      "script": "katakana",
      "char": "ホ",
      "sound": "ho",
      "hindi_hint": "'हो' जैसा, जैसे 'होंठ' में",
      "audio": "audio/katakana/ho.mp3"
    },
    {
      "id": "kata_ma",
      "script": "katakana",
      "char": "マ",
      "sound": "ma",
      "hindi_hint": "'म' जैसा, जैसे 'मन' में",
      "audio": "audio/katakana/ma.mp3"
    },
    {
      "id": "kata_mi",
      "script": "katakana",
      "char": "ミ",
      "sound": "mi",
      "hindi_hint": "'मि' जैसा, जैसे 'मिठाई' में",
      "audio": "audio/katakana/mi.mp3"
    },
    {
      "id": "kata_mu",
      "script": "katakana",
      "char": "ム",
      "sound": "mu",
      "hindi_hint": "'मु' जैसा, जैसे 'मुँह' में",
      "audio": "audio/katakana/mu.mp3"
    },
    {
      "id": "kata_me",
      "script": "katakana",
      "char": "メ",
      "sound": "me",
      "hindi_hint": "'मे' जैसा, जैसे 'मेला' में",
      "audio": "audio/katakana/me.mp3"
    },
    {
      "id": "kata_mo",
      "script": "katakana",
      "char": "モ",
      "sound": "mo",
      "hindi_hint": "'मो' जैसा, जैसे 'मोर' में",
      "audio": "audio/katakana/mo.mp3"
    },
    {
      "id": "kata_ya",
      "script": "katakana",
      "char": "ヤ",
      "sound": "ya",
      "hindi_hint": "'य' जैसा, जैसे 'यहाँ' में",
      "audio": "audio/katakana/ya.mp3"
    },
    {
      "id": "kata_yu",
      "script": "katakana",
      "char": "ユ",
      "sound": "yu",
      "hindi_hint": "'यु' जैसा, जैसे 'युग' में",
      "audio": "audio/katakana/yu.mp3"
    },
    {
      "id": "kata_yo",
      "script": "katakana",
      "char": "ヨ",
      "sound": "yo",
      "hindi_hint": "'यो' जैसा, जैसे 'योग' में",
      "audio": "audio/katakana/yo.mp3"
    },
    {
      "id": "kata_ra",
      "script": "katakana",
      "char": "ラ",
      "sound": "ra",
      "hindi_hint": "'र' और 'ड़' के बीच, जैसे 'रात' में हल्की जीभ",
      "audio": "audio/katakana/ra.mp3"
    },
    {
      "id": "kata_ri",
      "script": "katakana",
      "char": "リ",
      "sound": "ri",
      "hindi_hint": "'रि' जैसा, जैसे 'रिश्ता' में",
      "audio": "audio/katakana/ri.mp3"
    },
    {
      "id": "kata_ru",
      "script": "katakana",
      "char": "ル",
      "sound": "ru",
      "hindi_hint": "'रु' जैसा, जैसे 'रुपया' में",
      "audio": "audio/katakana/ru.mp3"
    },
    {
      "id": "kata_re",
      "script": "katakana",
      "char": "レ",
      "sound": "re",
      "hindi_hint": "'रे' जैसा, जैसे 'रेल' में",
      "audio": "audio/katakana/re.mp3"
    },
    {
      "id": "kata_ro",
      "script": "katakana",
      "char": "ロ",
      "sound": "ro",
      "hindi_hint": "'रो' जैसा, जैसे 'रोटी' में",
      "audio": "audio/katakana/ro.mp3"
    },
    {
      "id": "kata_wa",
      "script": "katakana",
      "char": "ワ",
      "sound": "wa",
      "hindi_hint": "'वा' जैसा, जैसे 'वाह' में",
      "audio": "audio/katakana/wa.mp3"
    },
    {
      "id": "kata_wo",
      "script": "katakana",
      "char": "ヲ",
      "sound": "wo",
      "hindi_hint": "'ओ' जैसा (सिर्फ़ कारक-कण के रूप में, 'वो' नहीं)",
      "audio": "audio/katakana/wo.mp3"
    },
    {
      "id": "kata_n",
      "script": "katakana",
      "char": "ン",
      "sound": "n",
      "hindi_hint": "'न्' जैसा, आधा न, जैसे 'हिन्दी' के 'न्' में",
      "audio": "audio/katakana/n.mp3"
    }
"""