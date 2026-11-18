---
title: 'Quiz result and Retry round'
type: 'feature'
created: '2026-11-18'
status: 'done'
baseline_commit: 'd0bc3ce69095821c9abf4cd189961d7fdfc44914'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A finished Quiz only leaves a one-line note on the Quiz tab. The Student cannot see every Grade, and cannot practise what they missed (CAP-8, FR-13).

**Approach:** Add P07 «Resultat»: the score, a strip and one expandable row per Question, plus a next-step-band «Øv på feilene (N)» that starts a Retry round of exactly the incorrect and partially correct Questions. Retry rounds repeat from their own P07 until all are correct. P07 replaces story 8's finish note. Acting on P07 rows in place is story 9b (Author's decision 2026-11-18).

## Boundaries & Constraints

**Always:**
- **Model (AD-9).** `Quiz` gains `parent_quiz` (nullable FK to self, CASCADE) and the kind `retry`. Migration `0002`.
- **Membership.** `quiz.services.start_retry(student, quiz)` takes the parent's Questions whose effective Grade (`with_effective_grade()`) is `incorrect` or `partial`, in the parent's position order (no shuffle). Not graded, pending and unanswered Questions are left out. It reuses the parent's Retry round that has no Answers yet, else creates one, and returns None when nothing is missed. The round copies `course` and `return_url`.
- **URLs.** `quizzes/<id>/result/` (GET, P07, a full page) and `quizzes/<id>/retry/` (POST → the round's first position; nothing missed → P07). Owned or 404.
- **End of a Quiz.** «Fullfør quiz», and resume with every Question answered, go to P07. «Avslutt» still goes to `return_url`. Remove `finish_note`, `finished_url`, `FINISHED_PARAM`, the Quiz-tab note and the unused `quiz_saved` message.
- **P07.** Session bar with «Avslutt» and the context «Resultat», no progress strip. Title «Resultat». Then:
  - **Band**, when anything is missed: «{N} spørsmål» · «Øv på feilene» · «Spørsmål 3, 4 og 5 var feil eller delvis riktige. Runden teller ikke i mestringen.» · «ca. {ceil(0.8·N)} min» · button «Øv på feilene ({N})» (POST to retry). The numbers are display numbers (1-based order among the remaining Questions), joined with «og».
  - **All correct** (every Question answered with effective Grade `correct`): no band; «Alle svarene var riktige.»
  - **result-summary:** «{k} av {N}» (k counts effective `correct`), the lead «{a} riktige, {b} delvis riktige og {c} feil.» (zero counts left out), and a strip of numbered slots tinted by Grade (unanswered dashed, not graded neutral), each linking to its row `#q-{number}`.
  - **Rows:** one `<details>` per Question with number, Grade word and prompt. Open, it shows story 8's feedback panel read-only (Grade, «Endret av deg»/«KI-vurdering», Explanation, Reference, «Vis fasit»; no menu, retry, delete or next), and a link «Åpne spørsmålet» to its P06 position. Unanswered: «Ikke besvart». Not graded adds «Spørsmålet er ikke med i «Øv på feilene» før det er rettet.»
  - «Tilbake» at the foot → `return_url`.
- **Retry round on P06.** The session-bar context reads «Øv på feilene», and a note under it says «Denne runden teller ikke i mestringen.» Otherwise story 8's P06.
- **Copy** in bokmål; new codes in `core/messages.py`.

**Never:**
- Override, regrade or delete inside P07 rows (story 9b).
- Scores, mastery, the mastery link on P07, quiz-history (stories 12–13), Exam mode, P11.
- Any gateway call or daily-limit count.
- Bands on other pages (story 13); build P07's band as a reusable component only.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Finish | last Question answered → «Fullfør quiz» | P07 «7 av 10», band «Øv på feilene (3)» | N/A |
| Start retry | 2 incorrect, 1 partial, 1 not graded | round of the 3 in parent order, `parent_quiz` set | N/A |
| Double click | retry POST twice before answering | same round | N/A |
| Retry of retry | round finished with 1 miss | its P07 offers «Øv på feilene (1)»; parent = that round | N/A |
| All correct | every effective Grade correct | no band, «Alle svarene var riktige.» | N/A |
| Override counts | missed Free-text overridden «Riktig» on P06 | not in the band count or the round | N/A |
| Abandoned | 3 of 10 answered, open P07 | 7 rows «Ikke besvart», dashed slots, not in the round | N/A |
| Nothing missed POST | retry POST with no misses | redirect to P07, nothing created | N/A |
| Not owned | other Student's result/retry | 404 | 404 |

</frozen-after-approval>

## Code Map

- `quiz/models.py:23` `QuizKind`, `Quiz` -- add `RETRY = "retry"` and `parent_quiz` (`related_name="retry_rounds"`); `quiz/migrations/0002_*`.
- `quiz/services.py` -- add `missed(quiz)` (shared by band and retry), `start_retry`, and `result(quiz)` (rows, counts, display numbers). Reuse `positions` and `with_effective_grade`. Remove `finish_note`/`finished_url`/`FINISHED_PARAM` (~lines 25–28, 178–200).
- `quiz/views.py` -- `resume` and `_context["next_url"]` go to `quiz:result` when all are answered. Add `result` and `retry` views (`require_safe`/`require_POST`, `_owned`). `_context` sets `context_label` «Øv på feilene» and a `retry_note` for kind `retry`.
- `templates/components/feedback_panel.html` -- a `readonly` input hides the override menu, retry form, delete link and next button.
- `templates/quiz/result.html` (new) -- full page; reuse `session_bar.html` (no slots), `feedback_panel.html` (readonly), `reference.html`.
- `templates/components/next_step_band.html`, `result_summary.html` (new) -- per DESIGN.md «next-step-band» and «result-summary». The `band*` tokens exist in `static/css/tokens.css:24-28`; check `score` and add only what is missing.
- `templates/quiz/question.html`, `session_bar.html` -- the retry note.
- `web/views.py:123`, `templates/web/topic.html:26` -- remove the finish note.
- Tests that change: `tests/test_quiz.py:352-372` (finish note → P07 score, keep the override-counts check), `tests/test_grade_override.py:281-290` (`finished_url` → P07).
- Do not touch `ai/`, `studymat/`, `courses/`.

## Tasks & Acceptance

**Execution:**
- [x] `quiz/models.py`, `quiz/migrations/0002_*` -- `parent_quiz` and kind `retry`.
- [x] `quiz/services.py` -- `missed`, `start_retry`, `result`; remove the finish note.
- [x] `quiz/views.py`, `quiz/urls.py` -- P07, the retry POST, the end-of-quiz route, the retry label.
- [x] `templates/quiz/result.html`, `templates/components/{next_step_band,result_summary,feedback_panel,session_bar}.html`, `templates/quiz/question.html`, `templates/web/topic.html`, `web/views.py` -- P07, the band, readonly panel, the retry note, the finish note removed.
- [x] `core/messages.py`, `static/css/components.css` -- copy and styles.
- [x] `tests/test_result.py` (new), `tests/test_quiz.py`, `tests/test_grade_override.py` -- every matrix row, reuse of an unanswered round, band copy and minutes, display numbers after a delete, the import graph.

**Acceptance Criteria:**
- Given a Retry round, when P06 opens, then the session bar reads «Øv på feilene» with the note «Denne runden teller ikke i mestringen.».
- Given an abandoned Quiz, when «Avslutt» is pressed, then the Student lands on `return_url`, not P07.
- Given a P07 row, when it is opened, then it shows no «Endre vurdering», «Prøv å rette igjen» or «Slett spørsmålet», and «Åpne spørsmålet» leads to its P06 position.

## Implementation Notes

- A reused unanswered Retry round has its Questions replaced by the parent's current misses (an override on P06 may have changed them).
- Concurrent retry POSTs: per-parent token `retry-{parent}-{n}` on the existing `(student, start_token)` constraint.
- Singular copy added: «Spørsmål 2 var feil eller delvis riktig.», «1 riktig», «1 delvis riktig».
- A Quiz with every Question deleted: P07 redirects to `return_url`.
- Not-graded reason in P07 rows is plain text, not `role="alert"`, so several rows do not each announce.
- Below 600 px the session context is forced visible on result pages so «Resultat» shows.

## Spec Change Log

## Review Triage Log

Pass 1 (iteration 0) — Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG).

