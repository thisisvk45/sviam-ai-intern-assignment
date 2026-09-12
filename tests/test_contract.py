"""Regression tests for the report-builder contract (CONTRACT.md).

*** EVERY TEST IN THIS FILE FAILS AGAINST THE STARTER CODE. ***
That is intentional: they encode the behavior the starter is missing.
Your job is to make them pass — without editing this file.
"""

import copy

from maya_review.report import (
    CLAIM_NEEDS_HUMAN_REVIEW,
    DISCLAIMER,
    MALFORMED_EVIDENCE,
    MISSING_SEGMENT,
    NO_CITATION,
    QUOTE_MISMATCH,
    REFERENCE_ISSUES,
    REFERENCE_OK,
    SPEAKER_MISMATCH,
    build_report,
    render_report,
)


def get_note(report, note_id):
    for note in report["notes"]:
        if note["note_id"] == note_id:
            return note
    raise AssertionError(f"note {note_id!r} missing from report")


def codes(note):
    return {issue["code"] for issue in note["issues"]}


# --- R2: cited segments must exist -----------------------------------------


def test_missing_segment_is_flagged(transcript, notes):
    report = build_report(transcript, notes)
    n2 = get_note(report, "n2")  # cites s99, which does not exist
    assert MISSING_SEGMENT in codes(n2)
    assert n2["reference_status"] == REFERENCE_ISSUES


# --- R3: quotes must match the cited segment --------------------------------


def test_quote_mismatch_is_flagged(transcript, notes):
    report = build_report(transcript, notes)
    n4 = get_note(report, "n4")  # quote does not appear in s7
    assert QUOTE_MISMATCH in codes(n4)
    assert n4["reference_status"] == REFERENCE_ISSUES


def test_whitespace_only_differences_are_not_mismatches(transcript, notes):
    report = build_report(transcript, notes)
    n6 = get_note(report, "n6")  # quote differs from s2 only in whitespace
    assert n6["issues"] == []
    assert n6["reference_status"] == REFERENCE_OK


# --- R4: speaker attribution -------------------------------------------------


def test_mayas_words_are_not_attributed_to_the_candidate(transcript, notes):
    report = build_report(transcript, notes)
    n3 = get_note(report, "n3")  # quotes Maya's question as the candidate's answer
    assert SPEAKER_MISMATCH in codes(n3)
    assert n3["evidence"][0]["speaker"] == "maya"


# --- R5: malformed notes are flagged, not fatal ------------------------------


def test_uncited_claim_is_flagged(transcript, notes):
    report = build_report(transcript, notes)
    n5 = get_note(report, "n5")  # claim with no evidence at all
    assert NO_CITATION in codes(n5)


def test_malformed_notes_do_not_crash_the_report(transcript, malformed_notes):
    report = build_report(transcript, malformed_notes)  # must not raise
    assert len(report["notes"]) == 3
    for note_id in ("m1", "m2", "m3"):
        assert MALFORMED_EVIDENCE in codes(get_note(report, note_id))


# --- R6: transcript is never modified ----------------------------------------


def test_transcript_is_not_mutated(transcript, notes):
    before = copy.deepcopy(transcript)
    build_report(transcript, notes)
    assert transcript == before


# --- R1: notes are data, never authority --------------------------------------


def test_no_recommendation_or_score_in_report(transcript, notes):
    report = build_report(transcript, notes)
    assert "recommendation" not in report
    rendered = render_report(report)
    assert "Strong hire" not in rendered
    assert "9/10" not in rendered


def test_model_confidence_does_not_set_status(transcript, notes):
    report = build_report(transcript, notes)
    # n2 declares model_confidence "high" but cites a nonexistent segment.
    n2 = get_note(report, "n2")
    assert n2["reference_status"] == REFERENCE_ISSUES
    # n1 declares itself "verified"; no note may ever be certified as true.
    n1 = get_note(report, "n1")
    assert n1["claim_assessment"] == CLAIM_NEEDS_HUMAN_REVIEW


# --- R9: reference validation is not truth ------------------------------------


def test_authentic_quote_does_not_certify_the_claim(transcript, notes):
    """n1 cites a real sentence, but the claim misrepresents it.

    The references check out (the quote is authentic), yet the claim — that
    the candidate designed and implemented a PostgreSQL database — is not
    supported. The report must keep the claim visible for human review, not
    certify it.
    """
    report = build_report(transcript, notes)
    n1 = get_note(report, "n1")
    assert n1["reference_status"] == REFERENCE_OK
    assert n1["claim_assessment"] == CLAIM_NEEDS_HUMAN_REVIEW


# --- R7 / R8: structure and rendering ------------------------------------------


def test_summary_counts(transcript, notes):
    report = build_report(transcript, notes)
    assert report["summary"]["total_notes"] == 6
    # n2, n3, n4, n5 have issues; n1 and n6 do not.
    assert report["summary"]["notes_with_issues"] == 4


def test_rendered_report_carries_the_disclaimer(transcript, notes):
    rendered = render_report(build_report(transcript, notes))
    assert DISCLAIMER in rendered
