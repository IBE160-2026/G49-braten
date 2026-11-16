---
title: 'AI gateway, Mock mode with the Sample document, and the daily limit'
type: 'feature'
created: '2026-11-16'
status: 'done'
baseline_commit: 'b8c21b935967cad8f46e067c1c97590519b1b102'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing can reach a language model yet: there is no `ai` port, no Mock mode, no Sample document with recordings, no mode shown to the Student, and no daily limit (CAP-12, CAP-13 NFR-7). Story 6 needs all of these to generate.

**Approach:** Build `ai.gateway` as the single port (AD-2) with the Mock adapter answering from recordings keyed by the Sample document's `content_sha256` (AD-4), a database counter for Generation calls (AD-3, AD-19), the mode-banner, and «Bruk eksempeldokumentet» in D05.

## Boundaries & Constraints

**Always:**
- `ai/schemas.py` (Pydantic, AD-2 rules: no length/numeric constraints, no `reasoning` field, enums lower-cased before validation): `Location(index, text)`, `GenerateRequest(source_id, content_sha256, language, detail_level, locations)`, `SummaryRequest(...)`, and `StudyMaterial(language, summary, key_concepts, flashcards, questions)` where every item has `reference = {location_index, quote}`; Question per AD-9 (`kind`, `prompt`, `hint`, `options` of four `{text, explanation}`, `correct_index`, `model_answer`).
- `ai/errors.py`: one class per AD-2 code, each with `code` equal to a `courses.FailureReason` value; messages in `core/messages.py`: `needs_key` «I demomodus lages studiemateriell bare for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.», `daily_limit` «Du har brukt alle 20 genereringene for i dag. Grensen nullstilles ved midnatt.»
- `ai.gateway`: `mode()` (`mock`/`real` from `settings.AI_PROVIDER`), `remaining_today(student)`, `generate_study_material(student, GenerateRequest)` and `regenerate_summary(student, SummaryRequest)`. Order per AD-3: mode check (Mock + non-Sample sha → `NeedsKey`, counts nothing) → counter → send. Asserts `not connection.in_atomic_block` (AD-19). Logs Student id, operation, outcome; never text or Key.
- Counter: `ai.GenerationCallCount(student, day, count)`, unique (student, day), `day` = `core.time.today()`. Increment is one conditional UPDATE `count < DAILY_LIMIT` committed on its own; 0 rows → `DailyLimitReached`. `DAILY_LIMIT = 20` (NFR-7) as module constant. A failed send still counts; Mock counts too.
- Mock adapter returns a recording validated through the same schema models; Real mode raises `ProviderUnavailable` until story 10.
- Sample document (Author's decision 2026-11-16): our own deck of about 20 slides of Norwegian bokmål lecture text, «Databaser: normalisering», written in this story and released CC0 by the Author. `sample/build_sample.py` renders `sample/source.md` to the committed `sample/normalisering.pdf` with the pinned `pypdf` (Helvetica/WinAnsi, æøå; no new dependency — Author's decision 2026-11-16, replacing `fpdf2`); licence in `sample/README.md`. One slide per PDF page. Recordings in `ai/mock/` as JSON: Study material plus a Summary for each Detail level, quotes copied verbatim from pypdf's extracted page text, exactly one item whose `location_index` points to the wrong page (its quote stands on another page).
- Mode-banner (DESIGN component) below the top-bar in the shell and on P01/P02 whenever Mock mode: «Demomodus: appen bruker innspilte svar for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.» Not closable.
- D05 in Mock mode: «Bruk eksempeldokumentet» (secondary submit) ingests the Sample PDF into the Topic through `ingestion.services.ingest()` with the chosen Detail level, then `HX-Location` to P05. At `remaining_today == 0` D05 shows the daily-limit inline-message, «Last opp» and «Bruk eksempeldokumentet» are `disabled`, and a POST anyway saves nothing and re-renders with the message.

**Never:** Generation lifecycle, claim, Reference check, saving Study material, the `needs_key` source-row message (story 6); Anthropic adapter, privacy guard (AD-17), Key-rejected/rate-limit handling (story 10); `grade_free_text` (story 8) and `simpler_explanation` (story 16) beyond signatures raising `NotImplementedError`; `record_mock` (story 10, see Design Notes); any network call.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sample, Mock | request with Sample sha, 0 used today | validated `StudyMaterial`; count 1 | N/A |
| Summary, Mock | Sample sha, `detailed` | the `detailed` recorded Summary; counts 1 | N/A |
| Other file, Mock | non-Sample sha | `NeedsKey`; count unchanged | raised |
| 21st call | 20 used today | `DailyLimitReached`; count stays 20; no send | raised |
| New Oslo day | 20 used yesterday, 00:05 Oslo | call succeeds; today's count 1 | N/A |
| Two Students | A at 20 | B's call succeeds | N/A |
| Inside atomic | call within `transaction.atomic()` | AssertionError | N/A |
| D05 sample | Mock, «Bruk eksempeldokumentet», «Detaljert» | Source pdf/pending/detailed with Sample sha; P05 | N/A |
| D05 at limit | 20 used, GET / POST | message shown; buttons disabled; POST saves nothing | 200 |
| Real mode | `AI_PROVIDER=anthropic` + Key | no banner; no «Bruk eksempeldokumentet» | N/A |

