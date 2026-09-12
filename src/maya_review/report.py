"""Report builder: turns a transcript + generated review notes into a reviewer report.

*** KNOWN-BROKEN STARTER CODE ***

This module is the part of the assignment you are expected to fix. It
currently trusts the generated notes completely: it never checks that cited
segments exist, never compares quotes against the transcript, presents every
quote as the candidate's words, copies the model's self-declared confidence
into the report status, and copies the model's hiring recommendation straight
into the report header. It also mutates the transcript it was given, and it
crashes on malformed notes.

CONTRACT.md at the repository root defines the behavior this module is
supposed to have. The constants below are part of that contract; the starter
defines them but (tellingly) never uses most of them.
"""

from __future__ import annotations

# --- Contract constants (see CONTRACT.md) ----------------------------------

# Issue codes. The fixed implementation must emit these; the starter never does.
MISSING_SEGMENT = "MISSING_SEGMENT"
QUOTE_MISMATCH = "QUOTE_MISMATCH"
SPEAKER_MISMATCH = "SPEAKER_MISMATCH"
MALFORMED_EVIDENCE = "MALFORMED_EVIDENCE"
NO_CITATION = "NO_CITATION"

# Reference-validation statuses for a note.
REFERENCE_OK = "ok"
REFERENCE_ISSUES = "issues_found"

# The only permitted claim assessment. This tool checks references; it can
# never certify that a generated claim is TRUE.
CLAIM_NEEDS_HUMAN_REVIEW = "needs_human_review"

# Rendering label for quotes that could not be verified against the transcript
# (missing segment, quote mismatch, malformed entry). Such a quote is nobody's
# words — it must never be rendered as "Candidate said" or "Maya said".
# See CONTRACT.md R8.
UNVERIFIED_QUOTE_LABEL = "Unverified model-supplied quote"

# This exact line must appear in every rendered report (see CONTRACT.md R8).
DISCLAIMER = (
    "Reference checks verify citations, not truth. "
    "Every claim below still requires human judgement."
)


def normalize_whitespace(text: str) -> str:
    """Collapse every run of whitespace into a single space and strip the ends.

    This is the normalization rule referenced by CONTRACT.md R3.
    """
    return " ".join(text.split())


def build_report(transcript: dict, notes: dict) -> dict:
    """Build a reviewer report from a transcript and generated review notes.

    BROKEN: see the module docstring and CONTRACT.md.
    """
    # Tidy up the transcript text so quotes line up nicely in the output.
    for segment in transcript["segments"]:
        segment["text"] = normalize_whitespace(segment["text"])

    report_notes = []
    for note in notes["notes"]:
        evidence = []
        for entry in note.get("evidence", []):
            evidence.append(
                {
                    "segment_id": entry.get("segment_id"),
                    "speaker": "candidate",
                    "quote": entry["quote"],
                }
            )

        confidence = note.get("model_confidence", "")
        status = "verified" if confidence in ("verified", "high") else "unreviewed"

        report_notes.append(
            {
                "note_id": note.get("note_id"),
                "claim": note.get("claim", ""),
                "status": status,
                "evidence": evidence,
            }
        )

    return {
        "interview_id": transcript["interview_id"],
        "recommendation": notes.get("overall_recommendation"),
        "notes": report_notes,
    }


def render_report(report: dict) -> str:
    """Render a report dict as human-readable text.

    BROKEN: presents every quote as the candidate's words, surfaces the
    model's recommendation, and shows no validation issues.
    """
    lines = [f"# Interview review — {report['interview_id']}", ""]

    if report.get("recommendation"):
        lines.append(f"**Model recommendation:** {report['recommendation']}")
        lines.append("")

    for note in report["notes"]:
        lines.append(f"## {note['note_id']} — {note['claim']}")
        lines.append(f"Status: {note['status']}")
        for entry in note["evidence"]:
            lines.append(
                f'> Candidate said: "{entry["quote"]}" (segment {entry["segment_id"]})'
            )
        lines.append("")

    return "\n".join(lines)
