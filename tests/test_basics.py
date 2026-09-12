"""Sanity tests for the parts of the project that already work.

These PASS against the starter code and must still pass after your fix.
They cover the loaders (supporting infrastructure — not part of what you
need to change) and the CLI plumbing.
"""

import json

import pytest

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
    assert len(notes["notes"]) == 7


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


# --- Loader guarantees (CONTRACT.md "What you may assume") --------------------


def write_json(tmp_path, data):
    path = tmp_path / "doc.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_transcript_doc(**overrides):
    doc = {
        "interview_id": "t1",
        "segments": [{"id": "s1", "speaker": "maya", "text": "Hello."}],
    }
    doc.update(overrides)
    return doc


def test_transcript_rejects_unknown_speaker(tmp_path):
    doc = make_transcript_doc(
        segments=[{"id": "s1", "speaker": "system", "text": "Hello."}]
    )
    with pytest.raises(loader.TranscriptError):
        loader.load_transcript(write_json(tmp_path, doc))


@pytest.mark.parametrize("bad_id", [None, "", 7])
def test_transcript_rejects_invalid_interview_id(tmp_path, bad_id):
    doc = make_transcript_doc(interview_id=bad_id)
    with pytest.raises(loader.TranscriptError):
        loader.load_transcript(write_json(tmp_path, doc))


def test_transcript_rejects_duplicate_segment_ids(tmp_path):
    doc = make_transcript_doc(
        segments=[
            {"id": "s1", "speaker": "maya", "text": "Hello."},
            {"id": "s1", "speaker": "candidate", "text": "Hi."},
        ]
    )
    with pytest.raises(loader.TranscriptError):
        loader.load_transcript(write_json(tmp_path, doc))


@pytest.mark.parametrize("doc", [[], {}, {"notes": "not-a-list"}])
def test_notes_must_be_an_object_with_a_notes_list(tmp_path, doc):
    with pytest.raises(loader.NotesError):
        loader.load_notes(write_json(tmp_path, doc))


@pytest.mark.parametrize(
    "note", ["not-an-object", {"note_id": "a"}, {"note_id": "a", "claim": 5}]
)
def test_notes_require_a_string_claim(tmp_path, note):
    with pytest.raises(loader.NotesError):
        loader.load_notes(write_json(tmp_path, {"notes": [note]}))


def test_note_id_must_be_a_string_when_present(tmp_path):
    with pytest.raises(loader.NotesError):
        loader.load_notes(write_json(tmp_path, {"notes": [{"note_id": 7, "claim": "x"}]}))


def test_notes_evidence_is_deliberately_not_validated(tmp_path):
    """Anything inside `evidence` is the report builder's problem, not the
    loader's — that is the published grading boundary."""
    doc = {
        "notes": [
            {"claim": "no evidence at all"},
            {"claim": "garbage evidence", "evidence": "not-a-list"},
            {"claim": "null note_id is fine", "note_id": None, "evidence": None},
        ]
    }
    loaded = loader.load_notes(write_json(tmp_path, doc))
    assert len(loaded["notes"]) == 3
