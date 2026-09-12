"""A deterministic stand-in for the LLM review step.

In production, Maya's pipeline sends the interview transcript to an LLM and
gets review notes back. For this assignment the model's response has been
recorded to a JSON file and is replayed verbatim, so the whole project runs
offline, deterministically, and without any API key.

The recorded output is intentionally imperfect — hallucinated claims, broken
citations, misattributed quotes. That is the point of the assignment: the
report builder must not blindly trust what this "model" produces.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


class RecordedReviewModel:
    """Replays a recorded model response for a specific interview."""

    def __init__(self, recorded_output_path: str | Path):
        self._recorded = json.loads(
            Path(recorded_output_path).read_text(encoding="utf-8")
        )

    def generate(self, transcript: dict) -> dict:
        """Return the recorded review notes for the given transcript.

        Raises ValueError if the recording belongs to a different interview,
        which would make the replay meaningless.
        """
        recorded_id = self._recorded.get("interview_id")
        if transcript.get("interview_id") != recorded_id:
            raise ValueError(
                f"recorded output is for interview {recorded_id!r}, "
                f"not {transcript.get('interview_id')!r}"
            )
        return deepcopy(self._recorded)
