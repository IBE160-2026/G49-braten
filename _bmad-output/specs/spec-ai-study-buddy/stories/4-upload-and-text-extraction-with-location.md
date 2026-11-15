---
title: 'Upload and text extraction with Location'
type: 'feature'
created: '2026-11-15'
status: 'done'
baseline_commit: '37ff412f9b4bb26a681ee854437847e330c792ef'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/docs/quality/oq1-pdf-extraction.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Topic cannot get a Source: there is no upload, no limit check and no stored text, so nothing later can generate or check References against a Location (CAP-3, FR-3, FR-4).

**Approach:** Add D05 «Legg til kilde» (in `studymat`) with a file or pasted text plus a Detail level, and `ingestion.services.ingest()` that validates, extracts text into `SourceText` rows per Location and creates the Source as `pending` (AD-5 step 1). The file itself is never kept.

## Boundaries & Constraints

**Always:**
- `ingestion.SourceText(student, source, kind, index, label, text)`: `kind` ∈ `page/paragraph/heading`, `index` from 1, unique per (source, kind, index), CASCADE from Source, `student` set from the Source (AD-7). Created in one transaction with the Source; a rejection keeps nothing.
- PDF via pypdf 7.0.1 plain `extract_text()`: one `page` row per viewer page, empty pages included; images skipped. Rejected as scanned when total non-whitespace characters < `MIN_TEXT_CHARS` = 200. Encrypted or unreadable PDFs are rejected, never a 500.
- `.txt` and pasted text: UTF-8 (BOM stripped), falling back to cp1252; line endings normalised; one `paragraph` row per block separated by blank lines.
- Limits as module constants in `ingestion`: 10 MB file, 50 pages, 150,000 extracted characters (every kind). Checked before any row is saved. Type by extension and content: PDF must start with `%PDF-`.
- Rejection messages in bokmål from `core/messages.py`, naming the limit: «Filen har 70 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.»; size «Filen er 12,4 MB. Grensen er 10 MB.»; characters «Teksten har 180 000 tegn. Grensen er 150 000 tegn.»; scanned «Fant ingen tekst i PDF-en. Skannede dokumenter støttes ikke.»; type «Bare PDF og tekstfiler (.txt) støttes.»; empty paste «Lim inn tekst først.». Shown in the upload-panel with «Velg en annen fil».
- `content_sha256` of the file bytes, or of UTF-8 for pasted text. Source `name` = file name, shortened to ≤ 80 characters keeping the extension (middle replaced by «…»). Pasted text has an optional name field, default «Innlimt tekst».
- D05: GET `/topics/<id>/sources/new/`, AD-13/AD-18 dialog mechanics as 3a/3b, `multipart/form-data`, «Velg fil», «Lim inn tekst» (a textarea, works without JS), limits shown up front «PDF eller tekstfil · maks 50 sider eller 10 MB», Detail level segmented-control «Kortfattet / Middels / Detaljert» default «Middels» with «Gjelder sammendraget. Du kan bytte detaljnivå senere.», «Last opp». Both file and text given → error «Velg enten en fil eller tekst.». Valid → `HX-Location` to the Topic's P05, Source listed as pending.
- P05 gets «Legg til kilde» (secondary) above the list; the empty-state gains the same action. Another Student's Topic → P12.

