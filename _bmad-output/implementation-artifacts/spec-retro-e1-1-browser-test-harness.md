---
title: 'Retro action E1-1: Key-free browser tests for app.js'
type: 'chore'
created: '2026-11-25'
status: 'done'
baseline_commit: 'be6ba494f6b188e2f2656b55e569b0363d4e0112'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `static/js/app.js` has no running test. It was deferred six times (deferred-work.md lines 10, 34, 43, 49, 64, 73). The only checks are source-text regexes, so deleting `showModal()` or breaking a key handler fails nothing.

**Approach:** Add Playwright (Chromium, headless) driven by pytest against Django's `live_server` in Mock mode, with no Key. Add one test module per surface, each asserting the observable behaviour the deferred entries name.

## Boundaries & Constraints

**Always:**
- Mock mode (`config.settings_test`). No network beyond 127.0.0.1. Build DB state with the existing helpers rather than new factories.
- Pin versions in `pyproject.toml` and `uv.lock` (dev group).
- Socket blocking stays on for every other test. Only the browser tests may open 127.0.0.1.
- Decision (Author, 2026-11-25): the tests are **opt-in**. A `browser` marker is deselected by default and run with `uv run pytest -m browser` after `uv run playwright install chromium`. The plain `uv run pytest` is unchanged (no download, no skips). The README documents the two commands.

