---
title: 'Topic score, Course score, Weak topics and Quiz history'
type: 'feature'
created: '2026-11-18'
baseline_commit: 'fc31a3b696e67009047c2fef2f0708cd5f8bdaf5'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Answers are graded and stored, but every mastery figure shows «Ikke nok data ennå», there are no Weak topics, and «Tidligere quizer» is always empty (CAP-10, CAP-8 history; FR-16, FR-17, FR-27).

**Approach:** Build the `progress` app on AD-10 (computed on read, nothing stored): Topic score, Course score and Weak topics. Show them in the fag-rail, fag-switcher, Hjem, Fagoversikt (P04) and under the Topic title (P05). Add D10 «Øv på svake temaer» (a Practice-mode Quiz from chosen Topics of one Course) and fill the quiz-history on P05's «Quiz» tab. The trend-label, «Siste 20 svar» and the tema-forecast-panel wait for story 13; the full spec is kept despite its size (Author's decisions 2026-11-18).

## Boundaries & Constraints

**Always:**
- **Rules (`progress/rules.py`, pure):** `WINDOW = 20`, `MIN_ANSWERS = 5`, `WEAK_BELOW = 60` (percent). A score is a whole percent, rounded half up; Weak means score `< 60`, so the shown figure and the tag always agree.
- **Topic score (`progress/services.py`):** the `quiz.rules.WEIGHTS` mean of the Topic's 20 most recent counted Answers (`answered_at` desc, then `id` desc). Counted: effective Grade (`Answer.objects.with_effective_grade()`, never `grade` directly) in correct/partial/incorrect, and Quiz kind not `retry`. Fewer than 5 → no score ("not enough data"), and never Weak. An Answer's Topic is `question.source.topic`. Overrides count at once; deleted Questions take their Answers with them (cascade).
- **Course score:** mean of the existing Topic scores in the Course (unrounded, then rounded); none → no score.
- **Weak topics:** Topics with a score `< 60`, lowest first (ties: creation order). One read function serves every page: e.g. `topic_scores(student, scope) -> dict[topic_id, TopicScore]`, with `courses.Scope`.
- **Fag-rail and fag-switcher:** the real Course score («61 %» and the filled `rail-meter`, «–» and the dotted meter without one); accessible name «mestring 61 % i snitt» or «mestring: ikke nok data ennå». Computed lazily in `web.context_processors`, like `shell_due`.
- **Hjem:** each course-row shows «Mestring 61 %» with a filled `mastery-meter` (or «Ikke nok data ennå»), a practice-tag «N temaer trenger øving» (or «1 tema trenger øving») when any Topic is Weak, and «Svakest: {tema} {score} %». Under the list: «Mestring for et fag er snittet av temaene som har nok svar.»
- **Fagoversikt (P04):** under the title, «Mestring 61 % i snitt» with a meter (or «Ikke nok data ennå»), and the same explaining line. Topic rows: Weak topics first, lowest first, then the rest in creation order; each shows «Mestring 45 %» with a meter or «Ikke nok data ennå», and the practice-tag «Trenger øving» when Weak. When there are Weak topics with ready Questions, a secondary «Øv på svake temaer (N)» (N = Weak topics) opens D10.
- **Tema (P05):** under the title, «Mestring 45 %» with the practice-tag when Weak, or «Ikke nok data ennå», and «Basert på de 20 siste svarene dine.».
- **D10** (`web`, GET dialog like D06 — full page normally, `#dialog` partial under HTMX; route under the Course): the topic-picker lists the Course's Topics that have ready Questions, Weak first (lowest first, preselected) then the rest in creation order; each row has the name, mastery and the Question count. Lead: «Temaene som trenger øving er valgt. Svakeste først.». Footer «{t} temaer valgt · {q} spørsmål», rendered for the preselection and updated by `app.js` on change. «Start quiz» POSTs; the Quiz holds every ready Question of the chosen Topics in random order, `course` = this Course, `return_url` = P04, idempotent on `start_token`. No Topic chosen → the form error «Velg minst ett tema.». Topics outside the Course or without ready Questions are ignored; none left → the same error.
- **Quiz history (P05 «Quiz» tab, «Tidligere quizer»):** every Quiz with a QuizQuestion from this Topic, newest first (`started_at`, then `id`). A row: the date in Oslo («18. nov.»), «Øv på feilene» when it is a Retry round, «{k} av {n} riktige» plus «· {p} delvis» when p > 0 (counts over the whole Quiz, from `quiz.services.result`), and the answer strip (the result-strip slot language, overridden Grades marked). The newest row, if it has misses, offers «Øv på feilene (N)» (POST to `quiz:retry`); every other row links «Se resultatet» (`quiz:result`). Under the list: «Runder med «Øv på feilene» teller ikke i mestringen.». No Quiz → the existing empty text. A Quiz with no Questions left is skipped.
- Imports follow AD-1: `progress` reads `quiz`, `web` reads `progress`; `quiz` never imports `progress`. Copy is bokmål via `core/messages.py` where it is reused; dates via `core.time`.