**Never:**
- Generation, `claimable`, `effective_status`, `Source.language` (story 6); D04 privacy notice (story 10); daily limit, Mock-mode message, Sample document (story 5); Word (FR-5); drag-and-drop zone and browser-side size check (JS niceties, later); keeping the uploaded file; OCR.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PDF | 3-page PDF, page 2 image-only, «Detaljert» | Source pdf/pending/detailed, size and sha256 set; 3 page rows, row 2 empty | N/A |
| Text file | `.txt` with 3 blank-line-separated blocks | 3 paragraph rows, kind text | N/A |
| Pasted | text, no name | Source «Innlimt tekst», kind pasted | N/A |
| cp1252 | `.txt` «Æøå» in cp1252 | stored as «Æøå» | N/A |
| Too many pages | 51-page PDF | D05 with page message; nothing saved | 200 |
| Too large | 10 MB + 1 byte | size message; nothing saved | 200 |
| Too many chars | 150,001 characters | character message; nothing saved | 200 |
| Scanned | PDF with < 200 chars | scanned message; nothing saved | 200 |
| Wrong type | `.docx`, or `.pdf` not starting `%PDF-` | type message | 200 |
| Broken PDF | truncated or encrypted | type/unreadable message, no 500 | 200 |
| Neither / both | no file and blank text / file plus text | matching field error | 200 |
| Long name | 120-char file name | name ≤ 80, ends `.pdf` | N/A |
| Other's tema | D05 GET/POST on B's Topic | P12, nothing saved | 404 |

</frozen-after-approval>

## Code Map

- `courses/services.py` `create_source` -- reuse as is; ingestion calls it inside its transaction.
- `courses/models.py` `Source`, `DetailLevel`, `SourceKind`, `NAME_MAX_LENGTH` -- reuse; no change.
- `core/http.py` (`render_page`, `redirect_after_submit`, `vary_on_htmx`), `core/ownership.py` `get_owned_or_404`, `courses/forms.py` `FocusFirstErrorMixin`, `accounts/forms.py` `LinkedErrorsMixin` -- dialog and form mechanics to reuse.
- `templates/courses/create.html` -- dialog template pattern for D05; `templates/components/dialog.html`, `text_input.html`, `inline_message.html`.
- `templates/web/topic.html` -- placeholder comment «Story 4 adds «Legg til kilde»»; add the action. `templates/components/source_row.html` already renders pending.
- `templates/components/` -- add `segmented_control.html` if none exists (D01 theme has one in `account_menu.html`; reuse its CSS).
- `tests/test_import_graph.py` -- allowed edges `studymat → ingestion, ai`, `ingestion → courses`; `studymat` views must not import `courses.views`.
- `pyproject.toml` -- add `pypdf==7.0.1`; `uv.lock`.
- `tests/test_topics_sources.py` -- fixtures for student, course, topic.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- add pypdf 7.0.1
- [x] `ingestion/models.py`, `ingestion/migrations/0001_initial.py` -- `SourceText`
- [x] `ingestion/extract.py` -- pure functions: PDF pages, text paragraphs, decoding, name shortening; limits and `MIN_TEXT_CHARS` as constants
- [x] `ingestion/services.py` -- `ingest(topic, *, upload=None, text="", name="", detail_level)` raising `IngestError(code, **params)`; one transaction
- [x] `core/messages.py` -- rejection and D05 texts
- [x] `studymat/forms.py`, `studymat/views.py`, `studymat/urls.py`, `config/urls.py`, `templates/studymat/add_source.html` -- D05
- [x] `templates/web/topic.html`, `static/css/components.css` -- «Legg til kilde», upload-panel at 360/1280 px, light and dark
- [x] `tests/test_ingestion.py`, `tests/test_upload.py` -- every matrix row, with PDFs built in the test (pypdf writer, no binary fixtures in git), `student` equals parent on SourceText, cascade on Source delete, HTMX partial and `Vary`, CSRF, signed-out redirect

**Acceptance Criteria:**
- Given JavaScript off, when the Student uploads a PDF and pastes text, then both work as full pages and land on P05.
- Given any rejection, then `Source` and `SourceText` row counts are unchanged.
- Given `uv run pytest` offline, then everything passes, including the import-graph test.

## Implementation Notes

