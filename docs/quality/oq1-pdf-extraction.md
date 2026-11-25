# OQ-1: PDF extraction

Status: **confirmed** 2026-11-25 by the Author, after the test on three of the Author's slide decks (2026-11-23, «Measurements» below). It was provisional from 2026-11-15 to 2026-11-23.

The architecture (OQ-1) asked for an extraction test on three of the Author's own slide decks: pypdf 7.0.1 in plain and layout mode against pdfplumber. No slide decks were available when story 4 started, so the values below were provisional until the test was run on 2026-11-23.

## Decision

| Setting | Value | Why |
|---|---|---|
| Library | pypdf 7.0.1 (already in the Stack) | Pure Python, no system dependencies, one row per page as AD-6 needs |
| Mode | plain (`extract_text()`) | Layout mode pads with spaces for column alignment, which bloats prompts and breaks quote matching |
| `MIN_TEXT_CHARS` | 200 (total, after stripping whitespace) | A scanned deck gives near zero; a text deck of a few slides gives well over 200 |
| `GLYPH_NAME_SHARE_MAX` | 0.5 (added 2026-11-23) | More than half the non-whitespace text in runs of glyph names (`/BW/CT/D2`) means a font with no Unicode map. The upload is refused with `unmapped_font_pdf`. Measured: 89 % on 05-Fordelinger_post.pdf, at most 0.9 % on seven ordinary PDFs |

All four are constants in `ingestion`, so changing them later needs no architecture change (spine: "Tuning the starting values").

## Still open

Nothing. The test confirmed pypdf plain mode and `MIN_TEXT_CHARS` = 200 and added `GLYPH_NAME_SHARE_MAX` for decks whose fonts have no Unicode map. Closes retro action epic-1 item 2.

## Measurements

Measured with `scripts/compare_extraction.py`.

### 2026-11-23 · pypdf 7.0.1 · 3 deck(s)

| File | Method | Pages | Empty pages | Chars | Non-space chars | Æ/Ø/Å | Mojibake | Padded lines | Seconds | App limits |
|---|---|---|---|---|---|---|---|---|---|---|
| Forelesning 10_arbeidsmiljø_video.pdf | pypdf-plain | 28 | 0 | 7252 | 6133 | 108 | 0 | 0 % | 0.08 | ok |
| Forelesning 10_arbeidsmiljø_video.pdf | pypdf-layout | 28 | 0 | 9356 | 6133 | 108 | 0 | 39 % | 0.10 | ok |
| Forelesning 10_arbeidsmiljø_video.pdf | pdfplumber | 28 | 0 | 7109 | 6133 | 108 | 0 | 0 % | 0.34 | ok |
| Forelesning 4_Digitalisering og lokalisering av arbeid_video.pdf | pypdf-plain | 14 | 0 | 5079 | 4333 | 62 | 0 | 0 % | 0.06 | ok |
| Forelesning 4_Digitalisering og lokalisering av arbeid_video.pdf | pypdf-layout | 14 | 0 | 5602 | 4333 | 62 | 0 | 43 % | 0.07 | ok |
| Forelesning 4_Digitalisering og lokalisering av arbeid_video.pdf | pdfplumber | 14 | 0 | 4998 | 4333 | 62 | 0 | 0 % | 0.16 | ok |
| 05-Fordelinger_post.pdf | pypdf-plain | 13 | 0 | 31621 | 28453 | 0 | 0 | 0 % | 0.08 | ok |
| 05-Fordelinger_post.pdf | pypdf-layout | 13 | 0 | 11716775 | 26890 | 0 | 0 | 99 % | 0.11 | over MAX_CHARS (150000) |
| 05-Fordelinger_post.pdf | pdfplumber | 13 | 0 | 20665 | 10920 | 152 | 0 | 0 % | 0.23 | ok |

Empty pages: no text (likely scanned or image-only slides). Mojibake: broken Æ/Ø/Å or replacement characters. Padded lines: lines with 3+ spaces in a row, which bloat the prompt and break verbatim quotes in the Reference check.


Findings (read with `--show-page`, 2026-11-23):

- **The two ordinary lecture decks (Forelesning 10, Forelesning 4):** all three methods give the same non-space text, and Æ/Ø/Å come through unbroken. Layout mode pads 39–43 % of lines. Plain mode is the fastest and pads nothing. This supports **pypdf plain**.
- **05-Fordelinger_post.pdf (a LaTeX deck with Type 3 / bitmap fonts):** none of the methods works. pypdf plain returns glyph names instead of letters (`/BW/CT/D2 /CZ/D9/D1 …`). Only the formulas survive. pdfplumber spaces and scrambles the letters (`D e n k u m u l a t i v e …`) and drops `≤` onto its own line. Layout mode blows up to 11.7 M characters.
- **Gap:** plain mode's glyph-name output is 28 453 non-space characters, so it passes `MIN_TEXT_CHARS` (200), and the app would send unreadable text to the AI. The rule «too little text = scanned» does not catch this kind of deck. Switching library would not help either.
