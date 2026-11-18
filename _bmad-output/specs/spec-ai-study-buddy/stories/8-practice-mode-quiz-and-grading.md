---
title: 'Practice-mode Quiz and grading'
type: 'feature'
created: '2026-11-17'
status: 'done'
baseline_commit: 'cd0206f9e3bcede6a1f9b199d83e171814d8617f'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** P05 counts a Topic's Questions, but the Student cannot practise them. There is no Quiz, no Answer and no Grade (CAP-7, FR-10–12).

**Approach:**
- Add Quiz, QuizQuestion and Answer in `quiz`.
- D06 «Start quiz» draws N random ready Questions.
- P06 shows one Question per page, with a Hint on request and feedback after each Answer.
- Multiple-choice is graded in code. Free-text is graded through `ai.gateway.grade_free_text` (a Mock word-overlap rule until story 10).
- A failed grading gives «Ikke rettet» with a retry.

## Boundaries & Constraints

**Always:**
- **Models.** Every model has a non-null `student` (AD-7) and cascades from Question and Source (AD-8).
  - `Quiz(course, kind=practice, started_at, return_url, start_token)`, with `start_token` unique per student.
  - `QuizQuestion(quiz, question, position)`.
  - `Answer(quiz, question, chosen_index|text, grade, override_grade, explanation, is_mock, failure, answered_at)`, unique on `(quiz, question)`. A null `grade` means pending.
  - The Grade enum `correct/partial/incorrect/not_graded` and the weights 1/0.5/0 go in `quiz/rules.py`.
  - `Answer.objects.with_effective_grade()` is `Coalesce(override_grade, grade)`. The override UI is story 8b.
- **Writes go only through `quiz/services.py`.**
  - `start_quiz` is idempotent on the token. Questions come from ready Sources only, in random order, and n is clamped to the number available.
  - `save_answer` keeps the first write and sets `answered_at` once.
  - `regrade` regrades with the same text.
  - Grading runs synchronously, outside any transaction (AD-19).
- **D06** opens from «Velg antall og start» on the Quiz tab. It is a `#dialog` GET/POST like `courses/delete.html`.
  - Title «Start quiz i {tema}», label «Antall spørsmål».
  - Presets «5», «10», «20», «Alle {n}», capped at n. The default is 10, or n if lower.
  - «{n} spørsmål tilgjengelig. Flervalg og fritekst blandes.»
  - Buttons «Avbryt» and «Start quiz».
- **P06** is `quizzes/<id>/<position>/`, a full page (AD-13).
  - The session bar has «Avslutt» (to `return_url`), «{i} av {N}» and «{tema} · øving».
  - Below it: the chip «Flervalg» or «Fritekst», the prompt, and «Vis hint» as a `<details>`.
  - Multiple-choice shows four native-radio option rows A–D, where keys 1–4 select. Free-text has a «Ditt svar» field. Then the button «Svar».
  - The answer POST swaps `#question-card` under HTMX, or redirects without JS.
  - Focus moves to the feedback heading. The panel is `aria-live="polite"`.
  - A reload shows the stored Answer locked, with its feedback.
- **Feedback panel**
  - The Grade is shown as an icon and a word: «Riktig», «Delvis riktig», «Feil» or «Ikke rettet».
  - Then the Explanation, then the Reference (`components/reference.html`).
  - Multiple-choice: the tags «Ditt svar» and «Riktig svar» and the chosen option's explanation. A wrong Answer starts with «Riktig svar er {bokstav}.»
  - Free-text: «Vis fasit» shows the model answer. A «Demo» chip appears when `is_mock`.
  - The button is «Neste spørsmål». On the last Question it is «Fullfør quiz».
- **Ikke rettet.** Any `AIError` saves `grade=not_graded` with `failure` set to the error code.
  - An assertive inline message shows «Kunne ikke rette svaret fordi KI-tjenesten ikke svarte. Prøv igjen.» For `key_rejected` it shows E:303.
  - «Prøv å rette igjen» runs `regrade`.
