import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "lesson.json"

with open(path, encoding="utf-8") as f:
    lessons = json.load(f)["lessons"]

missing = [l for l in lessons if not str(l.get("example_word", "")).strip()]

for l in missing:
    print(f"Missing example_word: {l.get('id')} ({l.get('char')})")

print(f"\n{len(missing)} of {len(lessons)} lessons missing example_word.")
sys.exit(1 if missing else 0)