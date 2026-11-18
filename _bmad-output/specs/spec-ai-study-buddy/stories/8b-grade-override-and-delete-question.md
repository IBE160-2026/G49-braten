---
title: 'Grade override and «Slett spørsmålet» in the feedback panel'
type: 'feature'
created: '2026-11-18'
status: 'done'
baseline_commit: 'b33ee5f7c414ff0ab22ab3b64a40784adb76abc5'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On P06 the Student cannot correct a Free-text Grade they disagree with, and cannot remove a bad Question while practising. CAP-7 (FR-12 override) and FR-24 on P06 are unfinished; story 8 already stores `Answer.override_grade` and `with_effective_grade()` (split from story 8, Author's decision 2026-11-17).

**Approach:** Add «Endre vurdering» (a menu of Grades plus «Bruk KI-vurderingen») and «Slett spørsmålet» (story 7's D09) to the feedback panel. The override saves at once and the panel re-renders with the effective Grade.

## Boundaries & Constraints

**Always:**
- **Override, where offered:** only on a Free-text Answer whose AI `grade` is `correct`, `partial` or `incorrect`. Never on Multiple-choice, on «Ikke rettet», or on a pending Answer (`grade` null).
- **Menu:** a quiet «Endre vurdering» button with the pencil icon among the feedback actions opens a native popover menu (like `account_menu.html`). Items: «Riktig», «Delvis riktig», «Feil», plus «Bruk KI-vurderingen» once overridden. The effective Grade's item is marked `aria-current="true"`. Each item is a POST button; the choice saves at once.
- **Write path:** `quiz.services.override_grade(student, answer, grade | None)` is the only writer of `override_grade`. `None`, or the AI Grade itself, clears the override. `answered_at`, `grade` and `explanation` never change. Any other case (MC, not graded, pending, an unknown value) leaves the row as it is.
- **POST** `quizzes/<id>/<position>/override/` (owned or 404) answers like `regrade`: under HTMX the `card` partial for `#question-card`, otherwise a redirect to the position. Focus returns to the feedback heading.
- **Overridden panel:** the tint, icon and heading follow the effective Grade (`shown_grade`). Beside the heading sits the chip «Endret av deg» with the pencil icon, styled like «Demo». Above the original Explanation, the line «KI-vurdering: {AI Grade label}» in small `ink-3` text.
- **«Slett spørsmålet»:** a quiet destructive action with the trash icon among the feedback actions, shown for every answered Question. It opens story 7's D09 (`studymat:delete_item`, kind `question`) in `#dialog`. After the delete, the Quiz continues at the panel's next URL (the next position, or resume, which lands on the finish note or `return_url`). «Avbryt» returns to the same P06 position, with or without JS.
- **Copy** in bokmål; D09 keeps story 7's copy («Slette spørsmålet?», «Dette kan ikke angres.», «Slett spørsmålet»).

**Never:**
- A migration, a new model field, or a change to `with_effective_grade`.
- Changing the AI Grade or Explanation on override, or calling the gateway.
- P07, Retry rounds, scores, history (stories 9, 12, 13) or Exam mode.
- `hx-confirm`, or deleting without D09.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Override | Free-text graded «Feil», POST `grade=correct` | override `correct`; panel «Riktig» + «Endret av deg» + «KI-vurdering: Feil» | N/A |
| Undo | overridden, POST `grade=ai` | override cleared; panel shows AI Grade, no chip | N/A |
| Same as AI | graded `partial`, POST `grade=partial` | override stays null | N/A |
| Not allowed | MC Answer, «Ikke rettet», or no Answer, POST | nothing saved; panel as before; no «Endre vurdering» shown | N/A |
| Bad value | POST `grade=not_graded` or `xyz` | nothing saved | N/A |
| Not owned / bad position | other Student's quiz | 404 | 404 |
| Delete mid-quiz | answered position 2 of 5, D09 «Slett spørsmålet» | Question, its QuizQuestion and Answer gone → P06 next position, «… av 4» | N/A |
| Delete last | last Question, D09 confirm | resume → finish note on the Quiz tab, or `return_url` if none left | N/A |
| Cancel delete | «Avbryt» in D09 without JS | back at the same P06 position | N/A |

</frozen-after-approval>

## Code Map

- `quiz/services.py:90` `regrade` -- model `override_grade` on it: the ownership `assert`, update only the one field, `refresh_from_db`. Use `Grade` from `quiz/rules.py`; valid override values are `CORRECT`, `PARTIAL`, `INCORRECT`.
- `quiz/models.py:104` `shown_grade` already returns `override_grade or grade`; add an `is_overridden` property (`override_grade` set and different from `grade`) only if the template needs it.
- `quiz/views.py` -- add `override` beside `regrade` (same decorators, `_owned_position`, `_stored_answer`, `_after_post`). In `_context`, add: `can_override` (free-text and `grade` in the three), `overridden`, `ai_grade_label`, `override_url`, `delete_url` (`studymat:delete_item` `question` id with `next`=the panel's `next_url` and `cancel`=this position's URL), and the menu items with their current mark.
- `quiz/urls.py` -- `quizzes/<int:quiz_id>/<int:position>/override/`, name `override`.
- `templates/components/feedback_panel.html` -- add the chip, the «KI-vurdering» line, and in `.feedback-actions` the override popover and the delete link (`hx-get` into `#dialog`, `hx-swap="innerHTML"`, as in `templates/studymat/item_menu_items.html`). The menu is inside `#question-card`, so a swap closes it. Use `{% icon "pencil" %}` and `{% icon "trash" %}` (both in `static/icons/sprite.svg`).
- `studymat/views.py:154` `delete_item` -- currently `cancel_url = next or tab`. Accept an optional safe `cancel` (relative path only) for «Avbryt». Generalise `core/http.py:58` `safe_next(request)` with a `field="next"` parameter rather than copying it. Leave the story-7 behaviour unchanged when `cancel` is absent.
- `static/css/components.css:877` feedback-panel block -- styles for the «KI-vurdering» line, a quiet destructive action, and the menu placement. Reuse `.chip`, `.menu`, `.menu-item`.
- `static/js/app.js` -- `[data-anchored]` popovers are already placed; nothing new is expected.
- Do not change `ai/`, the migrations, `with_effective_grade`, or `templates/courses/delete.html`.
- Tests: copy the P06 fixtures from `tests/test_quiz.py` and use `tests/test_item_deletion.py` for the D09 pattern.

## Tasks & Acceptance

**Execution:**
- [x] `quiz/services.py` -- add `override_grade` -- the only write path for FR-12's override.
- [x] `quiz/views.py`, `quiz/urls.py` -- add the override POST and the new context keys -- owned or 404.
- [x] `core/http.py`, `studymat/views.py` -- `safe_next(field=…)` and the optional `cancel` for D09 -- «Avbryt» returns to P06.
- [x] `templates/components/feedback_panel.html`, `static/css/components.css` -- the menu, chip, «KI-vurdering» line and «Slett spørsmålet».
- [x] `tests/test_grade_override.py` (new), `tests/test_quiz.py`, `tests/test_item_deletion.py` -- every I/O matrix row, the menu shown or not per case, `aria-current` on the effective Grade, the HTMX and no-JS responses, and that `cancel` refuses an absolute URL.

**Acceptance Criteria:**
- Given an overridden Answer, when `Answer.objects.with_effective_grade()` is read, then it returns the override.
- Given an overridden Answer, when P06 is reloaded, then it shows the override with «Endret av deg» and the original AI Grade and Explanation.
- Given the story-7 Quiz tab, when an item is deleted from its «⋯» menu, then it still lands on the Quiz tab as before.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Pass 1 (iteration 0) — Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG: no gaps).

| # | Source | Finding | Verdict | Evidence / route |
|---|--------|---------|---------|------------------|
| 1 | BH, EC | Ownership in `override_grade` is an `assert` (stripped under `-O`) | low | Same pattern as `regrade`, `delete_item`, `_counted` (story 8 row 13); the view 404s first. reject |
| 2 | EC | Stale `next` position if that Question is deleted elsewhere after render → 404 | low | Needs a delete in another tab between render and confirm; single-user app. reject |
| 3 | EC | «Slett spørsmålet» during in-flight grading → `refresh_from_db` DoesNotExist 500 | low | Only while a Real grading call runs (story 10); Mock grades in the request. Belongs with the deferred pending-vs-failed entry from story 8. reject |
| 4 | EC, BH | `override_grade` set while `grade` is None/not_graded → `Grade(None)` 500 or orphan chip | false | Override is only written when `grade` ∈ OVERRIDABLE; `regrade` only rewrites None/not_graded and `save_answer` is first-write-wins, so a graded `grade` never changes. reject |
| 5 | BH | Stale read: override lands after AI Grade changed | false | Same as 4: no writer changes a graded `grade`. reject |
| 6 | BH | No test that the override reaches score/finish note | false | `tests/test_quiz.py:352-359` pins `finish_note` using an override (VG). reject |
| 7 | BH | Popover menu `aria-label` on a role-less div gives no name | low | Generic elements prohibit `aria-label`. **patch** (`role="group"`) |
| 8 | BH | Current menu item mark lost in forced-colors | low | Background and box-shadow are dropped; only bold remains. **patch** |
| 9 | BH | `"ai"` literal duplicated in template and `USE_AI` | low | Separator breaks silently if one changes. **patch** (flag from `_override_items`) |
| 10 | BH | Invalid value / not-overridable POST is silent 200/302 | false | Frozen matrix: «nothing saved», panel as before. reject |
| 11 | BH | Tests pass both `chosen_index` and `text`; `next` unchecked; no backslash `cancel` cases | low | Fixtures are deterministic; VG confirms `next` is asserted; `url_has_allowed_host_and_scheme` handles backslash forms. reject |
| 12 | BH | `safe_next(..., "cancel")` also reads POST | low | Only a relative path passes either way; harmless. reject |

## Design Notes

**Picking the AI Grade clears the override.** Storing an override equal to the AI Grade would show «Endret av deg» for no change; clearing keeps the mark honest and makes «Bruk KI-vurderingen» and picking the AI Grade the same act.

**Delete lands on the next URL, not on a recomputed one.** The cascade removes the QuizQuestion and Answer, so the panel's `next_url` (the next existing position, or resume) is still right after the delete; resume handles a Quiz with nothing left.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, with no network.
- `uv run python manage.py makemigrations --check` and `uv run python manage.py check` -- expected: no changes and no issues.

**Manual checks:**
- At 360 px in light and dark: «Endre vurdering» opens the menu at its button, Esc closes it, a choice re-renders the panel with focus on the heading; «Slett spørsmålet» opens D09, «Avbryt» closes it, and «Slett spørsmålet» moves to the next Question.
