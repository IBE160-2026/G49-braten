---
title: 'Real mode, privacy notice and Key handling'
type: 'feature'
created: '2026-11-18'
status: 'done'
baseline_commit: 'e55ef4c2252d3995f1ab527b5cf24f606ae6dd44'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** With a Key set, every AI call fails as `provider_unavailable`: there is no Anthropic adapter, no privacy notice, and nothing stops Source text leaving before the Student accepts (CAP-13, FR-21, FR-22).

**Approach:** Add the Anthropic adapter (Claude Haiku 5.5, structured output) behind `ai.gateway` for generation, Summary and grading; enforce privacy acceptance in the gateway (AD-17); show D04 «Før du laster opp» before D05 in Real mode; map provider errors to the named messages.

## Boundaries & Constraints

**Always:**
- **Provider:** only `ai` imports `anthropic` (added to `pyproject.toml`/`uv.lock`). Model `claude-haiku-5-5`, a constant in `ai`. `messages.create` with `output_config.format` = the `ai.schemas` response model's JSON schema (as `messages.parse` would build it), validated in `ai` after the stop reason is read (Author's decision 2026-11-18: `parse` validates before the stop reason is visible, so refusals and truncations would show as `invalid_format`), `output_config.effort` set per operation (`low` for grading, `medium` for generation and Summary), no sampling parameters, no Citations or PDF blocks, no assistant prefill. `max_tokens` 16000, not streamed.
- **Response (AD-2):** only `stop_reason == "end_turn"` is parsed. `refusal` → `Refused`; `max_tokens`/`model_context_window_exceeded` → `Truncated`; any other stop reason, or JSON/pydantic validation failure → `InvalidFormat`.
- **Errors:** `AuthenticationError`/`PermissionDeniedError` → `KeyRejected`; `RateLimitError` → `RateLimited`; `APITimeoutError`, `APIConnectionError`, 5xx/529 and any other `APIError` → `ProviderUnavailable`. The app keeps running.
- **Timeouts:** grading `max_retries=0`, timeout 12 s (whole call under 15 s, NFR-3); generation and Summary `max_retries=1`, timeout 110 s.
- **Prompts** in `ai`: generation sends `markers.marked_text(locations)`, asks for the FR-7 counts and rules (Summary at the Detail level, ≥ 5 Key concepts, ≥ 10 Flashcards, ≥ 10 Questions with both kinds, four options for Multiple-choice, one-sentence Hints that never give away the answer, Key-concept definitions of at most two sentences, each item's Reference = a Location index plus a verbatim quote), in the Source's language. Grading sends Question, model answer, Source text and Answer, and asks for `correct`/`partial`/`incorrect` with a short Explanation in the Source's language.
- **Privacy (AD-17):** in Real mode, `generate_study_material`, `regenerate_summary` and `grade_free_text` raise `PrivacyNotAccepted` when `student.privacy_accepted_at` is null, after the mode check and before the counter, so it counts nothing and sends nothing. Never checked in Mock mode.
- **D04 is its own dialog URL** (Author's decision 2026-11-18): `studymat:privacy` at `privacy/?next=<relative path>`, a GET dialog per AD-18 (full page normally, the `dialog` partial in `#dialog` under HTMX). Title «Før du laster opp», the mockup's lead text (EXPERIENCE.md, mockup D04), buttons «Jeg forstår, fortsett» and «Avbryt». «Jeg forstår, fortsett» POSTs, calls `accounts.services.accept_privacy(student)` (sets `privacy_accepted_at` once, the only writer) and goes to the safe `next` (`safe_next`). «Avbryt»/Esc closes, nothing is stored or sent, and the notice shows again next time. In Mock mode the URL redirects to `next` without showing anything.
- **Where D04 appears:** in Real mode with no acceptance, `studymat:add_source` shows D04 (with `next` = D05) instead of D05, and a D05 POST saves nothing and shows D04. The `privacy_not_accepted` message on the source-row and in the feedback panel links to D04 with `next` = the current page, so the Student accepts where they are and then uses «Prøv igjen».
- **Messages** in `core/messages.py`, bokmål: add `privacy_not_accepted` («Du må godta personvernvarselet før teksten sendes til KI-tjenesten.») plus the link text «Les og godta varselet». The source-row shows any failure code's message as today; quiz grading shows `key_rejected`, `rate_limited` and `privacy_not_accepted` by name, others as `grading_failed`.
- **The Key** is read only from settings, passed only to the `anthropic` client, and never logged, rendered, put in an exception message or committed. `.env.example` keeps it empty.

**Never:**
- A network call in tests (`--disable-socket` stays); tests fake the client.
- `simpler_explanation` (story 16), `manage.py record_mock`, background generation, prompt tuning against real output (OQ-2, NFR-5 content check: Author's manual work).
- Changing the daily limit, the Mock adapter or recordings, or the Reference check.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Generate, Real | accepted, valid structured reply | Source ready, Study material saved, 1 call counted | N/A |
| Not accepted | Real, `privacy_accepted_at` null, generate/grade | no send, counter unchanged | `privacy_not_accepted` |
| First upload | Real, not accepted, «Legg til kilde» | D04; «Jeg forstår, fortsett» → D05; «Avbryt» → nothing stored | N/A |
| Accept elsewhere | Real, failed `privacy_not_accepted` row or «Ikke rettet» | link opens D04; accept → back to the same page; «Prøv igjen» then sends | N/A |
| Bad `next` | `next=https://evil.example` | accept → falls back to Hjem | refused by `safe_next` |
| Mock | any Student | no D04, no privacy check | N/A |
| Key rejected | 401 / 403 | Source failed `key_rejected`; quiz «Ikke rettet» with the Key message | named message |
| Rate limit | 429 | `rate_limited`, «Prøv igjen» | named message |
| Refusal / truncated / bad JSON | stop_reason or parse failure | `refused` / `truncated` / `invalid_format`; nothing saved; call counted | named message |
| Grading timeout | no reply in 12 s | Answer «Ikke rettet» | `provider_unavailable` |

</frozen-after-approval>

## Code Map

- `ai/gateway.py:116-134` -- `_send_generate`/`_send_summary`/`_send_grade` raise `ProviderUnavailable` in Real mode: route to the adapter. Add the privacy check in `_counted` (after the mode gate, before `_count_call`) and in `_uncounted` for grading (Real mode only). Keep the logging rule: Student id + outcome code only.
- `ai/anthropic_adapter.py` (new) -- client built lazily from `settings.ANTHROPIC_API_KEY`; `generate(request)`, `summary(request)`, `grade(request)`; stop-reason and exception mapping; prompts (or `ai/prompts.py`).
- `ai/errors.py:29` `PrivacyNotAccepted`, `:39` `RateLimited`, `:55` `KeyRejected` exist; codes match `courses.models.FailureReason` (`privacy_not_accepted` at `courses/models.py:81`).
- `ai/schemas.py` -- `StudyMaterial`, `SummaryResponse`, `GradeResponse` are the `output_format` models; keep them constraint-free. `ai/markers.py:marked_text` builds the prompt text.
- `config/settings.py:36-37`, `config/env.py:40` -- Key and `AI_PROVIDER` already resolved; `config/settings_test.py` forces Mock.
- `accounts/models.py:25` `privacy_accepted_at` exists; create `accounts/services.py` with `accept_privacy`.
- `studymat/views.py:58` `add_source` -- D04 gate; new `privacy` view and `studymat/urls.py` entry; `templates/studymat/privacy_notice.html` (new) using `components/dialog.html` like `add_source.html`. `core/http.py` `safe_next(request, field)` for `next`.
- `templates/studymat/source_row.html` (failure text) and `templates/components/feedback_panel.html` («Ikke rettet» reason) -- add the D04 link when the code is `privacy_not_accepted` (`hx-get` into `#dialog`, as `item_menu_items.html` does).
- `core/messages.py:42-55` -- add `privacy_not_accepted`; `quiz/views.py:395` `_failure_message` -- add the named codes.
- `studymat/services.py:61` and `quiz/services.py:155` already catch `AIError` and store `error.code`: no change expected.
- Tests: `tests/test_ai_gateway.py` (:67, :211 set Real mode and expect `ProviderUnavailable`; update), new `tests/test_anthropic_adapter.py` (fake client object via monkeypatch, no socket), `tests/test_privacy_notice.py`. `tests/test_import_graph.py:29` already restricts `anthropic` to `ai`.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- `uv add anthropic` -- the SDK for the adapter.
- [x] `ai/anthropic_adapter.py`, `ai/gateway.py` -- adapter, prompts, error mapping, privacy guard -- FR-21, AD-2, AD-17.
- [x] `accounts/services.py`, `studymat/views.py`, `studymat/urls.py`, `templates/studymat/privacy_notice.html`, `source_row.html`, `feedback_panel.html` -- D04 URL, its links and `accept_privacy` -- FR-22.
- [x] `core/messages.py`, `quiz/views.py` -- `privacy_not_accepted` and named grading failures.
- [x] `tests/test_anthropic_adapter.py`, `tests/test_privacy_notice.py`, `tests/test_ai_gateway.py` -- every matrix row; request shape (model, effort, `output_format`, no sampling params, marked text); every stop reason and exception class; the Key never appears in logs (caplog) or any rendered page.

**Acceptance Criteria:**
- Given Real mode and an accepted Student, when the fake client returns a valid `StudyMaterial`, then the Reference check runs and the Source becomes ready as in Mock mode.
- Given Real mode and a Student who has not accepted, when any gateway operation runs, then the fake client is never called.
- Given no Key, when the app runs, then it is Mock mode and no D04 is shown.

## Implementation Notes

- **`messages.create` instead of `messages.parse` (accepted by the Author 2026-11-18, now in the frozen block).** The SDK's `messages.parse` validates every text block inside the call, before the caller sees `stop_reason`. A refused or truncated reply rarely matches the schema, so it would raise a pydantic error and always come out as `invalid_format`, never `refused`/`truncated`, which breaks the AD-2 rule and the matrix row. The adapter therefore sends the same request `parse` would build (`output_config.format` = the `ai.schemas` model's JSON schema through `anthropic.transform_schema`, plus `effort`), reads the stop reason first, and validates only `end_turn` with `Model.model_validate_json`. In SDK 2.8.0, `output_format` is also marked deprecated in favour of `output_config.format`.
- After acceptance, a GET to D04 goes straight to `next`, so an old link never asks again. Accepting from the D05 gate under HTMX swaps D05 into `#dialog` and does not navigate.
- `tests/conftest.py` has an autouse guard: building the real Anthropic client in any test fails the test. Adapter tests use the real SDK on an `httpx2.MockTransport`, so no socket is opened.

## Spec Change Log

- **2026-11-19, after the Author's walkthrough (risk spots fixed at the Author's request).**
  - *Retries:* the frozen «generation and Summary `max_retries=1`» is now the adapter's own single retry with the SDK at `max_retries=0`. It retries 429, 5xx/529 and a lost connection, never a timeout (a timed-out request may have run and been billed) or a rejected Key. Worst case drops from about 220 s to about 112 s, and no request is billed twice.
  - *SDK logging:* the `anthropic`, `httpx`, `httpx2` and `httpcore` loggers are held at WARNING, so `ANTHROPIC_LOG=debug` cannot write Source text to the log (triage row 22, now patched).
  - *Unexpected errors in generation:* any non-`AIError` from the gateway fails the Source at once as `provider_unavailable` with «Prøv igjen», instead of a 500 and «genererer» until the AD-5 timeout.
  - *Privacy coverage:* a test lists every public gateway operation that takes a Student and a request and requires each to raise `PrivacyNotAccepted` in Real mode before acceptance; a new operation fails the test until it is added.
  - *Not fixed here:* the prompts' quality against real replies stays the Author's OQ-2 and NFR-5 content check.

## Review Triage Log

Pass 1 (iteration 0) — Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG).

