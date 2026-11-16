---
title: 'Study-material generation and the Reference check'
type: 'feature'
created: '2026-11-16'
status: 'done'
baseline_commit: '384ce9fc2e57bc12020e9c16d2c2167a7a345942'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Source stops at `pending` after upload. Nothing claims it, calls the gateway, checks References, or saves Study material, so the core loop has no material (CAP-4, CAP-5, FR-6, FR-9).

**Approach:** Build AD-5 step 2: a committed claim in `courses.services`, then `studymat.services.generate()` running gateway → FR-7 item checks → AD-6 Reference check → one token-guarded save. On P05 the source-row shows the result, and failed Sources get «Prøv igjen».

## Boundaries & Constraints

**Always:**
- `studymat` models (owned, `student` + `source` FK CASCADE, AD-7/AD-8): `Summary` (one per Source, `text`, `detail_level`), `KeyConcept(term, definition)`, `Flashcard(front, back)`, `Question` per AD-9 (`options` JSON). Every item has a Reference: `location_index`, `quote`.
- `courses.services` alone changes status: `claim(source) -> token|None` (one conditional UPDATE over `claimable()`: `pending`, `failed`, or `generating` with `started_at` older than `STALE_AFTER = 5 min`; sets `generating`, fresh `started_at`, clears `failure_reason`), `mark_ready(source, token, language, removed, dropped) -> bool`, `mark_failed(source, token, reason)`. Both match `status=generating AND started_at=token`. `Source.effective_status` / `effective_failure_reason` use the same predicate: `pending` reads as generating, stale reads as `failed`/`timed_out`.
- `generate(student, source)`: claim → build `GenerateRequest` from non-empty `SourceText` rows → gateway (no open transaction, AD-19) → checks → `transaction.atomic()`: `mark_ready` first, then bulk-create items only if it matched. Any `AIError` → `mark_failed(code)`; an empty Summary → `invalid_format`. Retry reuses `SourceText` and `detail_level`. `Source.language` = the language returned.
- FR-7 checks (drop + `dropped_count`): Key-concept definition ≤ 2 sentences; Hint exactly 1 sentence and not containing the correct option's text; Multiple-choice has 4 options, each with an explanation, and `correct_index` in 0–3; Free-text has a `model_answer`.
- Reference check, `studymat/checks.py` (remove + `removed_count`): normalise both sides (strip markers, NFKC, join `-`+line break, fold quotes/dashes, collapse whitespace, casefold). Pass when the quote is ≥ `MIN_QUOTE_WORDS = 5`, `location_index` is a non-empty Location of the Source, the quote occurs there, and it is not repeated (found in > half of the non-empty Locations and in ≥ 2 of them). The marker format lives in `ai/markers.py`; story 10 uses it in the prompt.
- `POST /sources/<id>/generate/` (`studymat:generate`) is owned (404 otherwise) and idempotent: no claim → return the current row without sending. At the limit a failed row's «Prøv igjen» is `disabled` with the daily-limit inline-message. A POST anyway sends nothing. HTMX gets the source-row (+ `#live-polite` OOB status text); otherwise 302 to P05.
- source-row: `ready` reads «Klar» or «Klar · {n} element(er) fjernet». `failed` shows the reason's message and «Prøv igjen», except `needs_key`, which shows its message and «Bruk eksempeldokumentet» (opens D05). Messages for `core/messages.py`: `timed_out` «Genereringen ble ikke ferdig. Prøv igjen.», `truncated` «Kunne ikke lage studiemateriell fordi svaret fra KI-tjenesten ble avbrutt. Prøv igjen.», `rate_limited` «KI-tjenesten har mange forespørsler akkurat nå. Vent noen minutter og prøv igjen.», `refused` «Kunne ikke lage studiemateriell fordi KI-tjenesten avviste forespørselen. Prøv igjen.», `invalid_format` «Kunne ikke lage studiemateriell fordi svaret fra KI-tjenesten hadde feil format. Prøv igjen.», `provider_unavailable` «Kunne ikke lage studiemateriell fordi KI-tjenesten ikke svarte. Prøv igjen.».
- Starting generation (Author's decision 2026-11-16): a `pending` source-row sends one `hx-post` to `studymat:generate` with `hx-trigger="load"` and `hx-swap="outerHTML"`. This is the second named exception to AD-13's no-lazy-loading rule, next to the pending-Grade cell. The claim makes a reload or a second tab safe.
- FR-3 limits stay module constants in `ingestion/extract.py` (unchanged).

**Never:** Topic tabs, Summary/Key-concept display, the «… ble fjernet fordi …» note, item deletion (story 7); Detail-level Summary regeneration UI (story 7); Anthropic adapter, prompts, privacy, `key_rejected` text (story 10); background runs (story 18); polling; a confidence score.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sample, Mock | pending Sample Source | `ready`, language `nb`, removed 1, dropped 0, ≥ 5/10/10 items, both Question kinds; «Klar · 1 element fjernet» | N/A |
| Other file, Mock | pending non-Sample | `failed`/`needs_key`, nothing saved, count unchanged; «Bruk eksempeldokumentet» | row 200 |
| Provider error | gateway raises `Truncated` | `failed`/`truncated`, nothing saved, counted | row 200 |
| Retry | failed Source, «Prøv igjen» | claimed again, `ready`; SourceText untouched | N/A |
| Double POST | Source already `generating` (fresh) | no second gateway call; current row | 200 |
| Stale run | `generating`, started 6 min ago | reads `failed`/`timed_out`; retry claims it | N/A |
| Late finish | token replaced by a newer claim | `mark_ready` matches nothing; nothing saved | N/A |
| Daily limit | pending, 20 used | `failed`/`daily_limit`; «Prøv igjen» disabled + message | 200 |
| Not owned | other Student's Source | 404 | 404 |

</frozen-after-approval>

## Code Map

- `courses/models.py` `Source` (status, failure_reason, started_at, language, removed_count, dropped_count exist; no migration needed) -- add `SourceQuerySet(OwnedQuerySet).claimable()` and the `effective_*` properties.
- `courses/services.py` -- add `claim`, `mark_ready`, `mark_failed`; `create_source` already sets `started_at`.
- `ai/gateway.py` `generate_study_material`, `ai/schemas.py` `GenerateRequest`/`Location`/`StudyMaterial`, `ai/errors.py` -- reuse unchanged; `ai/markers.py` new.
- `ai/mock/study_material.json` -- BCNF Flashcard planted at index 11 (quote on page 13); every other item must pass FR-7 and the Reference check (fix the recording, not the rule, if one does not).
- `ingestion/models.py` `SourceText(kind, index, label, text)` -- read-only from studymat.
- `studymat/` -- no `models.py`/`migrations` yet; add `models.py`, `migrations/`, `services.py`, `checks.py`, `generate` view + URL.
- `templates/components/source_row.html`, `status_label.html` -- read `effective_status`; add the failure/removed lines, action button and the pending load trigger.
- `web/views.py` `topic` -- passes `sources`; no change beyond what the row needs.
- `core/messages.py` -- add the six codes.
- `tests/conftest.py` `freeze_now`; `tests/test_ai_gateway.py` -- patterns for `transaction=True` and counting.

## Tasks & Acceptance

**Execution:**
- [x] `courses/models.py`, `courses/services.py` -- queryset, effective status, claim/mark functions -- AD-5.
- [x] `studymat/models.py` + migration -- four models -- AD-9, ERD.
- [x] `ai/markers.py`, `studymat/checks.py` -- markers, normalise, FR-7 checks, Reference check -- AD-6, FR-8.
- [x] `studymat/services.py` -- `generate()` orchestrator -- AD-5, AD-19.
- [x] `studymat/views.py`, `studymat/urls.py`, `source_row.html`, `status_label.html`, `core/messages.py` -- endpoint and row states -- FR-9.
- [x] `tests/test_generation.py`, `tests/test_reference_check.py` -- every matrix row plus unit cases (hyphenation, line breaks, curly quotes, 4-word quote, header repeated on most pages, single-Location Source, missing Location) named `test_fr7_…`/`test_fr8_…`/`test_fr9_…`.

**Acceptance Criteria:**
- Given a failed attempt of any kind, then no Summary, Key concept, Flashcard or Question row exists for that Source.
- Given generation runs, then the gateway is called outside any atomic block and the claim is committed before it.
- Given `uv run pytest` offline, then everything passes, including the import-graph test.

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap).

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| `sentence_count`: «1. normalform» counts as two sentences (BH) | medium | patch | Verified: `sentence_count('Tabellen er på 1. normalform.') == 2`; the Sample's own domain uses ordinals, so valid Hints and definitions get dropped in Real mode. |
| Abbreviation mask matches inside words, e.g. «Jamaica.» (BH, ECH) | low | patch | Verified: «Han bor i Jamaica. Det er varmt.» counts 1; a two-sentence Hint passes. Direct correction (word boundary). |
| Correct option found as a substring of the Hint (BH, ECH) | medium | patch | `correct in normalise(hint)`; a short option such as «Ja» or «2» matches inside other words and drops a valid Question. |
| Free-text Question with options or `correct_index` is saved (VG, ECH) | low | patch | `question_ok` checks only `model_answer` for free_text; AD-9 says no options. |
| Every Location re-normalised per item (BH) | low | patch | `reference_ok` rebuilds the normalised map per call; a 50-page Source normalises it ~40 times. Direct refactor. |
| Daily-limit text shown twice on a `daily_limit` row at the limit (ECH) | low | patch | Reason note and inline-message both render `MESSAGES["daily_limit"]`; met every time a pending row hits the limit. |
| No test: stale row at the limit is not claimed (VG) | low | patch | Pre-verified gap; flipping the guard to `!= FAILED` passes every test. |
| No test: quote on exactly half the Locations is kept (VG) | low | patch | Pre-verified gap; `>` → `>=` passes every test. |
| No CSRF test for `studymat:generate` (VG) | low | patch | Pre-verified gap; repo tests CSRF on every other POST. |
| Non-`AIError` after the claim leaves the row `generating` → 500 (BH, ECH) | low | reject | Mock never raises one; AD-5's 5-minute predicate turns it into `timed_out` with «Prøv igjen», the designed recovery. Real-mode parse errors become `InvalidFormat` in story 10's adapter. |
| `assert` in `mark_failed` stripped under `-O`; unknown code (BH, ECH) | false | reject | The app never runs under `-O` (story 5 precedent); every `ai.errors` code is a `FailureReason` value (tested in story 5). |
| `time` not imported in `courses/models.py` (BH) | false | reject | `from core import time` is already at the top; all tests pass. |
| Logging thin outside gateway (BH) | low | reject | The gateway logs Student, operation and outcome per call (Conventions); no named harm. |
| `_save` doesn't delete old items before insert (BH) | false | reject | `claimable()` excludes `ready`; failed runs save nothing, so no Source ever has items when `_save` runs. |
| Same index across Location kinds collapses (BH, ECH) | low | reject | PDF and text Sources have one kind; only Word (story 17) could mix kinds. Recorded in Implementation Notes for story 17. |
| `generating` row never polls (BH, ECH) | false | reject | Polling is a frozen Never; FR-26 (story 18). |
| Worker timeout vs synchronous call (BH) | low | reject | `runserver` has no worker timeout; the Hosted setup (story 18, AD-16) owns this. |
| Provider failures count toward the limit (BH) | false | reject | AD-3: "An attempt that fails after the send still counts." |
| `refused`/`rate_limited` offer immediate «Prøv igjen» (BH) | false | reject | EXPERIENCE.md specifies «Prøv igjen» for both. |
| Empty reason text for `key_rejected`/`privacy_not_accepted` (BH, ECH) | low | reject | Unreachable until story 10 adds those errors and their messages. |
| No DB CheckConstraint on Question shape (BH) | low | reject | Only `studymat.services` writes Questions (AD-1), behind `question_ok`. |
| `generate(student, source)` with another Student (BH) | false | reject | The only caller passes `request.user` with a Source fetched owned by that user. |
| Stale run finishing late turns `ready` (ECH) | false | reject | Its token still matches, nobody re-claimed, and the material is valid; AD-5 guards only against overwriting a newer run. |
| Compound hyphen at a line end («e-\npost») joins to «epost» (ECH) | low | reject | AD-6 requires joining hyphenation; rare in slide text, and both-variants matching adds a branch. |
| Quote starting mid-word passes (ECH) | low | reject | A ≥ 5-word quote still has to stand at that Location; no wrong item reaches the Student. |
| All items dropped → `ready` with only a Summary (ECH) | low | reject | The spec makes only an empty Summary a failure; FR-7 minimums are tuned values, not failure conditions. |
| Clock stepping backwards keeps a run fresh (ECH) | low | reject | Not met in everyday use. |
| Extra missing tests (null `started_at`, page-spanning quote, lambda style) (BH) | low | reject | Branches either covered indirectly or follow AD-6 by design; style only. |

