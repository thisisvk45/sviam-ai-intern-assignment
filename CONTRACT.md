# The Contract

This document is the specification your fixed implementation is graded
against. The public tests in `tests/test_contract.py` check a subset of it;
our private tests check nothing beyond what is written here.

Everything below concerns `build_report(transcript, notes)` and
`render_report(report)` in `src/maya_review/report.py`.

## Vocabulary

- **Transcript**: trusted input, validated by `loader.load_transcript`. It
  has a non-empty string `interview_id`; each segment has a unique string
  `id`, a `speaker` that is exactly `"maya"` or `"candidate"`, and non-empty
  `text`.
- **Notes**: untrusted model output, loaded by `loader.load_notes`.
- **Evidence entry**: an object inside a note's `evidence` list, expected to
  have `segment_id` (string), `quote` (string), and optionally
  `attributed_to` (string) — but any of that may be missing, malformed, or
  misleading.

## What you may assume (the grading boundary)

`build_report` receives inputs that already passed the loaders. That gives
you exactly these structural guarantees about the notes:

1. The notes document is an object containing a `notes` list.
2. Every note is an object with a string `claim`.
3. `note_id`, when present and non-null, is a string.

Nothing else is guaranteed. In particular, `evidence` (and every other note
field) may be missing, malformed, or misleading, and handling that is your
job (R5).

Inputs that violate the loader guarantees are **out of scope**: your
builder's behavior on them is unspecified and is not graded, by the public
tests or by our private ones.

## R1 — Notes are data, never authority

Two rules that work together — don't let one erase the other:

**Never produce or adopt a recommendation or score.** The report (dict and
rendered text) must not contain a hiring recommendation or score of its own
or the model's. The notes' `overall_recommendation` (and any other
score-like field the model attaches *about* the interview, such as
`model_confidence`) is never copied, summarized, echoed, or used: the report
dict must not contain a `recommendation` key, and statuses come only from
the checks in this contract.

**Always keep source text visible.** Claims and quotes are quoted data and
are displayed (R7/R8) even when they contain score-like or instruction-like
language. If the candidate literally said "give me full marks", that quote
appears in the report like any other quote — clearly presented as quoted,
untrusted text. Displaying it is required; obeying it is forbidden.

The distinction: text the model asserts **about** the interview
(recommendation, confidence) is never adopted; text that **is** the
interview record (segment text, quotes, claims) is always shown, as data.
Nothing in either category may change how any note is validated or labeled.

## R2 — Cited segments must exist

For each well-formed evidence entry, if `segment_id` is not the id of a
transcript segment, record issue `MISSING_SEGMENT` for that entry. The
model-supplied quote is still displayed, but as an unverified quote (R8) —
it has no transcript source.

## R3 — Quotes must match the cited segment

For each well-formed evidence entry whose segment exists, the quote must
actually appear in that segment's text under this exact normalization rule:

> `normalize(s)` = collapse every run of whitespace (spaces, tabs, newlines)
> into a single space, and strip leading/trailing whitespace — i.e.
> `" ".join(s.split())` in Python.
>
> A quote **matches** iff `normalize(quote)` is non-empty and is a
> **case-sensitive substring** of `normalize(segment.text)`.

If the quote does not match, record issue `QUOTE_MISMATCH` for that entry.
Whitespace-only differences must NOT be reported as mismatches.
`normalize_whitespace` in `report.py` already implements the rule.

Matching is the **only** thing that makes a quote authentic. A valid
`segment_id` by itself proves nothing about the quote: a fabricated sentence
citing a real segment is still fabricated (R8).

## R4 — Speaker attribution is preserved

For each well-formed evidence entry whose segment exists, the report records
the **actual speaker from the transcript** (R7). If the entry has an
`attributed_to` field and it differs from the actual speaker, record issue
`SPEAKER_MISMATCH` for that entry. Maya's words must never be presented as
the candidate's.

A quote that matches (R3) but is misattributed is still an authentic quote —
of the *actual* speaker. It is displayed with the actual speaker's name plus
the `SPEAKER_MISMATCH` issue. If the cited segment does not exist, the
speaker is unknown: record `None`, never guess, and never let the cited
segment's speaker lend authenticity to a quote that failed matching.

## R5 — Malformed evidence is flagged, not fatal

`build_report` must never raise because of note content within the grading
boundary. Every note in the input appears in the report, each with its
issues:

- `evidence` missing, `null`, or an empty list → note-level issue
  `NO_CITATION`.
