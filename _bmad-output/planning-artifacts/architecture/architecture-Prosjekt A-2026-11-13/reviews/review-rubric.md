---
title: 'Rubric review: ARCHITECTURE-SPINE.md against the good-spine checklist'
spine: '../ARCHITECTURE-SPINE.md (draft, updated 2026-11-13)'
driving_spec: '../../../prds/prd-Prosjekt A-2026-10-29/prd.md (FR-1..FR-28, NFR-1..NFR-7)'
date: '2026-11-14'
reviewer: 'rubric review (read-only; spine not edited)'
---

# Rubric review: AI Study Buddy v1 spine

## Verdict

**Pass with fixes.** The spine is well aimed. It fixes the real cross-unit seams (gateway, generation lifecycle, Reference shape, ownership, effective Grade, Due-card definition, time, rendering) and covers every PRD capability. Four high findings should be fixed before epics bind to it:
- a retry dead-end in the AD-5 lifecycle;
- undecided SQLite transaction and locking behaviour, which also breaks the AD-3 "failed attempts still count" rule;
- a `ReviewState` write that the dependency graph forbids;
- a `core` module that sits outside the graph and closes an import cycle.

The rest are medium seam gaps (timestamps, exam submission, cross-app delete cleanup, the Sample hash, migrations, backups) and low-severity trimming.

**Totals:** 0 critical, 4 high, 6 medium, 13 low (23 findings).

## Checklist summary

| # | Item | Result |
| --- | --- | --- |
| 1 | Fixes the real divergence points, misses none | Mostly. Misses: claim/stale semantics on retry (R-01), transaction scope (R-02), ReviewState creation (R-04), cross-app delete cleanup (R-05), Answer ordering (R-06), exam submission (R-07), Sample hash location (R-08). |
| 2 | Every Rule enforceable and prevents its divergence | Mostly. AD-3's counting contradicts AD-5's all-or-nothing transaction unless scope is fixed (R-02). AD-7 save-hook is bypassable (R-12). AD-1 has no mechanical check (R-13). |
| 3 | Nothing in Deferred lets units diverge | Yes, with small caveats (R-10, R-15). Host, prompt design, Word library and tuning are safely deferred. |
| 4 | Named tech verified-current | Versions are plausible and memlog-verified 2026-11-13. Pydantic is unpinned (R-14). "Django 6 Tasks with a database-backed worker" needs a third-party backend (R-15). |
| 5 | Covers the spec's capabilities | Yes. Every FR-1..FR-28 and NFR-1..NFR-7 maps to an app and an AD. No orphan capability. |
| 6 | Every owned dimension decided, deferred or open | Partly. Secrets (AD-14), logging (Conventions), environments (APP_ENV, test settings) and host requirements (AD-16) are decided. **Migrations on deploy and first run are silent (R-09).** Backup is deferred with an unsafe method (R-10). Hosted security settings are silent (R-21). |
| 7 | Over-specification and internal consistency | Some bloat in AD-18, AD-9, AD-10, AD-6 and AD-2 (R-20). Inconsistencies between the AD-5 diagram and AD-4 (R-08), AD-3 and AD-4 (R-11), accounts and the theme cookie (R-17), ADOPTED tags (R-18), the ERD (R-19) and AD-13 vs `core/messages.py` (R-23). |

## What is strong (no action)

- The dependency graph with "reachability counts" and the "explicit argument" escape hatch (AD-1) is the right shape for a solo modular monolith.
- The gateway is closed (four operations), there is one schema contract for Mock and Real, and the checks run in a fixed order (AD-2, AD-3, AD-4). These are exactly the seams where `studymat`, `quiz` and `ai` would otherwise drift.
- `Answer.effective_grade`, `Source.effective_status` and `review.services.due_cards` are single read definitions. They close the most common consumer divergence.
- Mock mode runs the real pipeline, with the one planted wrong-page item removed by the real check (AD-4). This makes SM-2 checks 1 and 2 honest.
- AD-12 (UTC storage, Oslo days through `core.time`) and AD-15 (tests named by FR) are short and enforceable.
- The capability map is complete, and the open questions have owners and dates tied to the build-order cut lines.