- **End of the quiz** (Author's decision 2026-11-17). Once every Question is answered, resume and «Fullfør quiz» go to `return_url` (`?tab=quiz`). The Quiz tab then shows «Quizen er lagret. {k} av {N} riktige.», where k counts the effective Grades that are `correct`. Story 9 replaces this with P07.
- **Modes.** Mock mode grades Free-text with the word-overlap rule (Design Notes), uncounted, with `is_mock` set. Real mode raises `ProviderUnavailable` until story 10, which shows «Ikke rettet».
- **Copy** is in bokmål. New codes go in `core/messages.py`.

**Never:**
- The Grade override and «Slett spørsmålet» (story 8b, Author's decision 2026-11-17).
- P07, Retry rounds (story 9), scores, history and the band (stories 12–13), Exam mode.
- Counting grading toward the daily limit (AD-3).
- An AI call for multiple-choice.
- Moving on automatically.
- `hx-confirm`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Start | Sample ready (11 Q), POST n=10 | Quiz with 10 distinct ready Questions → P06 position 1 | N/A |
| Double start | same `start_token` twice | one Quiz; both → same P06 | N/A |
| n too large | n=50 | clamped to 11 | N/A |
| MC right / wrong | POST option | «Riktig» / «Feil» + «Riktig svar er …», no gateway call | N/A |
| Free-text mock | text sharing model-answer words | Grade by rule, «Demo», «Vis fasit» | N/A |
| Empty answer | no option / blank text | 200 inline «Velg et svar først.» / «Skriv et svar først.», nothing saved | inline |
| Grading fails | gateway raises AIError | `not_graded`, message, «Prøv å rette igjen» → regrade | inline |
| Resubmit | second answer POST | first Answer kept and shown | N/A |
| Abandon | «Avslutt» after 3 of 10 | 3 Answers stay saved | N/A |
| Finish | last answered → «Fullfør quiz» | Quiz tab with «Quizen er lagret. k av N riktige.» | N/A |
| Not owned / bad position | other Student's quiz; position not in quiz | 404 | 404 |
| Question deleted | Question gone mid-quiz | its QuizQuestion and Answer gone; N drops; navigation skips the gap | N/A |

</frozen-after-approval>

## Code Map

- **`ai/gateway.py:55` `grade_free_text`** is a stub today. Model it on `_counted`:
  - Keep the `in_atomic_block` assert, the logging and the `_send_*` pattern.
  - Leave out `_count_call` and the `is_sample`/`NeedsKey` gate.
- **`ai/schemas.py`**: add `GradeRequest(prompt, model_answer, answer, source_text, language)` and `GradeResponse(grade: Literal[correct, partial, incorrect], explanation)`, lower-cased (AD-2). **`ai/mock/__init__.py`**: add `grade(request)`. **`ai/errors.py`**: do not add codes, because `courses.FailureReason` must equal them.
- **`tests/test_ai_gateway.py:217`**: remove `grade_free_text` from the test of operations not yet built.
- **`quiz/`** is new: models, rules, services, views, urls, and `migrations/` (`0001` depends on studymat `0001`). Mount it in `config/urls.py`.
  - `quiz` may import `studymat`, `courses`, `ai` and `core`, never `web` or `progress` (`tests/test_import_graph.py` GRAPH).
- **`studymat/models.py:70` `Question`** has `options`, `correct_index`, `model_answer`, `hint`, `location_index` and `quote`. `studymat.services.locations(source)` gives the Source text at the Reference.
- **`core/`**:
  - `http.render_page(partials=…)`, `redirect_after_submit`, `safe_next`, `vary_on_htmx`.
  - `ownership.get_owned_or_404`.
  - `time.now()`.
  - `messages.py`: `{% message %}` raises on a missing code.
- **`web/views.py:83` `topic`** and **`templates/web/topic.html:25-40`**: the Quiz panel gets the «Velg antall og start» button (`hx-get` into `#dialog`). The finish note is read through a `quiz.services` function (`web` may import `quiz`); an unknown or not-owned id gives no note.
- **Templates**:
  - Reuse `dialog.html`, `inline_message.html`, `reference.html` and `segmented_control.html`.
  - Add `session_bar.html`, `option_row.html` and `feedback_panel.html`.
- **`static/js/app.js`**: delegated listeners only. Keys 1–4 in `.option-group`; after a swap into `#question-card`, focus `[data-focus-on-swap]`.
- **`static/css/components.css`**: the option row, feedback panel and session bar, using the DES ok/part/bad tokens.
- **Tests**: copy the fixtures `sample` (`tests/test_generation.py:86`), `ready_source` (`tests/test_topic_page.py:52`) and `freeze_now`.

## Tasks & Acceptance

**Execution:**
- [x] `ai/schemas.py`, `ai/mock/__init__.py`, `ai/gateway.py` -- add the grade schemas, the mock rule and `grade_free_text` -- the AI boundary for FR-12.
- [x] `quiz/models.py`, `quiz/rules.py`, `quiz/migrations/0001_initial.py` -- add the models, the Grade enum and weights, and `with_effective_grade` -- the data for CAP-7.
- [x] `quiz/services.py` -- add `start_quiz`, `save_answer` (multiple-choice graded in code; free-text through the gateway with the Source text at the Reference), `regrade`, `next_position` and `finish_note` -- the only write path.
- [x] `quiz/views.py`, `quiz/urls.py`, `config/urls.py` -- add the D06 start, P06 GET, the answer and regrade POSTs, and resume `quizzes/<id>/` (first unanswered position, else `return_url`) -- every lookup owned (404).
- [x] `templates/quiz/*.html`, `templates/components/{session_bar,option_row,feedback_panel}.html`, `templates/web/topic.html` -- add D06, P06 with a `{% partialdef card %}`, and the Quiz-tab button and note.
- [x] `core/messages.py`, `static/js/app.js`, `static/css/components.css` -- add the copy, the keys and focus handling, and the styles.
- [x] `tests/test_quiz.py`, `tests/test_grading.py`, `tests/test_ai_gateway.py` -- cover:
  - every I/O matrix row;
  - the mock-rule thresholds;
  - that grading is not counted against the daily limit;
  - that multiple-choice makes no gateway call (a patched sender asserts it);
  - `student` set on each model;
  - `with_effective_grade`;
  - that the import graph still passes.

**Acceptance Criteria:**
- Given a ready Sample Topic, when the Student opens the Quiz tab, then «Velg antall og start» opens D06 with «Alle 11».
- Given Real mode, when a Free-text Answer is submitted, then the Answer text is saved and shows «Ikke rettet» with the message.
- Given Mock mode, when a Free-text Answer is graded, then the gateway's daily count is unchanged.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Pass 1 (iteration 0) — Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG).

| # | Source | Finding | Verdict | Evidence / route |
|---|--------|---------|---------|------------------|
| 1 | BH, EC | Non-AIError in `_grade_free_text` (request built outside `try`) leaves `grade=None` and 500s | medium | Only `AIError` caught; Answer row already committed. **patch** |
| 2 | BH, EC×2 | Concurrent second POST / regrade sees in-flight `grade=None` as «Ikke rettet» and can grade twice | medium | Real only for non-HTMX double submit; Mock grades instantly, Real arrives in story 10 (15 s window). Needs a pending state the spec does not define. **defer** |
| 3 | BH | `is_mock` read from `gateway.mode()` after the call | false | `mode()` reads `settings.AI_PROVIDER`, fixed for the process; it cannot differ within one request. reject |
| 4 | BH, EC | Free-text answer has no length limit | low | Mock ignores length; the cost only exists with story 10's Real adapter, and a limit adds a new message. reject (note for story 10) |
| 5 | BH | Mock rule gameable, counts stopwords, no stemming | false | The rule is exactly the spec's Design Notes (AD-4 "fixed rule"); changing it edits the spec. reject |
| 6 | BH, EC, VG | `start_token` missing → new UUID; token reused across Topics returns other Quiz | low | Token is a server-made uuid4 rendered in every D06; only a crafted POST hits it. reject |
| 7 | BH | `_source_text` loads all Locations | low | One Source's rows, once per free-text answer; negligible. reject |
| 8 | BH | Non-HTMX inline error gives no focus target | low | `autofocus` suppressed when `error`; `data-focus-on-swap` is HTMX-only. **patch** |
| 9 | BH, VG | Untested: out-of-range `choice`, regrade on graded Answer, D06 invalid count, regrade ownership | medium | VG pre-verified gaps; guards removable without failing tests. **patch** |
| 10 | BH, VG | `app.js` keys 1–4 / Enter / afterSettle focus untested | medium | No JS/browser runner in repo. **defer** |
| 11 | BH | Finish note counts only `correct`, ignores partial/not graded | false | Frozen decision: «k counts effective Grades that are `correct`». reject |
| 12 | BH | Option-row selected state invisible in forced-colors | low | Radio `opacity:0`, state only via background/border. **patch** |
| 13 | BH | `assert` used for ownership/transaction guards | low | Same pattern as `studymat.services.delete_item` and `_counted`; views already 404 first. reject |
| 14 | BH | No `GradeRequest` constraints | false | AD-2 forbids length/numeric constraints on schemas. reject |
| 15 | BH | Three position queries per render | low | Tiny queries per page. reject |
| 16 | BH | `failure` max_length 24 may not fit codes | false | Longest code `privacy_not_accepted` is 20 chars. reject |
| 17 | BH | Test name `not_yet_built_operations` not narrowed | low | Cosmetic. reject |
| 18 | EC | IntegrityError from FK (Question deleted mid-start) → `Quiz.DoesNotExist` 500 | low | Needs a delete in the same instant as start; single-user app. reject |
| 19 | EC | `refresh_from_db` after cascade delete → 500 | low | Same race window as 18. reject |
| 20 | EC | `all_positions.index` ValueError if QuizQuestion deleted mid-request | low | Same race window. reject |
| 21 | EC | MC with `correct_index=None` grades None==None as correct | false | `studymat.checks.question_ok` drops MC without 4 options and a valid `correct_index` before saving. reject |
| 22 | EC | MC with empty options can never be answered | false | Same `question_ok` guard. reject |
| 23 | EC | `?quiz=<id>` of another Topic shows its note | low | Only the Student's own Quizzes, via a hand-edited URL. reject |
| 24 | EC | SourceText kinds sharing an index give wrong grading context | maybe-false | Would need a Source whose heading and paragraph share an index; Mock ignores `source_text`; if true only low. reject |

## Design Notes

**Mock grading rule (AD-4).**
- Lower-case words of at least 3 letters (Æ/Ø/Å included).
- overlap = |answer ∩ model| / |model|.
- An overlap of at least 0.6 is correct, at least 0.3 is partial, and anything lower is incorrect.
- Explanation: «Demo-vurdering: {k} av {m} nøkkelord fra fasiten finnes i svaret ditt.»
- The rule applies to every Source, because `NeedsKey` would strand Questions generated in Real mode.

**`Answer.failure`.** It stores the code, so a reload shows the same message. A null `grade` at render time (a crash mid-request) is shown as `not_graded` with `provider_unavailable`.

**Navigation.** Positions are fixed, but deleting a Question leaves gaps, so «Neste» goes to the next existing position. A Quiz with nothing left sends resume to `return_url`.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, with no network.
- `uv run python manage.py makemigrations --check` and `uv run python manage.py check` -- expected: no changes and no issues.

**Manual checks:**
- At 360 px in light and dark: D06 → P06, keys 1–4 and Enter, focus on the feedback heading, «Vis hint», «Avslutt», and the finish note.
