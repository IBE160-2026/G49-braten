---
title: 'Leitner Review (Repetisjon)'
type: 'feature'
created: '2026-11-18'
status: 'done'
baseline_commit: 'e9d019ac30c766d39646766c47edd9834d0575f4'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Flashcards are generated but never practised: there is no schedule, no Due cards and no Review, and «I dag · 0» is hard-coded (CAP-9, FR-15).

**Approach:** Build the `review` app on AD-11 (Leitner boxes, one definition of Due cards, two writers) and P09 «Repetisjon»: flip a card, rate it «Igjen»/«Vanskelig»/«Bra»/«Lett» with the real return time on each button, «Igjen» cards come back in the same Review, and an end screen. Entry points: «I dag · N» (fag-rail, top-bar, fag-switcher) and «Repeter dagens kort (N)» on the Topic's «Test deg selv» tab. P08 «Bla i kort» is story 11b; the forecast-chart comes with story 13 (Author's decisions 2026-11-18).

## Boundaries & Constraints

**Always:**
- **Scope:** `courses.Scope` (frozen dataclass: `all`, a `course_id` or a `topic_id`) is the one scope type (AD-1).
- **Rules (pure, `review/rules.py`):** `INTERVALS = (1, 3, 7, 14, 30, 60, 120, 180)` days, boxes 1–8. `next_due(box, rating, today) -> (box, due_date)`: «Igjen» → box 1, due today; «Vanskelig» → same box; «Bra» → +1; «Lett» → +2; capped at 8; due = today + `INTERVALS[box-1]` except «Igjen». Also `return_label(days)` in bokmål: «i dag», «i morgen», «om N dager» (2–6), «om 1 uke» (7–13), «om N uker» (14–29), «om 1 mnd.» (30–59), «om N mnd.» (60+, N = days // 30).
- **Models (`review`, one migration):** `ReviewState(student, flashcard one-to-one, box, due_date, introduced_on)`; `Review(student, course null, topic null, started_at, ended_at null, return_url)`; `Rating(review, flashcard, rating, step, rated_at)`, unique `(review, step)`. All FKs CASCADE, so deleting a card, Source, Topic or Course removes its state and ratings (AD-8). Every row has its owning `student` (AD-7).
- **Writers (`review/services.py`, the only ones):** `introduce_today(student)` — idempotent per Oslo day; creates states (box 1, due today, introduced today) for up to `20 − introduced today` new cards from READY Sources, across all Courses, in generation order (Source id, card id). `rate(review, flashcard, rating, step)` — a no-op if `step` is already rated; otherwise writes the Rating and the new state from `next_due`. `start(student, scope, return_url)` reuses the Student's open Review of the same scope started today, else creates one. `finish(review)` sets `ended_at`.
- **Due cards:** `due_cards(student, scope)` calls `introduce_today` first, then returns states with `due_date <= today` filtered by scope, from READY Sources. It is the only definition; scope never changes which cards are introduced. A Topic Review holds only that Topic's Due cards.
- **Order in a Review:** cards not yet rated in this Review first (due date, then generation order), then cards whose last rating here was «Igjen», oldest rating first.
- **P09 page** (session layout like P06): session-bar with «Avslutt» (to `return_url`), progress «N av M» (M = distinct cards in this Review, rated or still due; N = cards done + 1), context «I dag · repetisjon» or «{tema} · repetisjon». The card shows «{fag} › {tema}», «Forside», the front and «Vis svaret». Flipping (button, Space, Enter, or without JS a `?vis=svar` link) shows «Bakside», the back and the Reference (`components/reference.html`), then the four rating-buttons, each with its `return_label` under the name. Keys 1–4 rate after the flip. A rating POSTs with the `step`; under HTMX the next card swaps in with focus on it, otherwise a redirect. Double submit is harmless.
- **End:** when nothing in the scope is due, the Review is finished and the page shows «Repetisjonen er ferdig», «Du repeterte {n} kort. Neste kort kommer {relative date}.» (or «Ingen flere kort er planlagt.») and «Tilbake» to `return_url`. Starting with nothing due creates no Review and shows «Ingen kort i dag. Neste kort kommer {dato}.» with «Tilbake».
- **Entry points:** `review:start` GET with optional `course`/`topic` and a safe `next` (else Hjem). «I dag · N» in fag-rail, top-bar and fag-switcher shows the real all-scope count and links to the all-scope start; the per-fag counts in fag-rail and fag-switcher are real too. On P05 «Test deg selv»: «{n} kort i temaet. {d} forfaller i dag.» and «Repeter dagens kort ({d})» (secondary, Topic scope, `next` = this tab), or «Ingen kort i dag». The existing card list stays.
- Copy in bokmål; dates via `core.time.today()`/`now()` (AD-12).

**Never:**
- P08 «Bla i kort», the forecast-chart or return-forecast, the Hjem and Fagoversikt bands (story 13), undo, «Forklar enklere».
- A second scheduler, a Due count computed anywhere but `due_cards`, or a write while browsing the Topic page beyond `introduce_today`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| New cards | 25 new cards, none introduced today | 20 introduced (generation order); next day 5 more | N/A |
| Topic Review | Due in Topic A and B, start from A | only A's cards; B's still due | N/A |
| Good streak | box 1 → «Bra» ×3 | due +3, +7, +14 days | N/A |
| Cap | box 8, «Lett» | box 8, +180 days | N/A |
| Igjen | «Igjen» on card 1 of 3 | card 1 comes after cards 2 and 3; box 1 | N/A |
| Double tap | same `step` POSTed twice | one Rating, one box move | N/A |
| Nothing due | start, no Due cards | «Ingen kort i dag …», no Review row | N/A |
| Not owned | another Student's Review or card | 404 | 404 |
| Card deleted mid-Review | delete via D09 | state and ratings gone; Review continues | N/A |
| Oslo day | rated 00:30 Oslo | due computed from the Oslo date | N/A |

</frozen-after-approval>

## Code Map

- `review/` -- stub (`apps.py` only); add `models.py`, `migrations/0001`, `rules.py`, `services.py`, `views.py`, `urls.py`; mount in `config/urls.py` at the root like `quiz`.
- `courses/` -- add `Scope` (e.g. `courses/scope.py` or `courses/models.py`), with a helper that filters a Flashcard/ReviewState queryset by `source__topic__course_id` / `source__topic_id`.
- `studymat/models.py:59` `Flashcard` (via `Item`: `student`, `source`, `location_index`, `quote`, ordering `source, id`); only READY Sources count (`web/views.py:95`).
- `quiz/models.py:29-55`, `quiz/views.py` (`_respond`, `_context`, `CARD_TARGET`), `templates/quiz/question.html` (`{% partialdef card inline %}`, oob session-bar) -- patterns for P09; `templates/components/session_bar.html` (no slots → use a progress variant), `components/reference.html`.
- `core/http.py` -- `render_page`, `redirect_after_submit`, `safe_next`, `vary_on_htmx`; `core/time.py` `today()`/`now()`; `tests/conftest.py` `freeze_now`.
- `static/js/app.js:170-221` -- extend with Space/Enter flip and 1–4 rating on P09 (delegated listeners, not while typing).
- `web/context_processors.py:16` -- add the real all-scope and per-course due counts; `templates/components/fag_rail.html:6-15`, `top_bar.html:5-6`, `fag_switcher.html:9,18` -- replace the hard-coded 0s and stale "story 9" comments; links to `review:start`.
- `web/views.py:83-137` + `templates/web/topic.html:45-55` -- «Test deg selv» tool-card text and button.
- Tests: `tests/test_topic_page.py:52` `ready_source(...cards=...)`, fixtures `ida`, `client_ida`; `tests/test_item_deletion.py` for the cascade.

## Tasks & Acceptance

**Execution:**
- [x] `courses` -- `Scope` and its filter.
- [x] `review/models.py`, migration, `review/rules.py`, `review/services.py` -- AD-11 model, rules and writers.
- [x] `review/views.py`, `review/urls.py`, `config/urls.py`, `templates/review/session.html` (+ end and nothing-due states), CSS in `static/css/components.css`, `static/js/app.js` -- P09.
- [x] `web/context_processors.py`, `fag_rail.html`, `top_bar.html`, `fag_switcher.html`, `web/views.py`, `templates/web/topic.html` -- real counts and entry points.
- [x] `tests/test_review_rules.py`, `tests/test_review.py` (new), `tests/test_item_deletion.py`, `tests/test_topic_page.py` -- every matrix row, `return_label` boundaries, the HTMX and no-JS responses, focus target, real «I dag · N».

**Acceptance Criteria:**
- Given a Review with 3 Due cards, when each is rated «Bra», then the end screen says «Du repeterte 3 kort» and names the next Due date, and «I dag · N» drops by 3.
- Given a card rated in a Review, when its Topic page is opened, then its Due count reflects the new date and no other card's date changed.

## Implementation Notes

- The fag-switcher shows the real count on its button; it has no own «I dag · N» link, since the top-bar above it on the same screens already links to Repetisjon (a duplicate added during review patches was removed).
- `next_due_date` returns tomorrow at the latest while the scope still has cards waiting for the daily introduction, so the end and nothing-due screens never say «Ingen flere kort er planlagt» while new cards are queued.
- The global `[hidden] { display: none !important; }` rule lives in the base rules of `static/css/components.css`.

## Spec Change Log

## Review Triage Log

Pass 1 (iteration 0) — Blind Hunter (BH), Edge Case Hunter (EC), Verification Gap (VG).

| # | Source | Finding | Verdict | Evidence / route |
|---|--------|---------|---------|------------------|
| 1 | VG | Course scope never tested to exclude other fag | medium | Mutating the course branch of `Scope.filter` left 746 green. **patch** (test) |
| 2 | VG | Course context label untested | low | Mutation survived. **patch** (test) |
| 3 | VG, BH | `rate` view guards (card no longer due, ended Review) untested | medium | Both guards removable with all tests green. **patch** (tests) |
| 4 | VG | Due-date-first order untested | low | Dropping `due_date` from the order survived. **patch** (test) |
| 5 | VG | `app.js` keys have no running test | low | No JS runner in the repo (already deferred for P06/P07). reject |
| 6 | BH | `next_due_date` ignores cards waiting for introduction | medium | With > 20 new cards, the end screen says «Ingen flere kort er planlagt» although 20 arrive tomorrow. **patch** |
| 7 | BH, EC | GET writes: `start`, `finish`, `introduce_today` in the context processor; prefetch/HEAD | low | Spec's design (Design Notes «Start on GET, reused»; AD-11 `due_cards` introduces first); local single-user app. reject |
| 8 | BH, EC | No DB CheckConstraint for one scope on `Review` | low | Only `services.start` writes, from a validated `Scope`. reject |
| 9 | BH | `return_url` max_length vs unbounded `next` | low | `safe_next` gives a relative path; SQLite stores it. reject |
| 10 | BH | `step` trusted from the client; card moved twice via two Reviews | false | The view refuses a card that is not due; a card rated in one Review is no longer due in the other unless rated «Igjen», where a second rating is legitimate. reject |
| 11 | BH, EC | Ownership `assert` in `rate` | low | House pattern (story 8 row 13, story 8b row 1); views 404 first. reject |
| 12 | BH, EC | `ReviewState.DoesNotExist` if the card is deleted mid-request | low | Real 500 window; the fix is a direct no-op. **patch** |
| 13 | BH, EC | `introduce_today` return value can overcount under a race | low | Return value unused outside tests. reject |
| 14 | BH | Global `[hidden]` rule hidden in the P09 section | low | Changes every component; moving it is direct. **patch** |
| 15 | BH | Quiz-tab negative assertion lost in `test_topic_page.py` | low | Direct restore. **patch** |
| 16 | BH | Empty-state absolute date vs end-state relative date; no year | low | Both are the spec's copy; the next date is at most 180 days away. reject |
| 17 | BH | Strings in templates, not `MESSAGES` | low | Cosmetic; no named divergence. reject |
| 18 | BH | `Progress.rated` unused; distinct count relies on Meta ordering | false | `.count()` drops ordering: the SQL is `COUNT(*) FROM (SELECT DISTINCT flashcard_id …)`. reject |
| 19 | BH, EC | Template loop in fag-switcher; empty `<b>` if course not listed | low | `current_course` is always one of the Student's courses. reject |
| 20 | BH | Switcher «I dag · N» is `role="option"` inside the fag listbox | medium | Screen readers announce a navigation link as a selectable fag. **patch** |
| 21 | BH | Extra queries per shell page | low | Two cheap queries; no measured cost. reject |
| 22 | EC | Deleting introduced cards reopens today's quota | low | Spec counts surviving states ("20 − introduced today"); harmless extra cards. reject |
| 23 | EC | Stale-tab rating dropped silently | low | Next card is shown; single user. reject |
| 24 | EC | Yesterday's open Review reachable by URL mixes days | low | `start` only reuses today's; old URL only via history. reject |

## Design Notes

**Start on GET, reused.** «I dag · N» and «Repeter dagens kort» are links, so `review:start` is a GET that reuses today's open Review of the same scope and redirects to it; a reload or second tab lands in the same Review, and nothing is created when nothing is due.

**Progress counts cards, not presses.** An «Igjen» card stays in M and is not done until rated otherwise, so «N av M» never runs backwards.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network.
- `uv run python manage.py makemigrations --check` and `uv run python manage.py check` -- expected: no changes after the new migration, no issues.

**Manual checks:**
- At 360 px in light and dark: flip, rate with buttons and keys 1–4, «Igjen» returns, the end screen; «I dag · N» updates.