## Findings

### High

#### R-01 — Retry of a timed-out Source can never be claimed, and a retry looks stale at once
- **Severity:** high
- **Checklist:** 1, 7
- **Issue:**
  - `effective_status` reports a stored `pending` or `generating` older than 5 minutes as `failed (timed_out)`, so the UI offers Retry. But the claim is a conditional UPDATE on the stored status `pending|failed → generating`. A Source whose stored status is still `generating` (a process died mid-run) never matches, so the retry is refused forever.
  - The rule also does not say the claim resets `started_at`. A retry of a Source uploaded hours earlier would at once read as `timed_out` again.
  - Nothing stops a run that overshoots 5 minutes from later writing `ready` over a Source that a newer claim now owns.
  - The state diagram draws `timed_out` as real transitions, but they are only derived on read.
- **Fix:** Set the claim condition to `status='failed' OR (status IN ('pending','generating') AND started_at < now-5min) OR status='pending'`, have it set `started_at=now()`, and make the final `ready`/`failed` write conditional on that same `started_at`.

#### R-02 — SQLite transaction scope and locking are undecided, which breaks AD-3 counting and the AD-16 concurrency goal
- **Severity:** high
- **Checklist:** 1, 2, 6
- **Issue:**
  - AD-5 says the orchestrator "runs the gateway … and saves all … in one transaction". One natural reading wraps the 60–150 s provider call in `transaction.atomic()` (or `ATOMIC_REQUESTS`). With SQLite, the claim UPDATE then holds the database write lock for the whole call. Every other write (answers, ratings, sign-in session updates) hits `database is locked` after the default 5 s, which defeats AD-16's "2 concurrent requests".
  - The same nesting makes the AD-3 counter increment a savepoint. It rolls back when generation fails, which violates "an attempt that fails after it was sent still counts".
  - With Django's default DEFERRED SQLite transactions, AD-3's "check and increment in one transaction" can race across two tabs.
- **Fix:** Add one rule to AD-5 and AD-3:
  - The claim and the counter increment each commit on their own before the send.
  - The provider call runs outside any transaction.
  - Only the final save is atomic.
  - `ATOMIC_REQUESTS` stays off.
  - SQLite runs with WAL, `transaction_mode: IMMEDIATE` and a busy timeout of at least 5 s.

#### R-03 — `core` is outside the dependency graph and closes an import cycle
- **Severity:** high
- **Checklist:** 7, 2
- **Issue:**
  - Every app is meant to use `core` (`core.time`, `core.ownership`, `core.messages`). But the graph says "a dependency the graph doesn't reach is forbidden", and `core` is not in it, so taken literally every use is illegal.
  - `core/messages.py` maps `ai.errors` and `ingestion.errors` to text, so `core` imports `ai` and `ingestion`. Meanwhile `courses` and `accounts` import `core.ownership` and `core.time`. That gives the cycle `courses → core → ai → courses`.
- **Fix:** Add `core` to the graph as a bottom layer that imports no app. Move the error-to-text mapping into `web` (or have typed errors carry a message code that `core.messages` resolves without importing the apps).

#### R-04 — `ReviewState` creation needs an upward write that the graph forbids
- **Severity:** high
- **Checklist:** 1, 7
- **Issue:**
  - AD-11 says "each Flashcard has one `ReviewState`", and the ERD shows `FLASHCARD ||--|| REVIEW_STATE`, with `due_date = null` until the card is introduced. Flashcards are created inside `studymat.services.generate`.
  - `review` owns `ReviewState`, and writes go only through the owner's `services.py`. Since `review → studymat`, `studymat` cannot call `review.services`.
  - The step-1 builder (`studymat`) and the step-2 builder (`review`) will each choose differently: bypass the rule, add a signal, or create the row lazily.
