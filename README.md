# Nihongo Tutor 🇯🇵

A small Japanese tutor I built for my little brother, who is in 6th grade and wants to learn Japanese. His first language is Hindi, so the tutor teaches through Hindi instead of English: every new sound comes with a Hindi hint, and the Hindi shrinks as he progresses.

Built for the Hacktoberfest Weekend Challenge: **Build for a Friend**.

## Why I made this

My brother is excited about Japanese, but almost every beginner resource assumes you know English. He shouldn't have to learn through a second language just to learn a third one. So I made something that speaks his language, runs on his own laptop, and is patient with him.

## What it does

- Teaches the 46 basic hiragana, one at a time, with a Hindi hint for each (like "'क' जैसा, जैसे 'कल' में")
- Plays a native-sounding audio clip for every sound and example word
- Gives each character an example word (あ → あめ, "rain") so he learns from real words
- **Say it and I'll check:** he taps the mic, says the word, and the app tells him whether it heard it right. Feedback is always gentle, and he can skip any word.
- _(In progress)_ A local language model that explains his mistakes in simple Hindi

Katakana is in the plan, but I held it back on purpose. One script at a time is enough for a beginner.

## How it works

| Piece                               | What I used                                                                            | Runs where                                                            |
| ----------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Listening (checks his speaking)     | [faster-whisper](https://github.com/SYSTRAN/faster-whisper), open-weight Whisper model | Locally, on the laptop                                                |
| Explaining mistakes _(in progress)_ | Gemma via [Ollama](https://ollama.com)                                                 | Locally, swappable for any OpenAI-compatible model                    |
| Server                              | FastAPI                                                                                | Locally                                                               |
| Lesson audio                        | ElevenLabs                                                                             | **Once, at build time.** The mp3 files are saved and played from disk |
| App                                 | Plain HTML and JavaScript                                                              | Browser                                                               |

The lessons are fixed and written by hand in `lesson.json`. I didn't want a language model inventing content, because small models make mistakes and a kid will believe them. The AI handles the parts that need listening and explaining, and the curriculum stays under my control.

## Setup

You need Python 3 and a Mac or Linux machine (I built this on a MacBook M4).

```bash
git clone <your-repo-url>
cd nihongo-tutor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then start the server:

```bash
<replace with your exact run command, for example: uvicorn server:app --port 8000>
```

Open `http://localhost:8000` in your browser and allow the microphone when asked.

**Note:** the first time you run it, faster-whisper downloads its model, so you need internet once. After that, the speech check works offline.

### Regenerating the audio (optional)

The audio is generated with ElevenLabs. If you want to regenerate it or change the voice, create a `.env` file:

```
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
```

Then run `python3 generate_audio.py` (or `python3 generate_audio.py hira_a` for a single lesson). Never commit your `.env` file.

## Project structure

```
nihongo-tutor/
  server.py           FastAPI server and the /check endpoint
  index.html          The app
  lesson.json         All lessons: characters, hints, example words
  generate_audio.py   Makes the mp3 files (run once)
  check_words.py      Checks that every lesson has an example word
  audio/              Generated audio
```

## Why open-source AI?

- **His voice stays on his laptop.** The mic recording is transcribed locally and thrown away. Nothing about a child's voice or mistakes goes to someone else's server.
- **It works without internet** once the models are downloaded.
- **It costs nothing to run.** No per-request fees and no API key needed for daily use.
- **I can change it.** I can swap the speech model or the language model, tune the matching to how a kid actually speaks, and compare models on real Hindi questions. With a closed API, I'd have to take what it gives me.

I'll be honest about the one closed piece: I used ElevenLabs for the lesson audio, because good Hindi and Japanese voices matter for pronunciation and I only needed them once. Everything that touches him day to day is open and local.

## What I learned

_(Fill this in after testing. Notes to include: where Whisper struggled with a beginner's accent, which words needed alternate spellings, which model's Hindi was better.)_

## What my brother said

_(Add his reaction here after he tries it.)_

## What's next

- Local model that explains mistakes in Hindi
- A "time and numbers" helper that uses code, not the model, so readings are always correct
- Katakana as a second level
- A simple review system so old sounds come back at the right time

## Credits

Built by [your name]. Thanks to my brother for being my first (and toughest) user.

Licensed under [choose a license, for example MIT].