| # | Source | Finding | Verdict | Evidence / route |
|---|--------|---------|---------|------------------|
| 1 | VG | D05 swapped in after D04 accept at the daily limit is untested | medium | `_render_add_source` recomputes `at_limit`, but no test pins it; a regression would show a usable D05 that saves nothing (NFR-7). **patch** (test) |
| 2 | VG | Feedback-panel D04 link never checked to vanish after acceptance | low | Only the source-row variant is tested. **patch** (test) |
| 3 | VG, BH, EC | `privacy` POST stores acceptance before the 404 for another Student's Topic in `next` | low | Needs a hand-crafted `next`; the Student did accept, so storing it is harmless. reject |
| 4 | VG, BH | Tests import `httpx2`, a transitive dependency; "lockfile missing" | low / false | `uv.lock` is updated (excluded from the review diff); `httpx2` is the SDK's own transport, so an SDK change rewrites these tests anyway. reject |
| 5 | BH | `accept_privacy` race guard never exercised | low | Second call returns at the early check. **patch** (stale-instance test) |
| 6 | BH | Privacy predicate written in gateway, view and templates | low | No named caller diverges today; AD-17 makes the gateway the guard and D04 only asks. reject |
| 7 | BH | D04 wording covers upload, not grading | low | Copy is the mockup's, frozen in the spec; changing it edits the spec. reject |
| 8 | BH | `request.language` ignored by prompts | low | Callers pass the stored `source.language` (`studymat/services.py:56`, `quiz/services.py:153`); a regenerated Summary or grading can drift language. **patch** |
| 9 | BH | XML-tag break-out in prompts lets a Student steer their own grade | low | Single-user self-study; the only victim is the Student. reject |
| 10 | BH | `add_source`/`_render_add_source` duplicate state and queries | low | One extra `remaining_today` query on one path; tests pass. reject |
| 11 | BH | «Prøv igjen» shown for `privacy_not_accepted` before acceptance | low | Retry can only fail again (uncounted). **patch** (hide retry until accepted) |
| 12 | BH | `rate_limited` copy wrong in grading | false | Text is «KI-tjenesten har mange forespørsler akkurat nå. Vent noen minutter og prøv igjen.», generic. reject |
| 13 | BH | `MAX_OUTPUT_TOKENS` "room for thinking" comment misleading; no live smoke test | false / low | Haiku 5.5 thinks adaptively by default when `thinking` is omitted; the real-Key check is the Author's manual step. reject |
| 14 | BH | Worst-case generation ~220 s | low | Spec's chosen timeouts (frozen); AD-5 stale is 5 min. reject |
| 15 | BH | Test helpers imported across test modules; `monkeypatch.undo()` | low | Cosmetic, no failing scenario. reject |
| 16 | BH | Weak prompt assertions ("medium", "one sentence") | low | Cosmetic test strength. reject |
| 17 | EC | Stored `privacy_not_accepted` message stays after acceptance | low | Link hides and retry shows after acceptance; changing the copy edits the frozen spec. reject |
| 18 | EC | Non-`APIError` SDK errors escape `_parse` | medium | `studymat/services.py:63` catches only `AIError`, so the request 500s and the Source stays generating until AD-5. **patch** |
| 19 | EC | Only the first text block is read | low | Structured output returns one text block. reject |
| 20 | EC | Stale D04 link under HTMX after acceptance navigates instead of swapping | low | Second-tab stale link only. reject |
| 21 | EC | Whitespace-only Locations send an empty `<source>` | false | Ingestion rejects text below `MIN_TEXT_CHARS`, so no such Source reaches generation. reject |
| 22 | EC | SDK debug logging (`ANTHROPIC_LOG=debug`) would log Source text | low | Opt-in developer setting, off by default. reject |
| 23 | EC | Refused/truncated grading shown as `grading_failed` | false | Frozen spec: only `key_rejected`, `rate_limited`, `privacy_not_accepted` are named in grading. reject |

## Design Notes

**Privacy before the counter.** AD-3 orders mode → privacy → counter → send, so a refused-by-privacy call never uses up the daily limit.

**One retry for generation, none for grading.** A transient 429/5xx on a counted call would otherwise cost the Student a Generation call on «Prøv igjen»; grading must stay under 15 s and falls back to «Ikke rettet».

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, with no network.
- `uv run python manage.py check` and `uv run python manage.py makemigrations --check` -- expected: no issues, no changes.

**Manual checks:**
- Author, with a real Key in `.env`: upload a short PDF, see D04 once, accept, get Study material; answer a Free-text Question; set a wrong Key and see «KI-tjenesten godtok ikke API-nøkkelen …». D04 at 360 px in light and dark.
