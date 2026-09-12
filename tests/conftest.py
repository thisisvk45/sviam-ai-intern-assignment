import pathlib

import pytest

from maya_review import loader

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "fixtures"
TEST_FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def transcript():
    return loader.load_transcript(FIXTURES / "transcript.json")


@pytest.fixture
def notes():
    return loader.load_notes(FIXTURES / "review_notes.json")


@pytest.fixture
def malformed_notes():
    return loader.load_notes(TEST_FIXTURES / "malformed_notes.json")
