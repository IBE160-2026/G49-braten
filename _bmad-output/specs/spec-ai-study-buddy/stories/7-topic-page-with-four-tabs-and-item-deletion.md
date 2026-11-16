---
title: 'Topic page with four tabs and item deletion'
type: 'feature'
created: '2026-11-16'
status: 'done'
baseline_commit: '3d240440d43e22cdceed8a69c1b0afec7a5a3754'
route: 'dispatch'
review_loop_iteration: 1
context:
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** P05 shows only a source list. Ready Study material is invisible, and the Student cannot remove a wrong Key concept or Flashcard (CAP-6, FR-23, FR-24).

**Approach:** Turn P05 into an ARIA tablist with «Sammendrag», «Quiz», «Test deg selv», «Kilder» selected by `?tab=summary|quiz|selftest|sources`. Show each ready Source's Summary and Key concepts with References. Add a D09 confirm dialog that deletes one item through `studymat.services`.

## Boundaries & Constraints

**Always:**
- Tabs are full-page GET links (`web:topic?tab=…`, AD-13: every URL renders a full page, no lazy loading). An unknown or missing `tab` gives `summary`. Use `role="tablist"`/`tab` (`aria-selected`)/`tabpanel`. In `app.js`, ←/→ move to the neighbouring tab and Home/End to the ends, each following that tab's link. Labels carry counts «Quiz · {questions}», «Test deg selv · {cards} kort», «Kilder · {sources}», with the count chip hidden below 600 px. Selected tab: ink, weight 700, 3 px underline, never copper (DES).
- Sammendrag: one summary-block per `ready` Source, newest first. Each block holds the source name, the full Summary (max 68ch), the removed note when `removed_count > 0` («1 element ble fjernet …» / «{n} elementer ble fjernet fordi kildehenvisningen ikke stemte.»), then its Key concepts (term, definition, Reference). A generating Source shows the dashed line «{kilde}: sammendraget lages. Vanligvis under 2 minutter.» There is no combined Topic Summary. With no ready Source the tab shows an empty-state.
- References render through new `components/reference.html` («Side {n} · {kilde}» for PDF, «Avsnitt {n} · {kilde}» for text, then the quote in «»), with the label from one helper `studymat.services.location_label(source, location_index)`. They are never external links.
- Kilder tab: today's «Legg til kilde» button and source-rows, unchanged in behaviour.
- Test deg selv (Author's decision 2026-11-16): a compact list of the Topic's Flashcards from ready Sources, newest Source first. Each shows front, back and Reference, with «⋯» → «Slett kortet». P08 (story 11) may replace the list.
- Actions for later stories are left out until their story ships (Author's decision 2026-11-16): no «Velg antall og start», «Repeter dagens kort», «Bla i alle kort» or «Sett opp prøveeksamen». The Quiz tab shows «{n} spørsmål er klare.» (or an empty-state when there are none) and «Tidligere quizer» with «Du har ikke tatt en quiz i dette temaet ennå.»
- Questions are never listed on P05, only counted.
- Deletion: `GET/POST items/<kind>/<id>/delete/` (`studymat:delete_item`, kind `concept|card|question`). It is owned (404), uses the `courses/delete.html` alertdialog pattern (GET into `#dialog`, POST → `redirect_after_submit` to `safe_next`, else `web:topic` with the right tab), and calls `studymat.services.delete_item(student, item)`, a hard delete (AD-8). The trigger is the item's «⋯» → «Slett». No toast, no undo. Copy: «Slette nøkkelbegrepet {term}?» / «Slett nøkkelbegrepet»; «Slette kortet?» / «Slett kortet»; lead «Dette kan ikke angres.» The `question` kind has a service and route but no P05 trigger (story 8 adds it in feedback).
- A deleted item's row is gone, so it can't appear in Topic, Quizzes, Retry rounds or Due today. Stories 8–11 build on that FK-cascade (AD-8).

**Never:** Detail-level Summary regeneration (deferred to its own story, Author's decision 2026-11-16, `deferred-work.md`); band and Next step (story 13); «Forklar enklere» (story 16); quiz history data (story 9); Leitner state (story 11); a `deleted` flag; `hx-confirm`/native confirm; HTMX partial tab swaps; Question text on P05.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Ready Sample | GET topic | Sammendrag selected; Summary, ≥ 5 Key concepts with «Side n · …», «1 element ble fjernet …» | N/A |
| Tab param | `?tab=sources` / `?tab=x` | Kilder selected / Sammendrag selected | 200 |
| Generating | pending Source only | dashed «… sammendraget lages …» line, no block | N/A |
| Delete card | POST owned Flashcard from «Test deg selv» | row gone; back on `?tab=selftest`; «Test deg selv · n−1 kort» | N/A |
| Delete concept | POST owned KeyConcept | row gone; HX-Location to topic Sammendrag; count drops | N/A |
| Not owned | other Student's item, GET or POST | 404, nothing deleted | 404 |
| Bad kind | `items/foo/1/delete/` | 404 | 404 |
| No CSRF | POST without token | 403, nothing deleted | 403 |

</frozen-after-approval>

## Code Map

- `web/views.py:40-63` `topic` -- add `tab` parsing and context (`ready_sources` with `summary` + `key_concepts` prefetched, counts); keep `get_owned_or_404`, `@vary_on_htmx`, `render_page`.
- `templates/web/topic.html` -- replace the single `source-list` section with tablist + panel; the line 12 comment marks the spot. The current Kilder markup moves into the Kilder panel unchanged.
- `studymat/models.py` -- `Item` (OwnedQuerySet, cascade), `Summary` (OneToOne `summary`), `KeyConcept`, `Flashcard`, `Question`; no migration needed.
- `studymat/services.py` -- add `delete_item`, `location_label`; `locations()` exists.
- `studymat/views.py`, `studymat/urls.py` -- add `delete_item`, copying the `courses/views.py:86` `_delete` pattern (studymat may not import `courses.views`); `TOPIC_PAGE` constant; `core.ownership.get_owned_or_404`, `core.http.redirect_after_submit`/`safe_next`.
- `templates/courses/delete.html`, `components/dialog.html` (`alert=True`), `components/menu.html`, `components/empty_state.html`, `courses/source_menu_items.html` (menu-item `hx-get` + `?next=` pattern) -- reuse.
- `core/messages.py` -- add the removed-note and delete-lead codes; `{% message %}` tag / `|message_text`.
- `static/js/app.js`, `static/css/components.css` -- tab keyboard handler, tab + summary-block + reference styles.
- `tests/test_topics_sources.py` (helpers `topic_url`, `main_of`, `client_ida`) and `tests/test_generation.py` (`sample` fixture + `generate`, `transaction=True`) -- patterns. The import graph allows web→studymat→courses only.
- `studymat/views.py:60,88` `add_source` (`topic_url` → `redirect_after_submit`) and `:128` `generate` (non-HTMX `redirect(TOPIC_PAGE, …)`) -- land on `?tab=sources` (Design Notes).
- `courses/views.py:86-91` `_delete` ignores `next` on POST; `delete_source` (~199-213) `after_url` -- make it `?tab=sources`. `templates/courses/{source,topic}_menu_items.html` -- `next` = `request.get_full_path`.

## Tasks & Acceptance

**Execution:**
- [x] `studymat/services.py` -- `delete_item`, `location_label` -- AD-1, AD-8.
- [x] `studymat/views.py`, `studymat/urls.py`, `templates/studymat/item_menu_items.html` -- delete dialog endpoint; upload and generate land on `?tab=sources` -- FR-24.
- [x] `courses/views.py`, `templates/courses/{source,topic}_menu_items.html` -- kilde delete lands on «Kilder»; menus keep the tab in `next`.
- [x] `web/views.py`, `templates/web/topic.html`, `templates/components/{tabs,summary_block,key_concept_item,flashcard_item,reference}.html` -- tabs, Sammendrag, card list -- FR-23.
- [x] `static/js/app.js`, `static/css/components.css` -- keyboard tablist and styles -- WCAG 2.2 AA.
- [x] `core/messages.py` -- copy codes.
- [x] `tests/test_topic_page.py`, `tests/test_item_deletion.py` -- every matrix row; names `test_fr23_…`/`test_fr24_…`; plus landing tests for upload and kilde delete.

**Acceptance Criteria:**
- Given a Topic with two ready Sources, when P05 loads, then their summary-blocks appear newest first and no Question prompt text is in the HTML.
- Given an item is deleted, when P05 reloads, then the tab counts reflect it and the other items of that Source are untouched.
- Given `uv run pytest` offline, then everything passes, including the import-graph test.

## Implementation Notes

- Only the selected tab's panel is rendered; tabs use a roving tabindex, and `app.js` puts focus back on the selected tab after a keyboard tab change (sessionStorage flag, wrapped in try/catch).
- «Sammendrag» is the default tab, so a `pending` kilde's dashed line also starts generation (`hx-post` on load, `hx-swap="none"`); `studymat.views.generate` answers a target starting with `summary-pending-` with `HX-Refresh`. Without this, an upload (which lands on P05 without `?tab`) would never start its run.
- `courses/source_menu_items.html` now passes `request.get_full_path` as `next`, so rename from «Kilder» returns to «Kilder». `courses.views.delete_source` still lands on the bare P05 (Sammendrag).
- The delete lead reuses the existing `delete_cannot_undo` code; new codes are `removed_note_one`/`removed_note_other`.
- Existing P05 tests that inspect source-rows now request `?tab=sources`.
- (Notes above are from iteration 0, reverted after review; see Spec Change Log.)

## Spec Change Log

- **Iteration 1 (review pass 1, bad_spec).** Trigger: a Sammendrag-tab generation trigger (not in the spec) answered with `HX-Refresh`. A failed run (Mock `needs_key`, `daily_limit`, provider errors) made the kilde vanish from the default tab, with the reason hidden. Several pending kilder refreshed mid-request and left the others stuck. Kilde delete from «Kilder» landed on «Sammendrag». The spec never said where an upload lands. Amended: Design Notes «Landing», Code Map lines for `add_source`/`generate`/`_delete`/menus, Tasks. Known-bad state avoided: generation started or failures reported on a tab that cannot show them. KEEP: the tablist markup (roving tabindex, `aria-controls`/`aria-labelledby`, full-page links, `tab-count` chip), `app.js` focus restore via try/catch'd sessionStorage, `_summary_blocks` shape (ready block / dashed line, newest first), `location_label`, `reference.html`, `ITEM_KINDS` + `_delete_copy`, `delete_item` dialog reusing `courses/delete.html` with `delete_cannot_undo`, `removed_note_one/_other`, the `ready_source` test builder, and the test suites `test_topic_page.py` / `test_item_deletion.py`. Also: ignore Shift with arrow/Home/End in `app.js`; hide `.tab-count` below 600 px visually only (visually-hidden styles, so screen readers keep the count); wrap the edited docstrings at the file's width.

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap).

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Failed kilde vanishes from the default tab after a Sammendrag-started run; the empty state hides the reason (BH, ECH, VG) | medium | bad_spec | `_summary_blocks` keeps only READY/GENERATING; the Sammendrag trigger + `HX-Refresh` sends every upload's failure there. Mock `needs_key` hits it on any non-Sample upload. |
| Several pending kilder: the first `HX-Refresh` reloads mid-request, the rest stay generating with no trigger (ECH) | medium | bad_spec | Same root cause: the trigger on the dashed line. |
| No live-region text after `HX-Refresh` (BH) | low | bad_spec | Same root cause. |
| Kilde delete from «Kilder» lands on «Sammendrag» (VG, ECH) | low | bad_spec | `_delete` POST uses `after_url`, bare P05; the default tab is now Sammendrag. |
| Topic menu `next` drops the tab (VG) | low | bad_spec | `topic_menu_items.html` uses `request.path`; folded into the landing amendment. |
| Shift+arrow navigates (ECH) | low | bad_spec | Direct correction; carried as a KEEP instruction. |
| `.tab-count` `display:none` hides the count from screen readers on phones (BH) | low | bad_spec | Verified in CSS; carried as a KEEP instruction. |
| Tab keyboard JS untested (VG, BH) | low | defer | No JS/browser harness in the repo; manual check. |
| Unselected tabs unreachable without JS (BH) | low | reject | `app.js` loads on every page; roving tabindex is the ARIA pattern; adding a no-JS branch adds complexity. |
| Space doesn't activate a tab (BH) | low | reject | Enter follows the link; tabs follow focus on arrows; a new key branch for a rare path. |
| Generating line never updates (BH, ECH) | false | reject | Polling is a frozen Never in story 6 (FR-26, story 18). |
| Pending→generating via `effective_status` undocumented (BH) | false | reject | `courses/models.py:143-146` docstring states it (AD-5). |
| Counts use stored status vs `effective_status` (BH) | false | reject | `effective_status` only rewrites PENDING and stale GENERATING; READY reads the same both ways. |
| «Quiz · 0» shows (BH, ECH) | low | reject | Spec format «Quiz · {questions}» includes 0; harmless. |
| Ready kilde without Summary shows a bare heading (BH) | false | reject | `generate` fails on an empty Summary and saves all or nothing; a ready Source always has one. |
| Bad-kind test hard-codes the URL (BH) | false | reject | `studymat.urls` is mounted at `""` (`config/urls.py:8`); `<str:kind>` matches `foo`, so the view's check runs. |
| Test helpers shared across modules (BH) | low | reject | Works; style only. |
| Untested: question GET dialog, zero-source aria pairing (BH) | low | reject | Same template path as card/concept, covered there. |
| `ITEM_KINDS` comment says "its copy"; long docstring line (BH) | low | bad_spec | Direct corrections; carried as KEEP instruction. |
| `delete_item` doesn't check item type (BH) | low | reject | The only caller passes a model from `ITEM_KINDS`. |

Pass 2 (Blind Hunter, Edge Case Hunter, Verification Gap), after iteration 1.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| `delete_source` `cancel_url` still bare P05; non-HTMX «Avbryt» from «Kilder» lands on «Sammendrag» (BH) | low | patch | `courses/views.py` passes `cancel_url=topic_url`; direct correction to the Landing value. |
| `.summary-block:last-of-type` drops the separator when a pending line or empty-state follows (BH) | low | patch | Verified `components.css:723-724`; `:last-of-type` keys on `<article>` only. Direct CSS correction. |
| No test: selftest omits cards of non-ready Sources (VG) | low | patch | Pre-verified gap; dropping `source__status` from the list query passes every test. |
| No test: stale run is left out of Sammendrag (VG) | low | patch | Pre-verified gap; switching to raw `status` passes every test. |
| Tab keyboard JS covered only by source-text checks (VG, BH) | low | defer | carried: same claim as pass 1; already in `deferred-work.md`. |
| Pending kilde on Sammendrag says «lages» but nothing starts it there; default tab no longer starts pending runs (BH, ECH) | low | reject | Every path that creates a pending Source lands on `?tab=sources` (Design Notes «Landing»), whose row starts it on load; a pending row unseen on «Kilder» needs leaving before page load. The dashed line is display-only by the amended spec; AD-5 reads pending as generating. |
| `assert` in `delete_item` stripped under `-O` (BH, ECH) | false | reject | The app never runs under `-O` (story 5/6 precedent); the view checks ownership with 404 first. |
| Arrow keys reload a page per press; should be manual activation; Space unhandled (BH) | low | reject | Frozen intent: ←/→ and Home/End each follow that tab's link. Space: carried from pass 1. |
| Held arrow key auto-repeat fires several navigations (ECH) | low | reject | The first `location.href` wins in practice; a repeat guard adds a branch for a rare case. |
| Key-concept prefetch has no `order_by` (BH) | false | reject | `Item.Meta.ordering = ["source", "id"]` (`studymat/models.py:31`) applies to the prefetch queryset. |
| Import order in `web/views.py` (BH) | false | reject | No isort/ruff config in `pyproject.toml`; nothing lints imports. |
| Duplicated visually-hidden CSS (BH) | low | reject | Style only; no named divergence. |
| Copy spread across templates/views instead of MESSAGES (BH) | false | reject | Repo convention: UI text inline in templates, MESSAGES for errors and shared notes. |
| `menu_next` only passed by `generate` (BH) | false | reject | `studymat/source_row.html` is rendered only by `generate` (grep); P05 renders the component directly. |
| Bad-kind test hard-codes URL (BH) | false | reject | carried: `studymat.urls` mounted at `""`. |

## Design Notes

**Landing** (where Student actions return on P05). Generation starts only from the «Kilder» source-row, as in story 6; the Sammendrag dashed line is display-only (no `hx-post`, no `HX-Refresh`). So everything that concerns a kilde's status lands on `?tab=sources`, where the status and «Prøv igjen» live:
- upload (`add_source` valid POST, both submits) → `web:topic?tab=sources`; `generate` without HTMX → same.
- kilde delete → `safe_next` else `?tab=sources`; rename keeps returning to `next`.
- item delete → `safe_next` else the item's tab (unchanged).
- Bare `web:topic` still opens «Sammendrag» (frozen).

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes

**Manual checks (if no CLI):**
- At 360 px in light and dark mode: no horizontal scroll, the tabs wrap or scroll inside themselves, and the count chips are hidden.