- **Fix:** State in AD-11 that `ReviewState` is created lazily by `review.services.due_cards`/`rate`, and that a missing row means a new, unintroduced card. Change the ERD to `FLASHCARD ||--o| REVIEW_STATE`.

### Medium

#### R-05 — Cross-app delete cleanup contradicts AD-1
- **Severity:** medium
- **Checklist:** 1, 7
- **Issue:**
  - AD-8: "A Quiz left with no QuizQuestions is deleted with them." A database cascade cannot do this. Topic and Source deletes live in `courses.services`, and Question deletes in `studymat`. Neither may import `quiz`.
  - `Quiz.parent_quiz` has no `on_delete` choice.
  - `Review(scope)` pointing at a deleted Course or Topic is undefined.
- **Fix:** Say who does the cleanup. Either a `post_delete` receiver registered in `quiz` (signals flow upward legally), or "empty Quizzes are hidden on read and swept by `quiz`". Fix `parent_quiz` as `SET_NULL` (or `CASCADE`), and say that `Review.scope` stores kind and id without an FK.

#### R-06 — Answers have no timestamp, yet scoring, trend and SM-4 depend on recency
- **Severity:** medium
- **Checklist:** 1
- **Issue:**
  - AD-10 uses "the 20 most recent Answers" and "before versus after the latest non-retry Quiz". SM-4 needs "the next time it comes up". But AD-9's Answer fields have no `answered_at`.
  - Exam Answers are updated in place, so `id` order and `created_at` order disagree.
  - The `quiz` and `progress` builders will choose different ordering keys.
- **Fix:** Add `Answer.answered_at`. It is set when the Answer is saved, or when the exam is submitted for exam Answers. AD-10 orders by it.

#### R-07 — Exam submission and grading time are ambiguous, so unsubmitted exams can leak into the Topic score
- **Severity:** medium
- **Checklist:** 1, 2
- **Issue:**
  - AD-9 says multiple-choice grading is a code comparison "when given", and exam Answers are "updated in place until submission". It is open whether an exam multiple-choice Answer gets its `grade` on save, which would leak it into AD-10 before submission and against FR-18's "no Grade before submission", or only on submission.
  - "Auto-submits on the next request it sees" does not say which request. An exam the Student abandons is never submitted.
- **Fix:** Exam Answers keep `grade = null` until submission. Define `Quiz.effective_submitted_at = submitted_at or (started_at + time_limit if passed)`, read by every consumer the way `effective_status` is, and grade on the first read after it.

#### R-08 — Where the Sample hash lives, and when `needs_key` is set, is undecided
- **Severity:** medium
- **Checklist:** 1, 7
- **Issue:**
  - AD-4 recognises the Sample "by the SHA-256 of its file bytes", but no unit is named to compute it, and no field stores it. The spine never says whether the uploaded file is kept, and a retry reuses only `SourceText`. So at generate or retry time the gateway (`ai` reads `courses`) has nothing to hash unless `ingestion` stored it.
  - The AD-5 diagram has `pending --> failed: needs_key`, as if it is set at upload. The AD-3 order raises `NeedsKey` inside the gateway, after the claim. `ingestion` and `studymat` could each set it.
- **Fix:** Add `Source.content_sha256`, set by `ingestion` at upload, and state that original files are not retained. `needs_key` is set only by the generate path (`generating → failed`). Correct the diagram to match.

#### R-09 — Migrations on deploy and first run are silent
- **Severity:** medium
- **Checklist:** 6
- **Issue:**
  - AD-16's local command is only `uv run manage.py runserver`. A fresh clone has no tables, so NFR-2's 15-minute Examiner path is missing `migrate`. It may also need `DATA_DIR` creation.
  - Nothing says whether the Hosted instance runs migrations on each deploy, or who runs them.
  - Nothing covers migration policy for a database holding the Author's SM-1 data, such as data migrations or no squashing.
