"""Load transcript and review-note fixtures from disk.

The transcript is trusted input produced by our own recording pipeline, so it
is validated strictly here. Review notes are *model output*: they are loaded
as plain JSON and deliberately NOT validated — deciding how to handle
malformed or untrustworthy notes is the report builder's job (see CONTRACT.md).
"""

from __future__ import annotations

import json
from pathlib import Path


class TranscriptError(ValueError):
    """Raised when a transcript file does not match the expected shape."""


def load_transcript(path: str | Path) -> dict:
    """Load and validate a transcript JSON file.

    Expected shape::

        {
          "interview_id": "...",
          "segments": [
            {"id": "s1", "speaker": "maya" | "candidate", "text": "..."},
            ...
          ]
        }
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(data, dict) or "interview_id" not in data:
        raise TranscriptError("transcript must be an object with an interview_id")
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise TranscriptError("transcript must contain a non-empty segments list")

    seen_ids = set()
    for segment in segments:
        if not isinstance(segment, dict):
            raise TranscriptError("each segment must be an object")
        for field in ("id", "speaker", "text"):
            if not isinstance(segment.get(field), str) or not segment[field]:
                raise TranscriptError(f"segment is missing a valid '{field}' field")
        if segment["id"] in seen_ids:
            raise TranscriptError(f"duplicate segment id: {segment['id']}")
        seen_ids.add(segment["id"])

    return data


def load_notes(path: str | Path) -> dict:
    """Load review notes as raw JSON.

    No validation happens here on purpose: notes are generated output and may
    be arbitrarily malformed. The report builder must cope with that.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))