**Never:**
- Storing scores, a second score computation, or filtering on `Answer.grade` directly.
- The trend-label, answer-history («Siste 20 svar»), the tema-forecast-panel, forecasts, the next-step-band on Hjem/P04/P05, or Weak topics across all Courses (story 13 and deferred).
- Exam mode (story 15). Colouring mastery by level.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Seeded | Topics with Answers giving 40 %, 55 %, 80 % | Weak: 40 % then 55 %; 80 % not Weak | N/A |
| Too few | 4 counted Answers | «Ikke nok data ennå»; not Weak | N/A |
| Window | 25 counted Answers | only the 20 newest count | N/A |
| Retry | Retry-round Answers all correct | score unchanged | N/A |
| Not graded | `not_graded` or pending Answers | ignored | N/A |
| Override | partial → correct override | score rises at once | N/A |
| Course score | Topics 40 %, 80 %, one without data | 60 % | N/A |
| D10 | choose A and B of 3 Topics | Quiz holds only A's and B's ready Questions | N/A |
| D10 empty | nothing chosen | «Velg minst ett tema.», no Quiz | form error |
| D10 foreign | a Topic id of another Course or Student | ignored; if none left, the form error | N/A |
| History | Practice Quiz, then its Retry round | two rows, Retry newest and marked; only it may offer «Øv på feilene» | N/A |
| Not owned | another Student's Course on D10 | 404 | 404 |

</frozen-after-approval>

## Code Map

- `progress/` -- only `apps.py`; add `rules.py`, `services.py` (no models, no migration). Reads `quiz.models.Answer.objects.with_effective_grade()`, `quiz.models.QuizKind`, `quiz.rules.WEIGHTS`, `courses.models.Topic`, `courses.scope.Scope`.
- `quiz/services.py` -- `start_quiz(student, topic, n, start_token, return_url)` and `available_questions`: add a sibling (e.g. `start_quiz_from_topics(student, course, topic_ids, start_token, return_url)`) that shares the create/IntegrityError path; keep `start_quiz`'s behaviour. `result(quiz)` gives counts and rows for history rows; `missed(quiz)` for «Øv på feilene (N)». Add `topic_history(student, topic)` (Quizzes with a QuizQuestion in the Topic) here, since history is `quiz`'s (FR-27).
- `quiz/views.py` -- `retry` (POST) and `result` exist; D06 `start` is the pattern for D10 (form, `start_token`, `redirect_after_submit`, `render_page`).
- `quiz/forms.py` -- `StartQuizForm` pattern; D10's form (a `MultipleChoiceField` of Topic ids) can live in `web/forms.py`.
- `web/views.py` -- `home`, `course` (Topics), `topic` (tabs; the `quiz` branch adds history and the mastery line is for every tab). Add the D10 view; `web/urls.py` route like `courses/<int:course_id>/weak-quiz/`.
- `web/context_processors.py` -- `ShellDue` pattern; add lazy Course scores onto `shell_courses` (`c.score`).
- `templates/web/home.html`, `templates/web/course.html`, `templates/web/topic.html`, `templates/components/topic_row.html`, `fag_rail.html`, `fag_switcher.html` -- replace the «Ikke nok data ennå» / «–» placeholders.
- `templates/components/result_summary.html` -- the `result-strip` / `result-slot--{grade}` markup and CSS to reuse for the history strip; `templates/quiz/start.html` + `components/dialog.html` for D10.
- `static/css/components.css` -- `.mastery-meter`, `.rail-meter` exist (add a fill via an inline width or `--fill`); add `.practice-tag` (DESIGN.md: practice tokens, refresh icon), quiz-history rows, topic-picker rows. `static/icons/sprite.svg` for the icon.
- `static/js/app.js` -- add the D10 footer count update.
- `core/messages.py` -- new reused strings.
- Tests: `tests/test_shell.py`, `tests/test_topic_page.py` assert the old placeholders; update them. New `tests/test_progress.py` (rules and scores, FR-16/FR-17), `tests/test_weak_topic_quiz.py` (D10), `tests/test_quiz_history.py` (FR-27).