**Never:**
- No change to `app.js` or the templates unless a test exposes a real bug. Such a bug is fixed and recorded in Implementation Notes.
- No Node or JS toolchain (AD-13).
- No CI setup.
- No visual or screenshot assertions.
- Not a new UJ-5 walk-through (that is `test_examiner_path.py`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior |
|---|---|---|
| Dialog opens | Click «Nytt fag» (hx-target `#dialog`) | `#dialog dialog` is `open` (modal) |
| Dialog closes by Esc | Open dialog, press Escape | `#dialog` empty; focus back on the trigger |
| Dialog closes by Avbryt | Click `[data-dialog-close]` | Same as Esc; URL unchanged (no navigation) |
| Dialog valid submit | Submit «Nytt fag» with a name | Page swapped; focus on `[autofocus]` or `#main` |
| Network failure | Route aborts the dialog POST | `.dialog-messages` holds `#message-network-error` content |
| Server error | Route answers 500 | `#message-response-error` content shown in place |
| P05 tab keys | Focus `#tab-summary`, press → / ← / End / Home | Navigates to the neighbour tab's URL; on the new page the selected tab has focus; wraps at the ends |
| P06 keys | Quiz question, press 2 then Enter | Option 2 checked; answer submitted; focus on `.feedback-heading` |
| P06 move on | Enter on `.feedback-heading` | Next question (`[data-next]` followed) |
| P06 typing guard | Free-text field focused, press 1 | Character typed, no option selected |
| P07 strip | Click `a.result-slot` q-3, then click it again after closing the row | `details#q-3` open and its summary focused, both times |
| P07 hash | Load result URL with `#q-2` | `details#q-2` open |
| D10 footer | Check one box, then a second | Footer shows the `data-one` text with counts, then the `data-other` text with summed `data-questions` |
| P08 arrows | Card 2 of 3, press → then ← | Card 3, then card 2; at card 3 → does nothing |
| P08 guards | Focus inside an open popover menu, press → | No navigation |
| P08/P09 flip | Press Space on the card front | Back faces shown, focus on `#review-back`; on P09, key 1–4 then clicks the matching `.rating-button` |

</frozen-after-approval>

## Code Map

- `static/js/app.js` -- the system under test. Sections: dialogs (L27-89), failures (L91-108), P06 (L170-221), P09 flip/rate (L231-279), P08 arrows (L285-295), P05 tabs (L301-335), P07 (L339-357), D10 (L361-372).
- `templates/layouts/base.html:7-23` -- `#dialog` slot, the htmx 2.0.11 vendored script, failure `<template>`s. `templates/layouts/shell.html:13` -- `#page-messages`.
- `templates/components/dialog.html` -- `[data-dialog-close]` and `.dialog-messages`. «Nytt fag» opener: `components/fag_rail.html:32` (`courses:create`).
- `templates/components/tabs.html:7-8` -- P05 tablist (`/topics/<id>/?tab=…`).
- `quiz/question.html`, `components/option_row.html`, `components/feedback_panel.html` -- P06 hooks.
- `components/result_summary.html:11`, `quiz/result.html:21` -- P07.
- `templates/web/weak_quiz.html:7-23` -- D10, opened from P04 (`web:weak_quiz`).
- `review/browse.html:16-28`, `review/session.html:17-30`, `components/flashcard_card.html:7-19` -- P08/P09.
- State helpers to reuse:
  - `sample` fixture and `make_quiz` (`tests/test_quiz.py:70`, `:96`)
  - `grade_all` (`tests/test_result.py:46`)
  - `ready_source`, `cards` (`tests/test_topic_page.py:52`, `tests/test_browse_cards.py:34`)
  - `abc` fixture and `seed`/`pct` (`tests/test_weak_topic_quiz.py:40`, `tests/test_progress.py:32`)
  - `start_review` (`tests/test_review.py:~106`)
  - `student` and `PASSWORD` (`tests/conftest.py`)
- `pyproject.toml:21` -- `addopts = "--disable-socket"`. This blocks `live_server`.
- Login: the form at `/accounts/sign-in/`, or a `force_login` session cookie copied into the browser context.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- add `pytest-playwright` (pinned) to the dev group and register the `browser` marker, deselected by default (`-m "not browser"` in addopts; `-m browser` overrides it) -- the harness.
- [x] `tests/browser/conftest.py` -- mark every test in the folder `browser`. Allow sockets to 127.0.0.1 only. Provide a `logged_in_page(student)` fixture against `live_server`. Fail with a clear message naming `uv run playwright install chromium` when Chromium is missing. Use `transactional_db` so the server thread sees the data -- shared setup.
- [x] `tests/browser/test_dialogs.py`, `test_topic_tabs.py`, `test_quiz_keys.py`, `test_result_strip.py`, `test_topic_picker.py`, `test_cards_keys.py` -- one test per matrix row -- coverage.
- [x] `tests/test_shell.py` (and any other app.js source-regex tests) -- keep the regexes. They still guard the no-build rule -- no change unless redundant.
- [x] `README.md` -- a «Nettlesertester» section with the two commands -- the Examiner can run them.
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- mark the six app.js entries resolved. `sprint-status.yaml` -- set epic-1-retro item 1 to `done` -- bookkeeping.

**Acceptance Criteria:**
- Given Chromium is installed, when the browser tests run, then every matrix row passes and no request leaves 127.0.0.1.
- Given `showModal()` is removed from app.js, when the dialog test runs, then it fails. Do the same mutation check for one P05 key and the D10 listener, then restore.
- Given the default `uv run pytest`, then the existing 902 tests still pass with sockets blocked.

## Implementation Notes

- **Real bug fixed in `app.js` (P07, row «P07 strip»).** Clicking the same strip slot a second time opened the row, but the link's default jump to the unfocusable `details#q-N` then moved focus to `<body>` (Chromium). The click handler now calls `evt.preventDefault()` when the slot's hash already matches, and `openRowForHash()` focuses (and so scrolls to) the summary. Reverting the fix makes `test_p07_strip_slot_opens_and_focuses_its_row_twice` fail.
- **Harness.** `playwright==1.65.2` and `pytest-playwright==0.10.0` pinned in the dev group. `addopts = "--disable-socket -m 'not browser'"`; a later `-m browser` overrides it. `tests/browser/conftest.py` adds the `browser`, `allow_hosts(["127.0.0.1"])` and `django_db(transaction=True)` marks to every test in the folder, so pytest-socket only lets `connect()` reach 127.0.0.1 there and blocks sockets fully everywhere else. `live_server` is overridden to bind 127.0.0.1 (pytest-django's default is `localhost`). A context route aborts and records every browser request to another host, and the test fails if any was made. `logged_in_page(user)` is a factory that copies a `force_login` session cookie into the context. A missing Chromium fails with "Run `uv run playwright install chromium` ...".
- **`DJANGO_ALLOW_ASYNC_UNSAFE`.** Playwright's sync API keeps an asyncio loop on the main thread for the session, which trips Django's async-safety check on ORM calls (fixtures, DB flush). The conftest sets the variable in `pytest_runtest_setup` for browser items only, and a `pytest_runtest_teardown` wrapper restores the previous value after the item's fixture teardown. Every non-browser test therefore keeps the check on, including in a mixed run (`-m ""`).
- **P06 typing guard.** A P06 card has either a text field or radios, never both, so the matrix row on the real free-text card would pass even without the guard. A second test adds a text input to an MC card (in the test DOM only) to reach the guard itself.
- **P08 "does nothing" without sleeps.** The tests record main-frame navigations. A key that must not navigate is followed by one that must, and the test then asserts that only the second navigation happened.
- **Mutation checks (run, then restored):** removing `showModal()` fails all 6 dialog tests (and D10, which opens in a dialog). Removing the P05 `End` branch fails the P05 key test. Removing the D10 footer write fails the D10 test. Removing `!isTyping(target)` fails the injected-field guard test.
- **Source-regex tests** (`test_shell.py`, `test_topic_page.py`, `test_browse_cards.py`) are unchanged.

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence / route |
|---|---|---|---|---|
| 1 | blind, edge | Session log and issues.md say the spec is `in-progress`; the frontmatter says `in-review` | low | True: the log was written before step 4. **patch**: the closing log entry states the final status. |
| 2 | blind | sprint-status `done` and deferred-work `resolved` are written before the review ends | low | True only until this review closes in the same session. Rejected: it becomes accurate at step 5, and the fix is extra bookkeeping. |
| 3 | blind, edge | P07 `preventDefault()` also cancels Ctrl/Cmd/Shift-click on the slot whose hash is already current | low | True, but only for an in-page anchor to the row already shown, opened in a new tab: rare. The fix adds a modifier guard. Rejected under the low + guard rule. |
| 4 | blind, edge | `DJANGO_ALLOW_ASYNC_UNSAFE` never cleared in a mixed run | low | True (`conftest.py` `pytest_runtest_setup`, no teardown). **patch**: restore it in teardown. |
| 5 | blind | Story-11b entry marked resolved promises the Space/Enter flip; only Space is tested | low | True (`test_cards_keys.py`). **patch**: add the Enter flip. |
| 6 | blind, edge | Naming a browser file without `-m browser` silently deselects it | low | True (`addopts -m 'not browser'`). **patch**: one README line. |
| 7 | blind, edge | `live_server` override ignores `--liveserver` / `DJANGO_LIVE_TEST_SERVER_ADDRESS` | low | True, but nobody passes them here, and the fix adds branching. Rejected. |
| 8 | blind | Fixtures imported from other test modules, `ida` redefined | low | The spec asks for existing helpers to be reused, and no caller breaks. Rejected: no named harm. |
| 9 | blind, edge | Off-site guard misses WebSockets and fails in teardown | false | The app opens no WebSocket (no `WebSocket`/`hx-ext`/`ws-connect` in templates or static/js). A teardown ERROR still fails the run red. |
| 10 | blind | Code Map line ranges stale after the P07 fix | low | Rejected: the fix edits this build's spec. |
| 11 | blind, verification | Opt-in tests are not run by the default `uv run pytest`, so a regression in app.js passes it | medium | Pre-verified; this follows from the Author's opt-in decision (frozen). **patch** (docs only): the README says to run `-m browser` before changing app.js. The deferred entries already say «opt-in, uv run pytest -m browser». |
| 12 | blind | Chromium-missing check matches Playwright's error text | low | When the text changes, the original error is re-raised, so nothing is hidden. Rejected. |
| 13 | edge | Hash matches but no `details.result-row` exists, so the click is cancelled with no effect | false | Slots and rows render from the same `rows` loop (`result_summary.html:11`, `quiz/result.html:21`), so every slot hash has its row. |

## Design Notes

htmx swaps are asynchronous, so the tests wait on DOM state (`expect(locator).to_be_visible()`, `to_be_focused()`, `page.wait_for_url`), never on sleeps. The failure rows use `page.route(…)` to abort or return 500 for the one dialog POST.

## Verification

**Commands:**
- `uv run playwright install chromium` -- expected: Chromium present
- `uv run pytest tests/browser -m browser -q` -- expected: all pass
- `uv run pytest -q` -- expected: 902 pass, browser tests deselected
