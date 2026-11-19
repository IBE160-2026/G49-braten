---
title: 'Bla i kort (Flashcard browsing)'
type: 'feature'
created: '2026-11-19'
baseline_commit: 'fb73c2439bd0f47dd355780b9ab201bb5b765e73'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Student can review Due cards (P09) but cannot flip through all of a Topic's Flashcards one at a time; the «Test deg selv» tab only lists them (CAP-9, FR-14).

**Approach:** Add P08 «Bla i kort» in `review`: one Flashcard per page in generation order, front first, flip to back and Reference, «Forrige»/«Neste» and ←/→, «Neste repetisjon: {dato}», and «⋯» with «Slett kortet» (D09). Browsing is GET only and never writes (AD-11). Reached from «Bla i alle kort» on the «Test deg selv» tab. Split from story 11 (Author's decision 2026-11-18).

## Boundaries & Constraints

**Always:**
- **Route:** `review:browse` at `topics/<topic_id>/cards/<int:position>/` (position from 1); `topics/<topic_id>/cards/` redirects to position 1. Topic owned or 404 (AD-7).
- **Cards:** the Topic's Flashcards from READY Sources in generation order (Source id, then card id) — the same order `introduce_today` uses. Position past the end → redirect to the last card; below 1 → the first. No cards → redirect to P05 `?tab=selftest`.
- **No writes:** the view never calls `due_cards` or `introduce_today` and creates no `ReviewState`, `Review` or `Rating`.
- **Page** (session layout like P09, `templates/review/browse.html`): session-bar with «Avslutt» → P05 `?tab=selftest`, progress «{n} av {m}» with the bar, context «{tema} · bla i kort». Under it the next-step-row text «Kort {n} av {m} · {m−n} kort igjen i temaet · → neste kort» (on the last card: «Siste kort i temaet»). The card reuses P09's card markup and classes: meta «{fag} › {tema}» with «Forside»/«Bakside», the front, «Vis svaret» (link to `?vis=svar`, flipped in place by `app.js`, Space/Enter), then the back and the Reference (`components/reference.html`). Under the card: «Neste repetisjon: {dato}» («19. november», `core.time.long_date`) from its `ReviewState.due_date`, or «Ikke repetert ennå» without one.
- **Moving:** «Forrige» and «Neste» links (absent at the ends, not disabled); ← and → follow them in `app.js` (not while focus is in a field or menu). Moving always shows the front.
- **«⋯»:** `components/menu.html` with `studymat/item_menu_items.html` (`item_kind="card"`, «Slett kortet»); D09's `next` is this page, so after deleting the Student lands on the same position (the following card), or the last, or P05 when none are left.
- **Entry:** on the «Test deg selv» tool-card «Kort», add «Bla i alle kort» (quiet button) → position 1, whether or not cards are due.
- **The card list on «Test deg selv» is removed** (Author's decision 2026-11-19): the tab shows only its tool-cards, as in EXPERIENCE.md; P08 is where cards are read and deleted. Tests that used the list move to P08.
- Copy in bokmål via `core/messages.py` where reused; `lang` from the Source on front and back.

**Never:** writes of any kind while browsing; «Forklar enklere» (story 16); the forecast (13b); shuffling or filtering.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Order | two Sources, cards made in order | position 1 is the first card of the older Source | N/A |
| Flip without JS | GET `?vis=svar` | back and Reference shown, front heading kept | N/A |
| Ends | position 1 / last | no «Forrige» / no «Neste»; last says «Siste kort i temaet» | N/A |
| Out of range | position 0 or m+5 | redirect to first / last | N/A |
| No writes | browse every card of a Topic with new cards | no `ReviewState` created; Due counts unchanged | N/A |
| Dates | card with state due 2026-11-25; new card | «Neste repetisjon: 25. november»; «Ikke repetert ennå» | N/A |
| Not ready | a generating Source's cards | not listed | N/A |
| Delete | delete card 3 of 5 via D09 | lands on position 3 (old card 4), «3 av 4» | N/A |
| Empty | Topic without ready cards | redirect to P05 `?tab=selftest` | N/A |
| Not owned | another Student's Topic | 404 | 404 |

</frozen-after-approval>

## Code Map

- `review/views.py` -- P09 `session`/`_context` (card markup data, `FLIP_PARAM`/`FLIP_VALUE`), `_context_label`; add `browse`. `review/urls.py` -- add the route. Do not touch `review/services.py` writers.
- `templates/review/session.html` -- card markup to reuse (consider extracting the card article into `components/` if both pages share it); `components/session_bar.html` (reads `exit_url`, `context_label`, `index`, `total`, `bar`, `done`).
- `review/models.py` -- `ReviewState(flashcard one-to-one, due_date)`; read only.
- `studymat/models.py` -- `Flashcard` (`source`, `front`, `back`, Reference fields), `Item.Meta.ordering = ["source", "id"]`.
- `studymat/views.py:230` `delete_item` -- D09 honours a safe `next`; `templates/studymat/item_menu_items.html` passes `request.get_full_path`.
- `templates/web/topic.html` -- «Test deg selv» tab: the «Kort» tool-card and the list (`components/flashcard_item.html`).
- `static/js/app.js:223` -- P09 flip handling (`[data-review-card]`, `[data-flip]`); extend for P08 and add ←/→.
- `core/time.py` -- `long_date`.
- Tests: new `tests/test_browse_cards.py` (FR-14, every matrix row); update `tests/test_topic_page.py` / `tests/test_item_deletion.py` per the list decision.

## Tasks & Acceptance

**Execution:**
- [x] `review/views.py`, `review/urls.py`, `templates/review/browse.html` -- P08 view and page.
- [x] `templates/web/topic.html` -- «Bla i alle kort»; the list per the decision.
- [x] `static/js/app.js`, `static/css/components.css`, `core/messages.py` -- flip and ←/→ on P08, styles, copy.
- [x] `tests/test_browse_cards.py` and updated tests -- every matrix row.

**Acceptance Criteria:**
- Given a Topic with cards, when the Student clicks «Bla i alle kort», then P08 opens on card 1 of m with the front showing.
- Given P08, when «Avslutt» is clicked, then P05 opens on «Test deg selv».

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | VG, BH | ←/→ and the shared Space/Enter flip on P08 are checked only by a source-text test | medium | No JS or browser runner in the repo; same as every other `app.js` behaviour | defer |
| 2 | ECH, BH | IndexError (500) if a card disappears between `count()` and the fetch | low | `cards[position - 1]` on a QuerySet raises when the row is gone; a direct correction | patch |
| 3 | ECH, BH | HTMX delete of the last/only card swaps the next page into the session layout with a stale URL | medium | D09 opens in `#dialog` and answers `HX-Location`; after a 302 to P05 the body keeps `session-body` | patch |
| 4 | ECH | Last-card row keeps «Kort m av m ·» before «Siste kort i temaet» | false | The spec names only the text that replaces the remaining-count part; both readings fit | reject |
| 5 | BH | Spec says in-review, sprint-status says in-progress; empty sections | false | The workflow moves sprint-status in step 5 and fills the log now | reject |
| 6 | BH | Few Given/When/Then ACs | false | Every behaviour is a matrix row with a test; fixing it edits the spec | reject |
| 7 | BH | Empty nav landmark and «← → blar» hint on a one-card Topic | low | Renders `<nav>` with no links; a direct correction | patch |
| 8 | BH | Click or tap on the card does not flip it (EXPERIENCE.md) | low | Inherited from P09's card (story 11); fixing it adds JS to both pages | defer |
| 9 | BH | «Forrige», «Neste», «Bla i alle kort» etc. hard-coded, not in `core/messages.py` | false | The spec asks for messages only where reused; these labels appear once | reject |
| 10 | BH | «⋯» trigger's accessible name no longer names the card | low | The removed list passed the front; one-line correction | patch |
| 11 | BH | Extra query for «Neste repetisjon» | low | One indexed lookup per page | reject |
| 12 | BH | Code Map line numbers go stale | false | Fixing it edits the spec | reject |
| 13 | BH | Reload/Back after an in-place flip shows the front | low | Matches «Moving always shows the front»; P09 behaves the same | reject |
| 14 | BH | Not-ready-only Topic redirect path untested | false | `test_fr14_cards_of_a_source_that_is_not_ready_are_not_listed` and the Empty test cover it | reject |

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, socket disabled.
- `uv run python manage.py check` and `uv run python manage.py makemigrations --check --dry-run` -- expected: no issues, no changes.

**Manual checks (if no CLI):**
- 360 px, light and dark: flip with Space, ←/→, «⋯» → «Slett kortet».