</frozen-after-approval>

## Code Map

- `config/env.py` `effective_ai_provider`, `config/settings.py` `AI_PROVIDER`, `config/settings_test.py` (forces mock) -- mode source; reuse, don't change.
- `courses/models.py` `FailureReason`, `DetailLevel` -- error codes and detail values; `ai` may not import `courses` (AD-1: ai → accounts only), so `ai` repeats the string values and a test asserts they match `FailureReason.values`.
- `core/time.py` `today()` -- the Oslo day for the counter; tests use `freeze_now` (`tests/conftest.py`).
- `core/messages.py` -- add the two codes.
- `ai/` -- only `apps.py` exists; add `models.py`, `migrations/`, `schemas.py`, `errors.py`, `gateway.py`, `mock/` (adapter + JSON).
- `ingestion/services.py` `ingest(topic, upload=..., detail_level=...)` -- reuse for the Sample; pass a Django `File` opened on the Sample path, named as the file.
- `studymat/views.py` `add_source`, `studymat/forms.py` `AddSourceForm`, `templates/studymat/add_source.html`, `templates/components/dialog.html` -- D05; add the sample submit (a `use_sample` button name) and the limit state. studymat may import `ai`.
- `web/context_processors.py` `shell` -- add `ai_mode` for every page (web reaches ai); used by `layouts/shell.html` and `layouts/auth.html`.
- `static/css/components.css` -- add `.mode-banner` using existing tokens (forecast-soft as in `.inline-message--info`).
- `tests/test_import_graph.py` -- must stay green; `tests/pdfs.py` has the PDF builder used by story 4 tests.

## Tasks & Acceptance

**Execution:**
- [x] `sample/` -- write the slide text, the build script, the committed PDF and `README.md` with CC0 licence -- CAP-12 copyright-free.
- [x] `ai/schemas.py`, `ai/errors.py` -- schemas and errors as above -- AD-2 contract.
- [x] `ai/models.py` + migration -- `GenerationCallCount` with `student` FK CASCADE, unique constraint -- AD-3.
- [x] `ai/mock/__init__.py`, `ai/mock/*.json` -- `SAMPLE_PATH`, `SAMPLE_SHA256` (computed from the file at import), loader validating recordings -- AD-4.
- [x] `ai/gateway.py` -- operations, `mode()`, `remaining_today()`, counter increment -- AD-2, AD-3, AD-19.
- [x] `core/messages.py` -- `needs_key`, `daily_limit`.
- [x] `web/context_processors.py`, `templates/components/mode_banner.html`, `layouts/shell.html`, `layouts/auth.html`, `components.css` -- mode-banner.
- [x] `studymat/views.py`, `studymat/forms.py`, `templates/studymat/add_source.html` -- sample button and limit state.
- [x] `tests/test_ai_gateway.py`, `tests/test_mock_recordings.py`, `tests/test_mode_banner.py`, extend `tests/test_upload.py` -- every matrix row, named by FR (`test_nfr7_…`, `test_fr20_…`).