- `SourceText.label` is the Location's number as text («3»); templates add «Side»/«Avsnitt». No Norwegian is stored. `heading` is defined but unused until Word (FR-5).
- `IngestError` lives in `ingestion/errors.py` (re-exported by `ingestion.services`) and formats its numbers: counts with a space as thousands separator, sizes in MiB (1024²) rounded *up* to one decimal with a comma, so 10 MB + 1 byte reads «10,1 MB».
- Codes not named by the spec, added to `core/messages.py`: `unreadable_pdf` (encrypted/broken PDF, also any page whose extraction raises), `empty_file` (a `.txt` with no text, or an empty upload), `detail_level_required`, `pasted_name_too_long`, `pasted_default_name`.
- A `.txt` starting with a UTF-16 BOM is decoded as UTF-16; otherwise one containing NUL bytes, or bytes neither UTF-8 nor cp1252, is refused as the wrong type. A PDF with only an owner password (empty user password) is opened with `decrypt("")`; lone surrogates from pypdf become U+FFFD before saving. Pasted text is stored with `size_bytes = 0`; its sha256 is of the newline-normalised text.
- The character limit counts the stored text (sum over rows), so blank-line separators between paragraphs are not counted.
- The rejection is shown as an inline-message (`#upload-error`) at the top of the upload-panel with «Velg en annen fil» as a `<label for="id_file">` (works without JS) when the rejection is about the file; the offending input gets `aria-invalid` and `autofocus`, and the dialog title then does not take focus (`dialog.html` gained `error` and `enctype`).
- P05: «Legg til kilde» (secondary) sits in the section head when there are Sources; with none, the empty-state carries it as its one action.

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap). No intent_gap or bad_spec; patches sent to the implementation agent; two defers.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Owner-password-only PDF refused as unreadable (BH, ECH) | medium | patch | `is_encrypted` refused without `decrypt("")`; common for lecture decks |
| UTF-16 `.txt` refused as wrong type (BH, ECH) | medium | patch | NUL check runs before any BOM check |
| Lone surrogates from pypdf reach the DB write (ECH) | low | patch | UnicodeEncodeError would be a 500; one-line replace |
| `except Exception` logs without the exception (BH) | low | patch | A pypdf API change would be invisible |
| «Velg en annen fil» shown on a paste rejection (BH, ECH) | low | patch | Template always renders it; the test locked it in |
| NUL in pasted text gives Django's English message (ECH) | low | patch | ProhibitNullCharactersValidator default text |
| Detail level help/error not linked by aria-describedby (BH) | low | patch | Fieldset has no describedby |
| Invisible BOM literal in `lstrip` (BH) | low | patch | Editors can strip it silently |
| OQ-1 deferred entry not in the file's format (BH) | low | patch | Other entries use source_spec/summary/evidence |
| Name > 80, 0-byte upload, `reject()` target, MIN_TEXT_CHARS boundary, PDF char limit untested (VG, BH) | low | patch | Cheap tests for documented behaviour |
| No request-size cap before the 10 MB check (BH) | medium | defer | Whole body is received first; belongs with hosting hardening (OQ-3) |
| PDF decompression bomb / slow extract in the request (BH, ECH) | maybe-false (medium if true) | defer | Needs a crafted PDF to measure pypdf's cost |
| Paste over 2.5 MB gives 400 (BH, ECH) | low | reject | 17× the character limit; fix adds a setting and a branch |
| `.txt` with one paragraph per line becomes one Location (BH) | low | reject | Spec fixes blank-line blocks; changing it edits the spec |
| `%PDF-` must be at byte 0 (BH) | low | reject | Spec wording; changing it edits the spec |
| Name typed together with a file is ignored (ECH) | low | reject | Help text says «Gjelder bare innlimt tekst.» |
| 150 000 one-character paragraphs make 150 000 rows (ECH) | low | reject | Local single-user app; adds a limit |
| Double submit without JS gives two Sources (ECH) | low | reject | Same as 3a: JS-off path only, fix needs a nonce |
| `uv.lock` missing from the diff (BH) | false | reject | Excluded from the review diff only; the file is modified in the tree |

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes
