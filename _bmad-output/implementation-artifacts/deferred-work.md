- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/1-project-skeleton-environment-settings-and-test-harness.md`
  summary: Add HTTPS hardening for non-local environments (SECURE_SSL_REDIRECT, HSTS, SECURE_PROXY_SSL_HEADER, a guard against ALLOWED_HOSTS=*), to be settled with the host for the Hosted instance.
  evidence: Story 1 sets only the AD-14 guards; a Hosted instance behind a TLS proxy needs these, and the right values depend on the host chosen in architecture OQ-3 (story 18).

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/3-shell-courses-and-a-basic-home.md`
  summary: Story 3b — Topics and Sources (models with student FK and cascade), Fagoversikt P04 with «Nytt tema» (D03), a basic Topic page listing Sources, rename/delete for Topics and Sources with D09 naming what goes, and the Course delete dialog counting Topics and Sources.
  evidence: Split from story 3 at the Author's choice (2026-11-15) because shell + Courses + Topics + Sources in one spec would be ~3000 tokens; 3b builds on 3a's shell and dialog pattern and must land before story 4.

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/3-shell-courses-and-a-basic-home.md`
  summary: Add a browser test harness (e.g. Playwright, run Key-free) covering app.js — dialog opens on swap into #dialog, Esc/Avbryt empties the slot and returns focus, failure messages show.
  evidence: The only check of app.js is a source-text regex; deleting `showModal()` would leave every dialog invisible with JS on and no test would fail.
  resolved: 2026-11-25. Retro action E1-1: Playwright browser tests in `tests/browser/` (opt-in, `uv run pytest -m browser`); see spec-retro-e1-1-browser-test-harness.md.

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/3b-topics-and-sources.md`
  summary: Story 4 must fit upload file names into `Source.name` (≤ 80 chars) — shorten keeping the extension, or reject with a named message.
  evidence: `Source.name` reuses NAME_MAX_LENGTH = 80; SQLite would store longer names silently and D08 would then pre-fill a value its own form refuses.

- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/4-upload-and-text-extraction-with-location.md`
  summary: Run the OQ-1 extraction test on three real slide decks (pypdf 7.0.1 plain and layout mode vs pdfplumber; Æ/Ø/Å, bullet lists, a table or two-column slide) and confirm or change the plain mode and `MIN_TEXT_CHARS` = 200 in `ingestion/extract.py` and `docs/quality/oq1-pdf-extraction.md`.
  evidence: Story 4 started without slide decks, so the Author chose provisional values (docs/quality/oq1-pdf-extraction.md, 2026-11-15); the tests only use Helvetica PDFs built with pypdf's writer.
  resolved: 2026-11-25. Test run on 2026-11-23, and the Author confirmed plain mode and `MIN_TEXT_CHARS` = 200. Added `GLYPH_NAME_SHARE_MAX` (`unmapped_font_pdf`) for LaTeX/Type 3 decks; see docs/quality/oq1-pdf-extraction.md.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/4-upload-and-text-extraction-with-location.md`
  summary: Cap the request body size before Django reads a whole upload (the 10 MB check runs after it is received).
  evidence: `_from_upload` checks `upload.size` only after the body is spooled to disk; set a server/proxy limit or `DATA_UPLOAD_MAX_MEMORY_SIZE`-style guard with the Hosted setup (OQ-3).
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/4-upload-and-text-extraction-with-location.md`
  summary: Bound pypdf extraction work per upload (decompression bomb or pathological content streams). Unverified; medium if true.
  evidence: Extraction runs in the request with no timeout; settle by timing a crafted 10 MB PDF with a highly compressed stream.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/5-ai-gateway-mock-mode-sample-document-and-daily-limit.md`
  summary: Keep provider response text out of gateway error logs: `ai/gateway.py` logs unexpected exceptions with `logger.exception`, whose traceback may carry the values a pydantic ValidationError quotes. Unverified; medium if true.
  evidence: Mock never raises with Source text; settle when story 10's Anthropic adapter parses real replies by checking what a failed `StudyMaterial` validation logs.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/7-topic-page-with-four-tabs-and-item-deletion.md`
  summary: Detail-level Summary regeneration on P05 (segmented control in the summary-block header, `ai.gateway.regenerate_summary`, replace only the Summary, failure keeps the old one, inactive at the daily limit; AD-5, EXP:134/232/298).
  evidence: Story 6 handed it to story 7, but story 7 (CAP-6) does not name it and the spec was over the size limit; the Author chose on 2026-11-16 to defer it to its own story.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/7-topic-page-with-four-tabs-and-item-deletion.md`
  summary: Add a browser/JS test harness so `static/js/app.js` behaviour (P05 tab keys ← → Home End, focus restore after a tab change) is tested, not only checked by hand.
  evidence: The repo has no JS or browser test runner; `tests/test_shell.py` only checks app.js as source text, so a broken key handler passes every test.
  resolved: 2026-11-25. Retro action E1-1: Playwright browser tests in `tests/browser/` (opt-in, `uv run pytest -m browser`); see spec-retro-e1-1-browser-test-harness.md.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/8-practice-mode-quiz-and-grading.md`
  summary: Story 8b — the Student's Grade override on Free-text Answers («Endre vurdering» → «Riktig»/«Delvis riktig»/«Feil», «Bruk KI-vurderingen», marker «Endret av deg · KI-vurdering: …», tint follows the effective Grade; not on MC or «Ikke rettet») and «Slett spørsmålet» in the P06 feedback panel via the story-7 D09 dialog, the Quiz continuing at the next Question.
  evidence: Split from story 8 at the Author's choice (2026-11-17) because the full CAP-7 spec was ~3000 tokens; story 8 already stores `override_grade` and `with_effective_grade()`, and 8b must land before story 9 (Retry round uses the effective Grade).
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/8-practice-mode-quiz-and-grading.md`
  summary: Distinguish an in-flight Free-text grading (`grade=None`) from a failed one on P06, and make `quiz.services.regrade` claim the row atomically, so a concurrent second POST or regrade neither shows a false «Ikke rettet» nor sends a duplicate grading call.
  evidence: Story 8 renders `grade=None` as `not_graded`/`provider_unavailable` (spec Design Notes) and `regrade` accepts `None`; harmless with Mock's instant grading, but story 10's Real adapter takes up to 15 s, during which a non-HTMX double submit hits this.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/8-practice-mode-quiz-and-grading.md`
  summary: Cover the P06 keyboard contract in `static/js/app.js` (1–4 selects the option, Enter answers, Enter on the feedback heading moves on, focus to `[data-focus-on-swap]` after an HTMX swap) with a browser/JS test.
  evidence: No JS or browser test runner exists; tests only check the markup hooks, so breaking the handlers fails nothing.
  resolved: 2026-11-25. Retro action E1-1: Playwright browser tests in `tests/browser/` (opt-in, `uv run pytest -m browser`); see spec-retro-e1-1-browser-test-harness.md.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/9-quiz-result-and-retry-round.md`
  summary: Story 9b — act on P07 rows in place: «Endre vurdering», «Prøv å rette igjen» and «Slett spørsmålet» inside an expanded result row, re-rendering the band, score, strip and rows under HTMX with the row kept open and focus on its feedback heading (no-JS: redirect to P07 `#q-{position}`).
  evidence: Split from story 9 at the Author's choice (2026-11-18) because the full spec was ~1900 tokens; story 9 shows P07 rows read-only with a link to the P06 position, where these actions already exist (stories 8, 8b).
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/9-quiz-result-and-retry-round.md`
  summary: Cover the P07 strip behaviour in `static/js/app.js` (a slot click or `#q-N` hash opens and focuses its result row) with a browser/JS test.
  evidence: No JS or browser test runner exists; tests only check the `href="#q-N"`/`id="q-N"` markup, so a broken selector fails nothing.
  resolved: 2026-11-25. Retro action E1-1: Playwright browser tests in `tests/browser/` (opt-in, `uv run pytest -m browser`); see spec-retro-e1-1-browser-test-harness.md.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/10-real-mode-privacy-notice-and-key-handling.md`
  summary: `manage.py record_mock`, which re-records the Mock responses from Real mode, strips headers and Keys, and re-plants the wrong-page item (AD-4).
  evidence: It needs real paid calls and a stable prompt, so it waits until the Author has tuned the prompt against real output (OQ-2). The `ai/mock/__init__.py` docstring still says story 10.
- source_spec: none
  summary: Story 11b — P08 «Bla i kort»: browse a Topic's Flashcards in generation order (front first, flip to back and Reference, «Forrige»/«Neste» and ←/→, «Neste repetisjon: {dato}», the card's «⋯» with «Slett kortet»), reached from «Bla i alle kort» in the «Test deg selv» tab; browsing never writes (FR-14, AD-11).
  evidence: Split from story 11 at the Author's choice (2026-11-18): P08 and P09 are independently shippable surfaces, and P09 (Leitner Review) is the larger, riskier half.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/11-flashcard-browsing-and-leitner-review.md`
  summary: The forecast-chart and return-forecast in P09 (the «+1» preview under the rating-buttons, «Bra: kortet kommer tilbake …» live sentence, today's column as cards left, and «Repetert» on the end screen) — build the forecast-chart once in story 13 and add it to Repetisjon there.
  evidence: The Author chose (2026-11-18) to build the forecast once in story 13, where Hjem and Fagoversikt need it; story 11 shows the real return time on each rating-button and the next Due date on the end screen.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/12-topic-score-course-score-weak-topics-and-quiz-history.md`
  summary: The trend-label («Opp 4 poeng» / «etter økta 12. nov.», AD-10), the answer-history «Siste 20 svar» and the tema-forecast-panel on P05, for story 13.
  evidence: Author's decision 2026-11-18 while planning story 12; the trend is a UX assumption not in the PRD, and the panel holds the mini forecast that story 13 builds.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/12-topic-score-course-score-weak-topics-and-quiz-history.md`
  summary: Cover the D10 topic-picker footer update in `static/js/app.js` (checking a box updates «{t} temaer valgt · {q} spørsmål», singular for one) with a browser/JS test.
  evidence: No JS test runner exists; tests only check the server-rendered footer and the data attributes, so a broken listener fails nothing.
  resolved: 2026-11-25. Retro action E1-1: Playwright browser tests in `tests/browser/` (opt-in, `uv run pytest -m browser`); see spec-retro-e1-1-browser-test-harness.md.
- source_spec: none
  summary: Story 13b — the seven-day forecast-chart (real Due dates only, today marked «I dag», counts printed, an ordered list for screen readers) on Hjem («Studievarsel for fagene dine» with fag-forecast-rows and day columns), P04 (mini «Kort i {fag} neste 7 dager»), P05 and in P09 (today as cards left, «Repetert» at the end, the return-forecast preview), absorbing the P09 forecast entry from story 11.
  evidence: Split from story 13 at the Author's choice (2026-11-19): the Next step (CAP-11, Must) ships first; the forecast is a UX surface that is independently shippable.
- source_spec: none
  summary: Story 13c — the trend-label (per tema and per fag), the answer-history «Siste 20 svar» and the tema-forecast-panel «Varsel for temaet» on P05, absorbing the story 12 deferral.
  evidence: Split from story 13 at the Author's choice (2026-11-19); the trend is a UX assumption not in the PRD, and the panel needs the forecast from 13b.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/11b-flashcard-browsing.md`
  summary: Cover P08's ←/→ navigation (and its guards for fields, menus and dialogs) and the shared Space/Enter flip on P08 and P09 with a browser/JS test.
  evidence: No JS test runner exists; the only test greps `app.js` for selector strings, so swapped or guarded-out handlers fail nothing.
  resolved: 2026-11-25. Retro action E1-1: Playwright browser tests in `tests/browser/` (opt-in, `uv run pytest -m browser`); see spec-retro-e1-1-browser-test-harness.md.
- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/11b-flashcard-browsing.md`
  summary: Make a click or tap on the card itself flip it on P08 and P09 (EXPERIENCE.md, flashcard component), not only «Vis svaret» and Space/Enter.
  evidence: The shared card (`components/flashcard_card.html`, from story 11) flips only through the `[data-flip]` link and the keyboard.