## Tasks & Acceptance

**Execution:**
- [x] `progress/rules.py`, `progress/services.py` -- constants, percent rounding, `topic_scores`, `course_scores`, `weak_topics` -- AD-10.
- [x] `quiz/services.py` -- `start_quiz_from_topics`, `topic_history` -- D10 and FR-27.
- [x] `web/forms.py`, `web/views.py`, `web/urls.py`, `templates/web/weak_quiz.html` -- D10.
- [x] `web/context_processors.py`, `fag_rail.html`, `fag_switcher.html`, `home.html` -- Course scores.
- [x] `web/views.py` `course` + `course.html` + `topic_row.html` -- P04 scores, order, «Øv på svake temaer (N)».
- [x] `web/views.py` `topic` + `topic.html` -- mastery line and quiz-history.
- [x] `static/css/components.css`, `static/icons/sprite.svg`, `static/js/app.js`, `core/messages.py` -- styles, icon, footer count, copy.
- [x] Tests listed in the Code Map, every I/O row covered; update tests that asserted placeholders.

**Acceptance Criteria:**
- Given seeded Answers giving 40 %, 55 % and 80 %, when the Student opens P04, then the first two rows are those Topics in that order with «Trenger øving», and «Øv på svake temaer (2)» is shown.
- Given a Grade override, when any page is reloaded, then every figure that includes that Topic reflects the new Grade.
- Given the fag-rail on any shell page, when a Course has a score, then its row shows the percent and its accessible name says «mestring {n} % i snitt».
- Given no Quizzes yet, when the «Quiz» tab opens, then it says «Du har ikke tatt en quiz i dette temaet ennå.» and no retry note.

## Implementation Notes