**Acceptance Criteria:**
- Given the Sample PDF ingested, then its `content_sha256` equals `SAMPLE_SHA256` and its SourceText page count equals the recordings' page range.
- Given the recordings, then all validate against `StudyMaterial`, contain ≥ 5 Key concepts, ≥ 10 Flashcards, ≥ 10 Questions with both kinds, and exactly one item's normalised quote is absent from its own page but present on another; every other quote (≥ 5 words) is on its page.
- Given an empty `.env`, when any page renders, then the mode-banner shows; with `AI_PROVIDER=anthropic` and a Key it does not, and the Key appears in no response.
- Given `uv run pytest` offline, then everything passes, including the import-graph test.

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap).

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| `fpdf2` dev dependency absent; build uses pypdf (BH, ECH) | medium | intent_gap → resolved | Author chose to keep pypdf (2026-11-16); frozen block updated. Frozen Always names `fpdf2`; agent's `uv add` was refused by permissions. Code works; only the build tool differs. Put to the Author rather than reverting the whole story. |
| `build_sample.py` uses private `writer._add_object` (BH) | low | grouped with fpdf2 | Same root: renderer choice; pinned pypdf 7.0.1 today. |
| `hx-disabled-elt` test checks only presence (VG) | low | patch | `tests/test_courses.py` asserts `"hx-disabled-elt=" in content`; selector changed in this diff. |
| «20» in `daily_limit` text not tied to `DAILY_LIMIT` (BH, ECH) | low | patch | No test links them; a one-line test does. |
| "Committed before send" test reads on same connection (BH) | low | patch | Would also see an uncommitted write; asserting `not in_atomic_block` in send settles it. |
| Off-page check after final decrement rejects a fitting slide (ECH) | low | patch | `y < MARGIN` checked after the last `y -= LINE_GAP`. |
| `logger.exception` may log provider text via ValidationError tracebacks (BH) | maybe-false (medium if true) | defer | Mock never raises with Source text; real parsing errors arrive with story 10's adapter. |
| AD-19 enforced by `assert`, stripped under `-O` (BH, ECH) | low | reject | AD-19 says "the gateway asserts"; the app never runs under `-O`. |
| `ai.mock` import fails if the PDF is missing (BH, ECH) | low | reject | PDF is committed; app runs from a clone, no packaging; lazy loading adds a branch. |
| `SAMPLE_PAGES` literal contradicts "no code change" (BH) | false | reject | Docstring and README say only the SHA needs no update. |
| No test that committed PDF matches `source.md` (BH) | low | reject | Developer-only drift; recordings are checked against the PDF itself; fix needs a render-to-path parameter. |
| `--demo-*` tokens undefined (BH) | false | reject | `static/css/tokens.css:53-55` and `:155` define them for both themes. |
| No concurrency test at the limit (BH) | low | reject | Conditional UPDATE is atomic in SQLite; a threaded SQLite test adds flakiness. |
| Sample twice shows «Velg en annen fil» on a duplicate rejection (BH) | false | reject | `ingest()` has no duplicate check; the second Sample is accepted. |
| Sample IngestError marks the text field (ECH) | low | reject | The committed Sample passes every limit; unreachable without changing limits. |
| Disabled buttons' `aria-describedby` not reachable (BH) | low | reject | The limit message is a visible `role="alert"` above the controls; switching to `aria-disabled` changes the interaction. |
| Empty-`.env` AC tested only via `effective_ai_provider({})` (BH) | low | reject | Settings read env through that function; a reloaded-settings render test adds a fixture for no new path. |

## Design Notes

**Recordings without `record_mock`.** AD-4 says only `manage.py record_mock` writes recordings, but that command needs the Anthropic adapter (story 10). Story 5 therefore writes the recordings by hand against the extracted page text; story 10 adds `record_mock`, which re-records them and re-plants the wrong-page item. The recordings are what Mock mode ships either way.

**Counter increment** (no transaction, each statement autocommits):

```python
row, _ = GenerationCallCount.objects.get_or_create(student=student, day=time.today())
if not GenerationCallCount.objects.filter(pk=row.pk, count__lt=DAILY_LIMIT).update(count=F("count") + 1):
    raise DailyLimitReached()
```

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes

## Implementation Notes

- **Resolved: pypdf instead of `fpdf2` (Author, 2026-11-16).** Adding `fpdf2` to the dev group (`uv add --dev fpdf2`) was refused by the agent's permission check, so `sample/build_sample.py` renders the PDF with `pypdf` (already pinned), drawing Helvetica/WinAnsi like `tests/pdfs.py`. One slide per page, æøå/«»/–/• extract verbatim, output is byte-for-byte reproducible. To follow the spec literally: approve `uv add --dev fpdf2`, port `render()` to fpdf2, rebuild, run `tests/test_mock_recordings.py` (quotes are copied from lines of `source.md`, so they should survive if fpdf2 keeps one line per text line). `SAMPLE_SHA256` is computed at import, so nothing else changes.
- **Schemas.** `SummaryRequest` has the same fields as `GenerateRequest`; `regenerate_summary` returns `SummaryResponse(summary)`. `StudyMaterial.summary` is a plain string. Free-text Questions have `options=[]` and `correct_index=None`; Multiple-choice have `model_answer=""`.
- **Recordings.** `ai/mock/study_material.json` (7 Key concepts, 11 Flashcards, 11 Questions: 7 multiple-choice, 4 free-text) and `ai/mock/summaries.json` (one per Detail level). The Mock adapter swaps in the Summary for the request's Detail level. The planted wrong-page item is the BCNF Flashcard: `location_index` 11, quote from page 13. References cover every page 1–20, which is what the "page range" acceptance test checks.
- **D05.** «Bruk eksempeldokumentet» sits at the top of the upload-panel. Because it is a second submit button, `components/dialog.html` gained `extra_submit` (a visually hidden copy of the main submit placed first, so Enter in a field still means «Last opp»), plus `submit_disabled` / `submit_describedby`. `hx-disabled-elt` now targets `.dialog-foot button[type='submit']`. A POST at the limit renders an unbound form (initial values kept) so no field errors appear.
- **Gateway tests** use `django_db(transaction=True)` because of the AD-19 assertion.