## Design Notes

**Save guard** (all or nothing, AD-5):

```python
with transaction.atomic():
    if not courses_services.mark_ready(source, token, material.language, removed, dropped):
        return  # a newer run owns the Source; save nothing
    Summary.objects.create(...); KeyConcept.objects.bulk_create(...)  # etc.
```

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes

## Implementation Notes
- Marker format (`ai/markers.py`): `[[L{index}]]`; `marked_text()` marks only non-empty Locations. Story 10 may change the format here only.
- The Sample recording passed FR-7 and the Reference check unchanged: 7/10/11 items saved, removed 1 (BCNF Flashcard, `location_index` 11), dropped 0.
- Beyond the listed FR-7 rules, an item with an empty term, front/back or prompt is also dropped (structure failure).
- At the daily limit the view claims only a `pending` row (so the gateway marks it `daily_limit`, or `needs_key` first); a failed or stale row is not claimed and keeps its reason.
- A non-`AIError` exception after the claim leaves the Source `generating`; it reads as `failed`/`timed_out` after 5 min.
- A fresh `generating` row (second tab) shows the spinner with no polling, per the spec; it updates on reload.
- Messages for `privacy_not_accepted`/`key_rejected` are not added (story 10); such a row shows «Feilet» + «Prøv igjen» with no reason text (`message_text` filter returns "").
- For story 17 (Word): `studymat.services.locations()` keys Locations by `index` only. A Source mixing `heading` and `paragraph` rows with the same index would send duplicate markers and check against the wrong text; settle the Location key there.
- Review patch side effect: a full stop right after a digit never ends a sentence, so «… i 2026. Så …» counts as one sentence (slightly more lenient FR-7 check).
