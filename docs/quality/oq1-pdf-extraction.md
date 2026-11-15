# OQ-1: PDF extraction (provisional)

Status: **provisional** — decided 2026-11-15 without the planned test.

The architecture (OQ-1) asked for an extraction test on three of the Author's own slide decks: pypdf 7.0.1 in plain and layout mode against pdfplumber. No slide decks were available when story 4 started, and the Author chose to continue without the test.

## Decision

| Setting | Value | Why |
|---|---|---|
| Library | pypdf 7.0.1 (already in the Stack) | Pure Python, no system dependencies, one row per page as AD-6 needs |
| Mode | plain (`extract_text()`) | Layout mode pads with spaces for column alignment, which bloats prompts and breaks quote matching |
| `MIN_TEXT_CHARS` | 200 (total, after stripping whitespace) | A scanned deck gives near zero; a text deck of a few slides gives well over 200 |

All three are constants in `ingestion`, so changing them later needs no architecture change (spine: "Tuning the starting values").

## Still open

Run the comparison on three real decks (Æ/Ø/Å, bullet lists, a table or two-column slide) and confirm or change the values above. Tracked in `_bmad-output/implementation-artifacts/deferred-work.md`.
