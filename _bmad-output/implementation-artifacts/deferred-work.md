- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/1-project-skeleton-environment-settings-and-test-harness.md`
  summary: Add HTTPS hardening for non-local environments (SECURE_SSL_REDIRECT, HSTS, SECURE_PROXY_SSL_HEADER, a guard against ALLOWED_HOSTS=*), to be settled with the host for the Hosted instance.
  evidence: Story 1 sets only the AD-14 guards; a Hosted instance behind a TLS proxy needs these, and the right values depend on the host chosen in architecture OQ-3 (story 18).

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/3-shell-courses-and-a-basic-home.md`
  summary: Story 3b — Topics and Sources (models with student FK and cascade), Fagoversikt P04 with «Nytt tema» (D03), a basic Topic page listing Sources, rename/delete for Topics and Sources with D09 naming what goes, and the Course delete dialog counting Topics and Sources.
  evidence: Split from story 3 at the Author's choice (2026-11-15) because shell + Courses + Topics + Sources in one spec would be ~3000 tokens; 3b builds on 3a's shell and dialog pattern and must land before story 4.

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/3-shell-courses-and-a-basic-home.md`
  summary: Add a browser test harness (e.g. Playwright, run Key-free) covering app.js — dialog opens on swap into #dialog, Esc/Avbryt empties the slot and returns focus, failure messages show.
  evidence: The only check of app.js is a source-text regex; deleting `showModal()` would leave every dialog invisible with JS on and no test would fail.

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/3b-topics-and-sources.md`
  summary: Story 4 must fit upload file names into `Source.name` (≤ 80 chars) — shorten keeping the extension, or reject with a named message.
  evidence: `Source.name` reuses NAME_MAX_LENGTH = 80; SQLite would store longer names silently and D08 would then pre-fill a value its own form refuses.

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/4-upload-and-text-extraction-with-location.md`
  summary: Run the OQ-1 extraction test on three real slide decks (pypdf 7.0.1 plain and layout mode vs pdfplumber; Æ/Ø/Å, bullet lists, a table or two-column slide) and confirm or change the plain mode and `MIN_TEXT_CHARS` = 200 in `ingestion/extract.py` and `docs/quality/oq1-pdf-extraction.md`.
  evidence: Story 4 started without slide decks, so the Author chose provisional values (docs/quality/oq1-pdf-extraction.md, 2026-11-15); the tests only use Helvetica PDFs built with pypdf's writer.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/4-upload-and-text-extraction-with-location.md`
  summary: Cap the request body size before Django reads a whole upload (the 10 MB check runs after it is received).
  evidence: `_from_upload` checks `upload.size` only after the body is spooled to disk; set a server/proxy limit or `DATA_UPLOAD_MAX_MEMORY_SIZE`-style guard with the Hosted setup (OQ-3).
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/4-upload-and-text-extraction-with-location.md`
  summary: Bound pypdf extraction work per upload (decompression bomb or pathological content streams). Unverified; medium if true.
  evidence: Extraction runs in the request with no timeout; settle by timing a crafted 10 MB PDF with a highly compressed stream.