| # | Source | Finding | Verdict | Evidence / route |
|---|--------|---------|---------|------------------|
| 1 | BH, EC×2, VG | `IntegrityError` fallback fetches any Quiz with the token (a crafted D06 token, or a non-token IntegrityError → DoesNotExist 500) | low | D06 accepts client tokens up to 64 chars; only the Student's own data. Direct fix: filter `kind`/`parent_quiz`, `.first()`, re-raise. **patch** |
| 2 | BH, VG | IntegrityError recovery path never runs in a test | medium | VG pre-verified: the double-click test takes the reuse branch. **patch** |
| 3 | VG | «Fullfør quiz» → resume fallback (earlier position unanswered) untested | medium | VG pre-verified: dropping `issuperset` fails nothing. **patch** |
| 4 | VG | Strip-slot click opening a row (app.js) only source-checked | medium | No JS runner in repo. **defer** |
| 5 | BH | Retry rounds not excluded from mastery/history | false | Mastery and history do not exist yet (stories 12–13); no query to exclude from. reject |
| 6 | BH, EC | Reuse branch `_set_questions` not locked under concurrent POSTs | low | Needs two simultaneous POSTs after an override changed the misses; `_set_questions` returns early when unchanged; single-user. reject |
| 7 | EC | Answer lands in another tab while a reused round is rewritten | low | Same race window as 6. reject |
| 8 | EC | `positions(round_)[0]` IndexError if Questions deleted between start and redirect | low | Delete in the same instant as the POST; same class as story 8 rows 18–20. reject |
| 9 | BH | Ownership by `assert` in `start_retry` | low | House pattern (story 8 row 13, 8b row 1); view 404s first. reject |
| 10 | BH | `parent_quiz` CASCADE unexplained | false | AD-8 hard delete with cascade; a Quiz is only deleted with its Course. reject |
| 11 | BH | `missed()` and `shown_grade` may disagree | false | Both are override-else-grade; pending/not graded are outside MISSED in both. reject |
| 12 | BH | Band why line built by `str.replace` placeholder hack | low | Safe today (int numbers, constant copy); one-line direct correction. **patch** |
| 13 | BH | No resume/next step on P07 of an abandoned or partly graded quiz | low | Frozen spec: band only for misses; «Tilbake» is at the foot; P07 of an unfinished quiz is reached only by URL. reject |
| 14 | BH | P07 reachable before the quiz is finished | false | Frozen matrix row «Abandoned» requires it. reject |
| 15 | BH | Band numbers differ from the round's 1..n numbering | low | Frozen copy names P07 numbers; the round is a new session. reject |
| 16 | BH | Result session bar switched on by empty `slots` | low | P06 always has ≥1 slot (an empty quiz redirects). reject |
| 17 | BH | Result strip `<ol>` has no accessible name | low | Unnamed list of links after the score. **patch** |
| 18 | BH | Band divider literal colour; no forced-colors rules for band | low | DESIGN.md gives `#FFFFFF2E` literally; band text and button stay legible in forced colors. reject |
| 19 | BH | Untested HTMX retry POST, pending style, singular unit | low | `redirect_after_submit` is shared and tested elsewhere; pending renders as not graded via `shown_grade`. reject |
| 20 | BH | Import order in `quiz/views.py` | low | Cosmetic, one-line move. **patch** |

## Design Notes

**Reuse rule (AD-9).** «Reuses an unanswered Retry round of the same parent»: unanswered = no Answers. A partly answered round is not reused; «Øv på feilene» then starts a fresh one from the parent's current misses.

**Display numbers.** Positions keep gaps after deletes, so P07 numbers Questions 1..N by order among the remaining ones, matching P06's «{i} av {N}».

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, with no network.
- `uv run python manage.py makemigrations --check` and `uv run python manage.py check` -- expected: no changes after `0002`, no issues.

**Manual checks:**
- At 360 px in light and dark: finish → P07, the band wraps to two rows, a row opens, «Øv på feilene» → P06 with the retry label and note, all correct → no band.