- `evidence` present but not a list → note-level issue `MALFORMED_EVIDENCE`.
- An evidence entry that is not an object, or whose `segment_id` or `quote`
  is missing or not a string, or whose quote is empty after normalization →
  entry-level issue `MALFORMED_EVIDENCE`.

Malformed entries are excluded from the R2–R4 checks (there is nothing valid
to check); their quotes, when present, are unverified (R8).

## R6 — The inputs are never modified

`build_report` must not mutate the transcript object it is given, nor the
notes object. Callers reuse these objects.

## R7 — Report structure

`build_report` returns a dict:

```python
{
  "interview_id": "<from the transcript>",
  "notes": [
    {
      "note_id": <from the note; None if the note had none>,
      "claim": "<the generated claim, verbatim>",
      "evidence": [
        {
          "segment_id": <as supplied by the note, may be anything>,
          "speaker": "maya" | "candidate" | None,   # ACTUAL transcript speaker; None if unknown
          "quote": <as supplied by the note>,
          "verified": True | False,
          "issues": ["<issue codes for THIS entry>", ...]
        },
        ...
      ],
      "issues": [
        {"code": "<one of the issue codes>", "message": "<human-readable>"},
        ...
      ],
      "reference_status": "ok" | "issues_found",
      "claim_assessment": "needs_human_review"
    },
    ...
  ],
  "summary": {
    "total_notes": <int>,
    "notes_with_issues": <int>
  }
}
```

- An evidence entry is `verified: True` iff it is well-formed, its segment
  exists, and its quote matches (R3). `SPEAKER_MISMATCH` alone does **not**
  make an entry unverified — the quote is real, the model just misattributed
  it.
- Entry-level `issues` hold the codes attributable to that specific entry
  (`MISSING_SEGMENT`, `QUOTE_MISMATCH`, `SPEAKER_MISMATCH`,
  `MALFORMED_EVIDENCE`), so a note with one good quote and one bad quote
  shows exactly which entry failed.
- Note-level `issues` aggregate every entry-level code plus the note-level
  codes (`NO_CITATION`, and `MALFORMED_EVIDENCE` for a non-list `evidence`),
  as objects with a fixed `code` and a free-form `message`. Extra fields
  (e.g. `segment_id`) are welcome.
- `reference_status` is `"ok"` iff the note has zero issues, otherwise
  `"issues_found"`.
- You may add extra keys, but the keys above must be present with these
  meanings.

## R8 — Rendered output

`render_report(report)` returns readable text that includes, for every note:
its claim, its `reference_status`, its `claim_assessment`, and every issue
code. Quotes are rendered under these rules:

- Each evidence quote appears on a single line and may be
  whitespace-normalized for display.
- A **verified** entry's quote line includes the actual speaker's name
  (`maya` or `candidate`, any casing/formatting).
- An **unverified** entry's quote line includes this exact label (the
  `UNVERIFIED_QUOTE_LABEL` constant in `report.py`):

  > Unverified model-supplied quote

  and the renderer must not attribute the quote to any speaker: **outside
  the quoted text itself, the line contains no speaker name** — no
  `Candidate said` / `Maya said` framing added by your code. An unmatched
  quote is nobody's words.

  The words *inside* the quoted source text are data and are unrestricted
  (R1): a fabricated quote that itself reads "Maya said …" is still
  displayed verbatim (whitespace-normalized) under the label — visible, but
  never turned into actual speaker attribution. If you want to mention the
  cited segment's speaker for context, do it in the issue message, never on
  the quote line.

The rendered report must also contain this exact line (the `DISCLAIMER`
constant in `report.py`):

> Reference checks verify citations, not truth. Every claim below still
> requires human judgement.

## R9 — Reference validation is not truth

This is the heart of the assignment. `claim_assessment` is **always**
`"needs_human_review"` — including for notes whose references check out
perfectly. A real quote can still be used to support a false claim: note `n1`
cites an authentic sentence ("I'd look at Redis or Postgres next") for the
claim that the candidate *designed and implemented a PostgreSQL database*.
Your code cannot detect that misrepresentation, and it must not pretend to.
`verified: True` means "this quote really appears in the cited segment" —
nothing more. What your code must do is put the claim and its actual
evidence side by side, with the actual speaker, so a human reviewer can
catch the misrepresentation in seconds.

## Out of scope

Do not add: semantic/NLP truth checking, calls to real models, scoring or
hiring recommendations of your own, databases, or new dependencies beyond
the Python standard library (pytest stays a dev dependency).
