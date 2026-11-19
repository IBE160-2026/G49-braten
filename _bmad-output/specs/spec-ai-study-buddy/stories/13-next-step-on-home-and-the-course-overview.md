---
title: 'Next step on Home and the Course overview'
type: 'feature'
created: '2026-11-19'
baseline_commit: '4f5aee843884bb778bae6756e24c1831b2c22bc8'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Hjem and Fagoversikt (P04) show no Next step, so the Student must work out what to do; the band exists only on P07 (CAP-11, FR-28).

**Approach:** Add `progress.next_step(student, scope)` (AD-10) that applies the fixed FR-28 order and returns one band or a calm-message, rendered by `components/next_step_band.html` right after the title on Hjem (all fag) and P04 (one fag), plus the UX quiz band on P05. On Hjem, rule 2 sends the Student to D10 of the fag with the weakest Weak topic. The forecast-chart is story 13b; trend, «Siste 20 svar» and the tema-forecast-panel are story 13c (Author's decisions 2026-11-19).

## Boundaries & Constraints

**Always:**
- **Result:** `NextStep(number, unit, heading, why, minutes, button_label, action_url, method="get")`, `Calm(text)` or `None`. `why` is safe HTML with numbers in `<b>`; every `action_url` is a GET page or dialog, never a mutating endpoint.
- **Order (first that applies, within the scope):**
  1. **Due cards** (`review.services.due_cards`, the only definition): «{n}» «kort» · Hjem «Repeter dagens kort», why «{n} kort forfaller i dag: Databaser 9 og Statistikk 5.» (per fag); P04 «Repeter kortene i {fag}», why per tema («… : Normalisering 5, Transaksjoner 3 og Grunnleggende SQL 1.»). Parts sorted by count desc, then name; joined with `quiz.rules.join_with_og`. Button «Start repetisjon» → `review:start` (P04 with `course`), `next` = this page.
  2. **Weak topics with ready Questions** (`progress.services`; a Weak topic with no ready Question does not count): P04 «{q}» «spørsmål» (ready Questions in those Topics) · «Øv på de svake temaene» · «2 temaer trenger øving: Normalisering 45 % og Transaksjoner 55 %.» (lowest first; «1 tema trenger øving: …»). Hjem: the fag of the lowest such Topic (ties: fag creation order) · «Øv på de svake temaene i {fag}» · «{t} temaer trenger øving i alle fag. Svakest: {tema} {score} %.» (singular «1 tema …»), `{q}` counted in that fag. Button «Øv på svake temaer» → that fag's `web:weak_quiz` (D10).
  3. **A Topic without Sources** (first by fag creation order, then Topic creation order): «1» «kilde» · «Legg til kilde i {tema}» · Hjem «{tema} i {fag} har ingen kilder ennå.», P04 «{tema} har ingen kilder ennå.» · button «Legg til kilde» → `studymat:add_source` (which shows D04 first when needed).
  4. **Otherwise** `Calm`: Hjem «Ingen kort i dag. Neste kort kommer {dato}.», P04 «Ingen kort i {fag} i dag. Neste kort kommer {dato}.» with `review.services.next_due_date` for the scope; no date → «Ingen kort i dag. Ingen flere kort er planlagt.» (P04: «Ingen kort i {fag} i dag. …»). `{dato}` as «19. november».
- **No band:** Hjem with no fag; P04 with no Topics (the empty-states carry the action).
- **Minutes** (`progress/rules.py`): `CARD_MINUTES = 0.8`, `QUESTION_MINUTES = 0.8`, `SOURCE_MINUTES = 2`; «ca. {m} min» with `m = ceil(count × rate)` via the existing `band_minutes` message.
- **P05 band** (only when the Topic has ready Questions): «{d}» «spørsmål» (`d` = D06's default count) · «Ta en quiz i {tema}» · why: Weak «Mestring 45 %, så temaet trenger øving. {n} spørsmål er klare.»; scored «Mestring 80 %. {n} spørsmål er klare.»; no data «{n} spørsmål er klare.» · button «Start quiz» → `quiz:start` (D06). Without ready Questions, no band (the tabs' empty-states carry the action).
- **One primary per page:** the band's button is the only primary; nothing else on Hjem, P04 or P05 uses `button-primary` while a band shows.
- **Hjem rows** also show «{n} kort i dag» (or «Ingen kort i dag») from `shell_courses.due_today`.
- Imports per AD-1 (`web` → `progress` → `quiz`, `review`); copy in `core/messages.py`; one call per page (no other band logic in `web`).

**Never:**
- The forecast-chart, return-forecast, trend-label, answer-history, tema-forecast-panel (13b, 13c); a cross-fag Quiz; storing anything; a band button that POSTs.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Due and Weak | Due cards and Weak topics | rule 1 (Review) | N/A |
| Weak only | no Due cards, Weak topics with ready Questions | rule 2 (D10) | N/A |
| Weak without Questions | Weak topic whose Sources are generating, nothing else | not rule 2; next rule applies | N/A |
| Topic without Sources | nothing due, no Weak topics, an empty Topic | rule 3, first by creation order | N/A |
| Calm with date | nothing applies, a card due in 3 days | calm-message with that date | N/A |
| Calm without date | no cards at all | «… Ingen flere kort er planlagt.» | N/A |
| Scope | Due cards only in another fag | P04 of this fag: not rule 1 | N/A |
| Hjem Weak across fag | fag A weakest 55 %, fag B weakest 40 % | button → D10 of B; why counts both | N/A |
| Empty | Hjem with no fag; P04 with no Topics | no band | N/A |
| P05 | Topic with 28 ready Questions, score 45 % | «10» · «Ta en quiz …» · Weak why | N/A |

</frozen-after-approval>

## Code Map

- `progress/services.py` -- `topic_scores`, `weak_of`, `weak_first`, `course_scores` exist (story 12); add `next_step`, `NextStep`, `Calm` here (or `progress/next_step.py`). `progress/rules.py` -- add the minute rates.
- `review/services.py` -- `due_cards(student, scope)`, `due_count_by_course`, `next_due_date(student, scope)`; group `due_cards(...)` by `flashcard__source__topic` for P04's why.
- `quiz/rules.py` -- `join_with_og`. `quiz/forms.py` -- `default_count(available)` for P05's number.
- `web/views.py` -- `home`, `course`, `topic`: pass `next_step` into the context; `_ready_question_counts` exists (move or reuse for rule 2 counts in `progress`).
- `templates/components/next_step_band.html` -- takes a dict; `method == "get"` renders a link. Pass `NextStep` (same attribute names). `templates/quiz/result.html` -- calm-message markup (`<p class="calm-message">{% icon "ok" %}<span>…</span></p>`).
- `templates/web/home.html`, `course.html`, `topic.html` -- band right after the title (`topic.html` has the comment «The band comes with the Next step (story 13).»).
- `core/messages.py` -- `band_minutes` exists; add the band texts.
- Tests: new `tests/test_next_step.py` (every matrix row, FR-28 named); update `tests/test_shell.py` / `tests/test_topic_page.py` / `tests/test_progress.py` only where they break.

## Tasks & Acceptance

**Execution:**
- [x] `progress/rules.py`, `progress/services.py` -- `next_step` with the four rules, both scopes, and the P05 quiz band.
- [x] `core/messages.py` -- band and calm texts.
- [x] `web/views.py`, `templates/web/home.html`, `course.html`, `topic.html` -- render the band or calm-message after the title; Hjem rows' due count.
- [x] `tests/test_next_step.py` -- every matrix row, plus one-primary and the GET-only URL.

**Acceptance Criteria:**
- Given any state, when Hjem or P04 renders, then it holds at most one `next-step-band` or calm-message and at most one `band-button`, and no other `button-primary`.
- Given the band on Hjem with Due cards, when its button is followed, then P09 starts with all fag's Due cards and «Avslutt» returns to Hjem.
- Given P04 rule 2, when its button is followed, then D10 opens with the Weak topics preselected.

## Implementation Notes

- `progress.services.next_step(student, scope)` handles all three pages: `Scope.all()` (Hjem), one fag (P04), one tema (P05 quiz band). `NextStep`/`Calm` carry `is_calm` so templates branch without type checks.
- `_ready_question_counts` moved from `web/views.py` to `progress.services.ready_question_counts(student, scope)`; P04 and D10 now use it.
- Minutes use an exact `Fraction` (`progress.rules.band_minutes`), so 35 × 0.8 is 28, not 29.
- `core.time.long_date` gives «19. november» for the calm-message.
- The band button is a plain link (no `hx-get`), so D06, D10 and D05/D04 open as full pages from the band.
- P05 why uses «1 spørsmål er klart.» when one Question is ready (`_one`/`_other` keys).

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | BH, ECH | Rule 1's `review:start` link writes a Review on GET | false | Story 11's design: a Review starts on GET and is reused while open (`review.services.start`), so a repeat or prefetch adds nothing; AD-10 requires a GET page, which it is | reject |
| 2 | BH | GET-link test accepts any 200/302 | low | Would pass on a redirect to sign-in; unlikely, the client is signed in | reject |
| 3 | BH | Hjem Weak tie-break relies on unordered `Course` query; same-fag ties unproven | false | `Course.Meta.ordering = ["created_at", "id"]`; `topic_scores` iterates Topics by creation and `weak_of` sorts stably | reject |
| 4 | BH, VG | Escaping of names in the band never tested | low | All test names are plain words; a `.format` refactor would pass | patch (test) |
| 5 | BH | Hjem with fag but no Topics shows a calm-message | low | FR-28 has no rule for it; the fag rows and «Nytt tema» on P04 remain | reject |
| 6 | BH | Rule 3 counts failed or generating Sources | false | The rule is «a Topic without Sources» (glossary, FR-28); such a Topic has a Source and its row shows the status | reject |
| 7 | BH | P05 «1 spørsmål er klare.» | low | Ungrammatical for one Question; a direct correction | patch |
| 8 | BH | Spec in-review, sprint-status in-progress; empty triage log | false | The workflow moves sprint-status in step 5 and fills the log now | reject |
| 9 | BH | Deferred 13b/13c entries have `source_spec: none` | false | The split format in step 1 prescribes `none` | reject |
| 10 | BH | Unused imports in `web/views.py`; repeated queries; no query-count test | false / low | `ruff --select F401` is clean (`Question`, `Status` still used); repeated reads are small for one Student | reject |
| 11 | BH | Band/calm markup copied into three templates; float rates; preformatted `minutes` | low | Duplication of one line; no named harm | reject |
| 12 | VG | Precedence of rules 1 and 2 over rule 3 untested | medium | Reordering the `or` chain passes every test | patch (test) |
| 13 | VG | Name tie-break in rule 1's parts untested | low | All test counts differ | patch (test) |
| 14 | ECH | Name sort is code-point, not locale (Æ/Ø/Å, case) | low | Only on equal counts with such names; fix adds locale handling | reject |

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, socket disabled.
- `uv run python manage.py check` and `uv run python manage.py makemigrations --check --dry-run` -- expected: no issues, no changes.

**Manual checks (if no CLI):**
- 360 px, light and dark: the band on Hjem, P04 and P05 (button on its own row), and the calm-message.
