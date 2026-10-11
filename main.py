#!/usr/bin/env python3
"""birdjournal - identify bird calls offline and write a field-journal entry.

Examples:
  python main.py walk.wav --place "Sheesh Mahal Gardens, Patiala"
  python main.py walk.mp3 --lat 30.33 --lon 76.40 --model gemma3:4b --language Hindi
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from detector import detect, summarise
from journal import write_entry


def main() -> int:
    p = argparse.ArgumentParser(description="Offline bird call field journal")
    p.add_argument("audio", help="Audio file (wav/mp3/flac) recorded outdoors")
    p.add_argument("--place", default="somewhere outdoors")
    p.add_argument("--lat", type=float, help="Latitude (improves accuracy)")
    p.add_argument("--lon", type=float, help="Longitude (improves accuracy)")
    p.add_argument("--min-conf", type=float, default=0.4)
    p.add_argument("--model", default="qwen2.5:3b", help="Any Ollama model")
    p.add_argument("--language", default="English")
    p.add_argument("--out", help="Save journal entry to this .md file")
    args = p.parse_args()

    now = dt.datetime.now()
    week = int(now.strftime("%V"))
    when = now.strftime("%A %d %B %Y, %I:%M %p")

    print(f"Listening to {args.audio} ...")
    detections = detect(args.audio, args.lat, args.lon, week, args.min_conf)
    summary = summarise(detections)

    print(f"\nSpecies heard: {len(summary)}")
    for s in summary:
        print(
            f"  {s['common_name']:<28} x{s['count']:<3} "
            f"best {s['best_confidence']:.0%}  first at {s['first_heard_s']:.0f}s"
        )

    print("\nWriting journal entry with local model ...")
    text, used_llm = write_entry(
        summary, args.place, when, args.model, args.language
    )
    print("\n" + text)

    if args.out:
        lines = [f"# Field journal - {when}", f"**Place:** {args.place}", ""]
        lines += ["| Species | Heard | Best confidence |", "|---|---|---|"]
        for s in summary:
            lines.append(
                f"| {s['common_name']} | {s['count']}x | {s['best_confidence']:.0%} |"
            )
        lines += ["", text, ""]
        Path(args.out).write_text("\n".join(lines), encoding="utf-8")
        print(f"\nSaved to {args.out}")

    if not used_llm:
        print("(Tip: install Ollama and run `ollama pull qwen2.5:3b` for richer entries.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