- **Fix:** Add to AD-16:
  - Locally, run `uv run manage.py migrate` and then `runserver`. `DATA_DIR` is created on start.
  - On the Hosted instance, every deploy runs `migrate` before reload, after a database backup.

#### R-10 — The deferred backup method is unsafe, and there is no fallback if the host fails AD-16
- **Severity:** medium
- **Checklist:** 6, 3
- **Issue:**
  - Deferred says backups mean "copying `db.sqlite3`". With a live writer, and especially with WAL (R-02), a plain file copy can be torn or miss the `-wal` file.
  - FR-25's "data survives new deployments" and SM-1/SM-4 evidence live only in that file.
  - OQ-3 may well fail on the free PythonAnywhere candidate (allowlist, concurrency). The spine says nothing about what happens then.
- **Fix:** Fix the backup method now as `sqlite3 .backup` or `VACUUM INTO`, run before each deploy and daily. Add one line: "if no zero-cost host meets AD-16, FR-25 is dropped (it is Should), with no architecture change".

### Low

#### R-11 — The AD-3 check order contradicts AD-4 for Mock grading and simpler explanations
- **Severity:** low
- **Checklist:** 7, 2
- **Issue:**
  - AD-3 says "every gateway operation" starts with "Mock mode with a non-Sample Source raises `NeedsKey`". AD-4 gives Mock mode a word-overlap grader. Grading a Question from a Real-generated Source after the Key is removed would raise `NeedsKey` instead.
  - AD-3's step 3 nominally applies to `grade_free_text`, while it "never counts".
  - Mock Simpler explanations are recorded for Key concepts only. A Flashcard request on the Sample has no defined result.
- **Fix:** Scope steps 1 and 3 to the three generation operations, and say what a Mock Flashcard Simpler explanation returns (for example, an `InvalidFormat` error or a recording).

#### R-12 — The AD-7 rule that a child's `student` equals its parent's is bypassable
- **Severity:** low
- **Checklist:** 2
- **Issue:** "On save" enforcement is skipped by `bulk_create`, which the all-at-once save in AD-5 is likely to use.
- **Fix:** Have services set `student` from the parent explicitly, and add one test per owned model that checks the equality after generation.

#### R-13 — The AD-1 graph has no mechanical check
- **Severity:** low
- **Checklist:** 2
- **Issue:** "Apps import only along the graph" and "only `ai` imports `anthropic`" rely on discipline.
- **Fix:** Add an import-linter contract, or one pytest test that walks the imports, under AD-15.

#### R-14 — Pydantic and the network-blocking tool are not in the Stack
- **Severity:** low
- **Checklist:** 4
- **Issue:** `ai/schemas.py` uses Pydantic directly, but it arrives only transitively ("pydantic < 3"). AD-15's "network access blocked" names no tool.
- **Fix:** Pin `pydantic` 2.x as a direct dependency, and name the blocker (for example `pytest-socket` with its version).

#### R-15 — The deferred FR-26 route assumes a Django core feature that does not exist
- **Severity:** low
- **Checklist:** 4, 3
- **Issue:**
  - Django 6 ships the Tasks API with only the immediate and dummy backends. A "database-backed worker" means the third-party `django-tasks` package.
  - A queued task that waits more than 5 minutes would read as `timed_out` before it is claimed.
- **Fix:** Name `django-tasks` (DatabaseBackend) as the expected backend. Note that the worker performs the claim, so the 5-minute window starts at the claim.

#### R-16 — Introducing Due cards as a side effect of a GET can exceed 20 a day
- **Severity:** low
- **Checklist:** 1
- **Issue:** `due_cards()` "does the day's introductions" and is called from Home, the Course overview, Topic pages and the Review. Two concurrent reads can each introduce up to the cap.
- **Fix:** Compute the cap as `20 − count(introduced_on = today)` inside an IMMEDIATE transaction, so introduction is idempotent per Oslo day.

