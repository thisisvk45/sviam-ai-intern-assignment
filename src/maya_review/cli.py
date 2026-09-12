"""Command-line interface: build a reviewer report from fixture files.

Usage:
    maya-review fixtures/transcript.json fixtures/review_notes.json
    maya-review fixtures/transcript.json fixtures/review_notes.json --out report.md
    maya-review fixtures/transcript.json fixtures/review_notes.json --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import loader
from .report import build_report, render_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="maya-review",
        description="Build a reviewer report from an interview transcript "
        "and AI-generated review notes.",
    )
    parser.add_argument("transcript", help="path to a transcript JSON file")
    parser.add_argument("notes", help="path to a review-notes JSON file")
    parser.add_argument("--out", help="write the report to this file instead of stdout")
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the raw report dict as JSON instead of rendered text",
    )
    args = parser.parse_args(argv)

    transcript = loader.load_transcript(args.transcript)
    notes = loader.load_notes(args.notes)

    report = build_report(transcript, notes)
    output = json.dumps(report, indent=2) if args.json else render_report(report)

    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
