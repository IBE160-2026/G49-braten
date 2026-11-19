---
title: 'Examiner path end to end and the README'
type: 'feature'
created: '2026-11-19'
baseline_commit: '3509f6b5ab6ec1fc769b01dcdb12b41399fac7e7'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/SETUP-GUIDE.md'
  - '{project-root}/_bmad-output/specs/spec-ai-study-buddy/success-metrics.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The README is a nine-line group header, so the Examiner cannot run the app from a fresh clone (NFR-2), and nothing proves the whole UJ-5 path or maps each SM-2 check to its evidence (CAP-12).

**Approach:** Write the README from Part A of the setup guide (plus a short Real-mode section from B1), add one end-to-end Mock-mode test that walks UJ-5 through the real views, add a test-backed SM-2 checklist, and run the README's commands from a fresh local clone, recording the result in `docs/quality/`.

## Boundaries & Constraints

**Always:**
- **README** (`README.md`): keep the course header and «Medlemmer». Sections, in order: what the app is (two or three sentences); what you need (git, uv, with install commands); start the app (the setup guide's commands, Windows `copy` variant, the Mock-mode banner); try every core function (UJ-5 steps 1–7 as in Part A, with the Norwegian labels the app shows: «Bruk eksempeldokumentet», «Test deg selv», «Øv på feilene», etc.); run the tests (`uv run pytest`, no Key or network, sockets blocked; the NFR-5 areas covered, each with an example test-file name); SM-2 checklist (a table: check 1–10, R or T, the README step or test names); if something goes wrong (the setup guide's table); Real mode (B1 steps 1–6 short, `AI_PROVIDER=mock`, Key-leak advice); project documents (links to `_bmad-output/specs/spec-ai-study-buddy/SPEC.md`, the architecture spine, `docs/quality/`). Every command and label must match the code as it is.
- **UJ-5 test** (`tests/test_examiner_path.py`, named `test_uj5_…`/`test_sm2_…`): Mock mode, Django test client, through views only (no service shortcuts except the clock): sign up → Mock banner visible → create Course and Topic → «Bruk eksempeldokumentet» → the Topic shows Summary, ≥ 5 Key concepts, ≥ 10 Flashcards and «1 element ble fjernet» (or the app's exact removed note) → start a Quiz, answer every Question with at least one wrong → result → «Øv på feilene» holds exactly the missed Questions → answer them → Review from «I dag» rating every card until «Repetisjonen er ferdig» → sign out and in, data unchanged. A second test uploads another PDF and asserts it is stored with the `needs_key` message. No socket, no Key; NFR-3's 5 s Mock budget asserted per request.
- **SM-2 coverage** (`tests/test_sm2_checklist.py`): one test per check 7–10 that imports and asserts the existence of the named covering tests (e.g. `test_fr15_…`, `test_fr17_…`, the NFR-7 limit test, `test_fr28_…`), so renaming a covering test fails here; checks 1–6 point to `test_uj5_…` and the README steps.
- **Fresh clone** (by the implementer, not a test): `git clone` this repo to a temp dir, follow the README exactly (`cp .env.example .env`, `uv sync`, `uv run manage.py migrate`, `runserver` on a free port, fetch `/` and the sign-up page), run `uv run pytest` there, note wall-clock time and any deviation, fix the README or code for every deviation. Record date, OS, uv and Python versions, times and result in `docs/quality/nfr2-fresh-clone.md`, with a line that the run on another machine is still the Author's.
- The README is in Norwegian bokmål, addressing the reader as «du» (Author's decision 2026-11-19); code identifiers, test names and `docs/quality/` notes are English.

**Never:** new app features; changing FR behaviour to make the test pass (a failing step is a bug to fix and log); the Author's Real-mode measurements (OQ-1/OQ-2, NFR-3 Real, NFR-5 content check, SM-3); hosting (B3).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| UJ-5 happy path | fresh DB, no Key | every step above passes; one item removed | N/A |
| Other PDF | upload a non-sample PDF in Mock mode | Source stored, `needs_key` message, no Study material | N/A |
| Persistence | sign out, sign in | Courses, Topics, Study material, Answers, review dates unchanged | N/A |
| Covering test renamed | a check 7–10 test missing | `test_sm2_checklist` fails naming the check | N/A |
| Mock budget | any UJ-5 request | under 5 s | N/A |
| Fresh clone | README followed verbatim | app serves `/`; tests pass; deviations fixed | README or code corrected |

</frozen-after-approval>

## Code Map

- `README.md` -- nine lines today (course header, «Medlemmer»); rewrite around them.
- `SETUP-GUIDE.md` (context) -- Part A is the README's source; B1 for Real mode; the env-variable table matches `.env.example`.
- `.env.example`, `config/settings.py:107` -- `DATA_DIR` is created on start, so `migrate` works on a fresh clone.
- `studymat/views.py` (`use_sample`), `templates/studymat/add_source.html` -- «Bruk eksempeldokumentet»; `core/messages.py` `needs_key`.
- `ai/mock/` -- recorded responses; the one planted wrong Reference (AD-4).
- Existing helpers to reuse in tests: `tests/conftest.py` fixtures and the flows in `tests/test_quiz.py`, `tests/test_result.py`, `tests/test_review.py`, `tests/test_upload.py` (or the nearest upload test), `tests/test_next_step.py`; the NFR-7 limit test (find by `daily_limit`).
- `docs/quality/` -- `oq1-pdf-extraction.md` exists; add `nfr2-fresh-clone.md`.

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_examiner_path.py` -- UJ-5 end to end and the other-PDF case.
- [x] `tests/test_sm2_checklist.py` -- checks 7–10 tied to named tests.
- [x] `README.md` -- the sections above.
- [x] Fresh-clone run; fix deviations; `docs/quality/nfr2-fresh-clone.md`.

**Acceptance Criteria:**
- Given a fresh clone and only the README, when its commands are run, then the app serves the Mock-mode banner and `uv run pytest` passes.
- Given the README's SM-2 table, when each T row's test names are searched, then each exists and passes.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|
| 1 | VG | No verification gaps | — | Reported none | — |
| 2 | BH, ECH | SM-2 check 4 marked R but the README gives no PDF over 50 pages; checklist comment says 1–6 are walked by UJ-5 | medium | The Examiner cannot do check 4 from the README alone | patch |
| 3 | BH, ECH | `test_sm2_checklist` checks existence, not passing; skip/xfail not detected | false | The spec asks for existence; passing is the full run's job; no covering test is marked | reject |
| 4 | BH, ECH | README table parsed loosely; a README row may cite a test not in `COVERING_TESTS`; duplicate rows overwrite | low | `readme_table_rows` matches any numbered row and checks only R/T | patch |
| 5 | BH, ECH | Fresh-clone note says «passed» and «No command deviated» though it cloned locally, copied files and had Python and a warm cache | medium | Stated in the note's Setup row but not as deviations; the GitHub URL and cold install were never run | patch |
| 6 | BH | Spec in-review, sprint-status in-progress | false | The workflow moves sprint-status in step 5 | reject |
| 7 | BH, ECH | UJ-5 test: `% 4`, bare StopIteration, unchecked regex matches, unchecked retry POSTs | low | Failures would surface as unrelated errors; direct asserts | patch |
| 8 | ECH | A `not_graded` Answer would break the history count | false | Mock grading never yields `not_graded`; MC is graded in code | reject |
| 9 | BH | Persistence snapshot partial and unordered | low | Lists lack `order_by`; Quiz, Rating rows not in it | patch (ordering) |
| 10 | BH | NFR-5 table and SM-2 table cite different files for NFR-7 | low | `tests/test_generation.py` missing from the NFR-7 row | patch |
| 11 | BH | README lacks Ctrl+C, the 15-minute target, and that shell env vars override `.env` | low | `load_dotenv(override=False)`; a shell Key would silently keep Real/Mock mode | patch (Ctrl+C, override) |
| 12 | BH | Privacy notice absent in Mock mode not tested here | false | Covered by story 10's `tests/test_privacy_notice.py` | reject |
| 13 | ECH | README states the generation cost without a measurement | low | From the setup guide (research A2); measurement is the Author's (OQ-2) | reject |

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, socket disabled.
- `uv run python manage.py check` -- expected: no issues.

**Manual checks (if no CLI):**
- The README renders on GitHub (headings, table, code blocks); the fresh-clone note exists.
