"""Sanity tests for the parts of the project that already work.

These PASS against the starter code and must still pass after your fix.
"""

import json

from maya_review import loader
from maya_review.cli import main
from maya_review.mock_model import RecordedReviewModel

from conftest import FIXTURES


def test_transcript_loads(transcript):
    assert transcript["interview_id"] == "int_2026_0142"
    ids = [segment["id"] for segment in transcript["segments"]]
    assert len(ids) == 7
    assert len(set(ids)) == 7


def test_notes_load(notes):
    assert len(notes["notes"]) == 6


def test_mock_model_is_deterministic(transcript, notes):
    model = RecordedReviewModel(FIXTURES / "review_notes.json")
    assert model.generate(transcript) == notes
    assert model.generate(transcript) == model.generate(transcript)


def test_cli_runs(capsys):
    exit_code = main(
        [str(FIXTURES / "transcript.json"), str(FIXTURES / "review_notes.json")]
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "int_2026_0142" in out


def test_cli_json_output_parses(capsys):
    exit_code = main(
        [
            str(FIXTURES / "transcript.json"),
            str(FIXTURES / "review_notes.json"),
            "--json",
        ]
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    report = json.loads(out)
    assert report["interview_id"] == "int_2026_0142"