- Means are exact `Fraction`s (`progress/rules.py`), so half-up rounding never meets a float error (11.5/20 → 58 %).
- `progress.services.topic_scores` returns every Topic in scope (no-score ones included); `course_scores`, `course_score`, `weak_topics`, `weak_first` build on it. The shell attaches `course.mastery` (a `CourseScore`) inside the existing lazy `shell_courses`.
- Hjem shows «Svakest: …» for the lowest *scored* Topic whenever one has a score; a fag without any score shows no «Svakest» line.
- D10's footer count uses singular «1 tema valgt · {q} spørsmål» for one Topic (bokmål); foreign or not-ready Topic ids are dropped by `web.forms.LenientTopicsField`.
- `core.time.short_date` gives «18. nov.»; `{% message code k=v %}` now formats parameters.
- The history strip reuses `.result-slot`; an overridden Grade adds `.result-slot--overridden` (a dot under the slot) and «, endret av deg» in its accessible name.

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | VG | P04 hides «Øv på svake temaer» when Weak topics lack ready Questions, untested | low | Dropping the `any(ready…)` check fails no test; regeneration sets GENERATING (`courses/services.py:82`) | patch (test) |
| 2 | VG | D10 footer update in `app.js` never runs in a test | medium | No JS runner in the repo; listed as a manual check | defer |
| 3 | VG, BH | Hjem «Svakest» for a Course with scores but no Weak topic, untested | low | No Hjem test has every scored Topic ≥ 60 % | patch (test) |
| 4 | BH | Spec says in-review, sprint-status says in-progress | false | The workflow moves sprint-status to review in step 5 | reject |
| 5 | BH | `last_updated` format changed in sprint-status | low | Was `11-18-2026 19:12`, became `2026-11-18` | patch (restored) |
| 6 | BH | `sprite.svg` task ticked but unchanged; tag uses `refresh` not `i-practice` | false | `refresh` and `info` already exist; DESIGN.md specifies a refresh icon for the practice-tag | reject |
| 7 | BH | `test_shell.py`/`test_topic_page.py` not updated | false | Their «Ikke nok data ennå» assertions are the no-data case and still hold | reject |
| 8 | BH, ECH | D10 silently redirects when chosen Topics have no ready Questions at service time | low | `weak_quiz` returns `redirect_after_submit` when the service gives None; spec says the form error | patch |
| 9 | ECH | POST to D10 when no Topic is listed redirects without error | low | Nothing could be chosen; a race only; fix adds a branch | reject |
| 10 | BH, ECH | Button count N can exceed the preselected Topics | low | Only when a Weak topic is regenerating; spec defines N as Weak topics | reject |
| 11 | BH, ECH | Ownership `assert` in `start_quiz_from_topics` vanishes under `-O` | false | House pattern; the only caller loads the Course via `get_owned_or_404` | reject |
| 12 | BH, ECH | Quiz history unbounded with queries per Quiz | low | One Student's data; fix adds prefetch/paging | reject |
| 13 | BH | Scores computed several times per page; all Answers loaded | low | Small single-Student data; AD-10 accepts compute on read | reject |
| 14 | BH | P05 explain line lacks icon and shows with no data | low | The spec's line; cosmetic | reject |
| 15 | BH | Some copy bypasses `core/messages.py`; «{n} spørsmål» lacks singular | false | Spec requires messages only for reused copy; «spørsmål» is the same in singular and plural | reject |
| 16 | BH, ECH | `{% message %}` may leak `{n}` or raise on braces | false | Every call with placeholders passes params; texts without params are returned unformatted | reject |
| 17 | BH | Singular D10 footer not rendered in a test | low | No test preselects exactly one Topic | patch (test) |
| 18 | BH | Override test asserts "100 %" anywhere in main | low | Would pass if only one figure updated | patch (test) |
| 19 | BH | `CourseScore` frozen with a list; properties re-sort per access | low | Negligible cost; no named harm | reject |
| 20 | BH | Spec logs empty | false | Filled during this triage; deferred items are in the frozen Intent | reject |
| 21 | ECH | Retry offered on the newest Quiz while unfinished | false | Same as P07 (story 9), which offers the misses so far | reject |
| 22 | ECH | Multi-topic Quiz whose Retry round lacks this Topic: parent offers retry again | low | Retry rounds may repeat by design (FR-13); rare | reject |
| 23 | ECH | `answered_at` NULL sorts DB-dependently | false | `save_answer` always sets `answered_at` | reject |
| 24 | ECH | Empty `start_token` loses idempotency | low | The hidden field is always rendered; same as D06 | reject |

## Design Notes

Percent first, then compare: `pct = floor(mean * 100 + 0.5)`; Weak is `pct < 60`. A 59.6 % mean shows «60 %» and is not Weak, so a tag never sits beside «60 %».

Compute scores in one query per scope: fetch `(topic_id, effective_grade)` of counted Answers ordered `answered_at` desc, `id` desc, and keep the first 20 per Topic in Python. Data is one Student's, so this stays small.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, socket disabled.
- `uv run python manage.py check` and `uv run python manage.py makemigrations --check --dry-run` -- expected: no issues, no changes.

**Manual checks (if no CLI):**
- 360 px, light and dark: P04 rows with tag and meter, D10 checkboxes and footer, the history rows on the «Quiz» tab.
