"""Save YouTube transcripts that guides are based on.

  python tools/fetch_transcript.py JEWRiaOb9JY gwMMpH-OY9c

Writes data/transcripts/<video id>.json: {"video", "lang", "rows": [{"t": seconds, "text"}]}.
Prefers an English track (manual over auto-generated). Needs youtube-transcript-api.
"""
import json
import sys
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

OUT = Path(__file__).resolve().parent.parent / "data" / "transcripts"


def main(ids):
    OUT.mkdir(parents=True, exist_ok=True)
    api = YouTubeTranscriptApi()
    for vid in ids:
        tracks = api.list(vid)
        try:
            track = tracks.find_transcript(["en", "en-US", "en-GB"])
        except Exception:
            track = next(iter(tracks))
        rows = [{"t": round(s.start), "text": s.text} for s in track.fetch()]
        (OUT / f"{vid}.json").write_text(
            json.dumps({"video": vid, "lang": track.language_code, "rows": rows}, ensure_ascii=False), encoding="utf-8")
        print(f"{vid}: {len(rows)} lines ({track.language_code})")


if __name__ == "__main__":
    main(sys.argv[1:])
