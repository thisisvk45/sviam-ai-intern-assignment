"""Load transcript and review-note fixtures from disk.

The transcript is trusted input produced by our own recording pipeline, so it
is validated strictly here.

Review notes are *model output*. The loader enforces only the STRUCTURAL
guarantees published in CONTRACT.md ("What you may assume"): the document is
an object with a `notes` list, every note is an object with a string `claim`,
and `note_id` is a string when present. Everything else — especially the
`evidence` field — is left untouched and untrusted: deciding how to handle
malformed or misleading evidence is the report builder's job.
"""

from __future__ import annotations

import json
from pathlib import Path

ALLOWED_SPEAKERS = ("maya", "candidate")


class TranscriptError(ValueError):
    """Raised when a transcript file does not match the expected shape."""


class NotesError(ValueError):
    """Raised when a notes document violates the structural guarantees."""


def load_transcript(path: str | Path) -> dict:
    """Load and validate a transcript JSON file.

    Expected shape::

        {
          "interview_id": "...",          # non-empty string
          "segments": [
            {"id": "s1", "speaker": "maya" | "candidate", "text": "..."},
            ...
          ]
        }
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise TranscriptError("transcript must be a JSON object")
    interview_id = data.get("interview_id")
    if not isinstance(interview_id, str) or not interview_id:
        raise TranscriptError("transcript must have a non-empty string interview_id")
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
        if segment["speaker"] not in ALLOWED_SPEAKERS:
            raise TranscriptError(
                f"segment {segment['id']}: speaker must be one of "
                f"{ALLOWED_SPEAKERS}, got {segment['speaker']!r}"
            )
        if segment["id"] in seen_ids:
            raise TranscriptError(f"duplicate segment id: {segment['id']}")
        seen_ids.add(segment["id"])

    return data


def load_notes(path: str | Path) -> dict:
    """Load review notes, enforcing only the published structural guarantees.

    Guaranteed after this call (see CONTRACT.md "What you may assume"):

    - the document is an object containing a ``notes`` list;
    - every note is an object with a string ``claim``;
    - ``note_id``, when present and non-null, is a string.

    Deliberately NOT validated: ``evidence`` and every other field. Those are
    untrusted model output, and handling them is the report builder's job.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(data, dict) or not isinstance(data.get("notes"), list):
        raise NotesError("notes document must be an object containing a 'notes' list")
    for position, note in enumerate(data["notes"]):
        if not isinstance(note, dict):
            raise NotesError(f"note at index {position} must be an object")
        if not isinstance(note.get("claim"), str):
            raise NotesError(f"note at index {position} must have a string 'claim'")
        note_id = note.get("note_id")
        if note_id is not None and not isinstance(note_id, str):
            raise NotesError(
                f"note at index {position}: 'note_id' must be a string when present"
            )

    return data