#### R-17 — Theme preference is owned twice
- **Severity:** low
- **Checklist:** 7
- **Issue:** The app table gives `accounts` the "theme preference", but the conventions say the override is a `theme` cookie rendered server-side.
- **Fix:** Pick one. The cookie is enough, so drop it from `accounts`.

#### R-18 — ADOPTED status tags are inconsistent
- **Severity:** low
- **Checklist:** 7
- **Issue:** AD-14 to AD-18 lack `[ADOPTED]`. The memlog records that AD-14 to AD-16 were accepted ("ser bra ut, fortsett") and that AD-17 and AD-18 were applied at Finalize.
- **Fix:** Tag them `[ADOPTED]`, or mark them `[PROPOSED]` and list them for confirmation.

#### R-19 — The ERD has gaps against the ADs
- **Severity:** low
- **Checklist:** 7
- **Issue:** The ERD lacks the privacy acceptance entity (AD-7, AD-17), the `ANSWER` to `QUIZ_QUESTION` uniqueness link and the `QUIZ`–`TOPIC` relation through Questions. It also shows `REVIEW_STATE` as mandatory (see R-04).
- **Fix:** Add `PRIVACY_ACCEPTANCE`, note `ANSWER unique(quiz, question)`, and change `REVIEW_STATE` to optional.

#### R-20 — Over-specification bloats the spine (about 31 KB)
- **Severity:** low
- **Checklist:** 7
- **Issue:** Several rules state detail that a builder can read off code, or that one unit owns alone:
  - AD-18: `popover` menus, `autofocus`, `data-key`, the exact `hx-sync` string;
  - AD-9: the full Question and Quiz field lists;
  - AD-10: the `NextStep(...)` field signature;
  - AD-6: the itemised normalisation steps, owned only by `studymat`;
  - AD-2: lower-casing enums;
  - Conventions: CSS file names.
- **Fix:** Keep the invariant sentence in each case (one dialog slot and the OOB region names; `effective_grade`; one `next_step()` and one partial; "normalise both sides identically"). Move the field lists and attribute recipes to the seed or to story notes.

#### R-21 — Hosted security settings are silent
- **Severity:** low
- **Checklist:** 6
- **Issue:** The AD-14 non-local guard covers only `SECRET_KEY` and `DEBUG`. Nothing is decided for `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, secure and HTTPS-only cookies, or whether Django admin is exposed on the Hosted instance.
- **Fix:** Extend the AD-14 guard: non-local requires `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` from env, `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` on, and admin off (or staff-only).

#### R-22 — Two concurrent requests is a thin floor
- **Severity:** low
- **Checklist:** 6
- **Issue:** One 150 s generation plus one 15 s Free-text grading occupies both workers, and the next page load blocks.
- **Fix:** State the floor as at least 3 concurrent requests (or threaded workers), or accept the risk explicitly until FR-26.

#### R-23 — AD-13 and the Conventions disagree on where Norwegian text lives
- **Severity:** low
- **Checklist:** 7
- **Issue:** AD-13 says interface text is Norwegian "in templates". The Conventions put all error text in `core/messages.py`, which is Python.
- **Fix:** Reword AD-13 to "in templates and `core/messages.py`, nowhere else".

## Capability coverage check (item 5)

Every FR-1..FR-28 and NFR-1..NFR-7 has a row in the capability map, an owning app and at least one governing AD. The Should items (FR-5, FR-18, FR-19, FR-25, FR-26) are either decided enough to build (FR-18, FR-19) or deferred with their invariants already in place (FR-5 through AD-6 `heading`/`label`; FR-25 through AD-16 and OQ-3; FR-26 through the AD-5 claim). The SM-1 and SM-4 measurement needs are supported once R-06 adds `Answer.answered_at`.

Two quiet PRD points are covered implicitly and could be made explicit later:
- the 10 MB and 150,000-character limits are enforced before processing, through Django upload limits (seed);
- the FR-27 "newest Quiz only" Retry rule.
