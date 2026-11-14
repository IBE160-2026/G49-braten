# Adversarial review: ARCHITECTURE-SPINE.md (AI Study Buddy v1)

- **Reviewed:** `ARCHITECTURE-SPINE.md` (draft, 18 ADs, 2026-11-13), against `prd.md` (final, 2026-11-13) as the behaviour authority.
- **Lens:** construct two units one level down (epics/stories built by separate agents) that each obey every AD to the letter yet build incompatibly. Each pair is a hole to close with a new or tightened AD.
- **Units used:** U-UP upload & ingestion · U-GEN generation & Reference check · U-TOPIC Topic page & Study material view · U-QUIZ Quiz practice · U-RETRY Retry rounds & Quiz history · U-FT Free-text grading & override · U-REV Flashcards & Review · U-PROG scores, Weak topics & Next step · U-EXAM Exam mode · U-SIMP Simpler explanation · U-DEL delete items · U-MOCK Mock mode & Sample document · U-HOST Hosted instance.
- **The spine was not edited.**

## Verdict

The spine pins the data shapes well (AD-6, AD-9, AD-11), but it leaves the **transaction boundaries around the paid call**, the **gateway's call signatures** and **who may write across the dependency graph** open. Several ADs also require imports that the AD-1 graph forbids. Separately built units would most likely clash on those three points rather than on field names.

| Severity | Count |
| --- | --- |
| Critical | 2 |
| High | 7 |
| Medium | 9 |
| Low | 7 |
| **Total** | **25** |

---

## Part 1: The dependency graph against AD-1 and the app table

AD-1 says: "A dependency the graph doesn't reach is forbidden, including any upward one." Taken literally, the following ADs or PRD needs require an import, or an equivalent read, that the graph does not allow.

| # | Required by | Needed edge | Graph says | Hole |
| --- | --- | --- | --- | --- |
| G-1 | AD-7 (`core.ownership`), AD-12 (`core.time`), Conventions (`core/messages.py`) | every app → `core`; and `core.messages` → `ai.errors`, `ingestion.errors` | `core` is not in the graph, so every import of it is literally forbidden. If `core.messages` imports the error classes, the bottom layer depends on mid-level apps (and `ai` imports `core.time`) | A-12 |
| G-2 | AD-2 ("sends only marked `SourceText`"), AD-6 (markers fixed in `ai`), FR-12 (grade against "Source text at the Question's Reference") | `ai` → `ingestion` (SourceText), `ai` → `quiz`/`studymat` (Answer, Question) | `ai` → `courses` only | A-3 |
| G-3 | AD-11 + ERD `FLASHCARD \|\|--\|\| REVIEW_STATE` (every Flashcard has exactly one ReviewState) | `studymat` (creates Flashcards in AD-5's one transaction) → `review` | `review` → `studymat` only; upward is forbidden | A-4 |
| G-4 | AD-8 ("A Quiz left with no QuizQuestions is deleted with them") | `studymat.services.delete_question`, `courses.services.delete_topic/delete_source` → `quiz` | `quiz` → `studymat`; neither `studymat` nor `courses` reaches `quiz` | A-6 |
| G-5 | AD-18 (a mutating POST may answer with OOB `band`, `tab-counts`) + AD-1 ("feature apps own their own forms") | `quiz`/`review`/`studymat`/`courses` views → `progress` (band), and → each other (tab counts) | All upward or sideways: forbidden | A-5 |
| G-6 | AD-17 (notice shown only in Real mode) + AD-5 step 1 (`ingestion` creates the Source) | the upload/notice view → `ai.gateway.mode()` | If the view is in `ingestion` or `accounts`: forbidden. Only `studymat`/`web` reach `ai` | A-15 |
| G-7 | FR-13/FR-18 result score, FR-27 history row vs AD-10 (weights are "constants in `progress/rules.py`") | `quiz` → `progress.rules` | `progress` → `quiz`; upward is forbidden, so `quiz` must copy the weights | A-16 |
| G-8 | `web → ai` edge | none | Redundant (`web → progress → quiz → ai` already reaches it). Harmless; keep it for readability or drop it | n/a |

Also note the **reverse-accessor loophole**: Django lets `ai` call `source.sourcetext_set.all()` or `answer.question.source` with no `import` statement, so a unit can "read upward" while technically obeying "import only along the graph". AD-1 should say that the graph governs **model access**, not only `import` lines (see A-3).

---

## Part 2: Holes (clashing unit pairs)

### Critical

#### A-1: The transaction around the paid call is undefined, so the counter can roll back, the claim can stay invisible, and SQLite can lock for 150 s

- **Units:** U-GEN (`studymat.services.generate`) × the `ai` gateway part of U-GEN/U-MOCK (AD-3 counter). The same pattern applies to U-SIMP and to `regenerate_summary`.
- **U-GEN obeys:** Conventions say "Multi-row writes run in `transaction.atomic()`". AD-5 says generate "claims… then runs the gateway, validation and the Reference check, and saves all… in one transaction." A literal reader wraps the whole `generate()` in one `atomic()`: claim, gateway call, Reference check, save.
- **`ai` obeys:** AD-3 step 3 says "check and increment the Student's counter for today in one transaction". The `ai` builder uses its own `atomic()`, which nests as a savepoint inside U-GEN's block.
- **Clash:**
  1. A `Refused`, `Truncated` or `InvalidFormat` raised after the send rolls back the outer block, **including the counter increment**. That breaks AD-3 ("an attempt that fails after it was sent still counts") and SM-2 check 9.
  2. The `pending → generating` claim is not committed until the end, so a second tab sees `pending` and its own conditional UPDATE blocks on the SQLite write lock. It then fails with `database is locked`, not the clean "refuse" that AD-5 promises.
  3. The SQLite write lock is held for the whole provider call (up to the 150 s floor in AD-16), so every other writer stalls: `rate()`, saving an Answer, the counter of another request. That cancels the "2 concurrent requests" guarantee.
  4. The `failed` status and reason are written inside the rolled-back block, so they vanish and the Source stays `generating` until it goes stale.
  5. With SQLite's default deferred transactions, two concurrent increments can both read 19 and both write 20, so the limit leaks. `ATOMIC_REQUESTS=True`, a common Django default in tutorials, triggers all of the above for every view.
- **Severity:** Critical. It breaks NFR-7 and FR-9 and makes the AD-16 envelope meaningless.
- **Tightening (new AD-5/AD-3 clause, "Transaction boundaries"):**
  - `ATOMIC_REQUESTS = False`. **No gateway call runs inside a transaction.** `ai.gateway` asserts `not connection.in_atomic_block`.
  - The claim is its own committed statement and sets a fresh `started_at`.
  - The counter is incremented in its own committed transaction by one conditional statement (`UPDATE … SET count = count + 1 WHERE count < LIMIT`, or an insert for the first call of the day), never read-then-write.
  - The final save is one `atomic()` that holds only the writes.
  - The failure path (`failed` + reason) is a separate committed write after the error.
  - SQLite runs with `"transaction_mode": "IMMEDIATE"` and a busy timeout.

#### A-2: A timed-out Source can never be retried, and a retried Source times out at once

- **Units:** U-TOPIC (Sources area, renders status and the retry button) × U-GEN (claim).
- **U-TOPIC obeys:** AD-5: "Everyone reads `Source.effective_status`", which reports `generating` older than 5 minutes as `failed (timed_out)`. It shows "failed" with a retry button (FR-9: "The Student can retry generation").
- **U-GEN obeys:** the claim is literally "one conditional UPDATE (`pending|failed → generating`)". The stored status of a timed-out Source is still `generating`, so no row matches and the claim refuses.
- **Clash:** the Student sees "failed, try again", presses it, and nothing happens, forever. That is the FR-9 "never as generating forever" failure in a new form. The reverse case: a Source that failed an hour ago is claimed, but AD-5 never says the claim resets `started_at` (it is set at upload). `effective_status` immediately reports the running retry as `timed_out`, so the row shows "failed" while a paid call is running, and the Student presses retry again.
- **Severity:** Critical. FR-9 is Must, and this is the only recovery path.
- **Tightening:** the claim condition is defined on the *effective* status: `WHERE status = 'failed' OR status = 'pending' OR (status = 'generating' AND started_at < now - 5 min)`, and the claim sets `started_at = now()`. `effective_status` and the claim share one predicate, written once in `courses` (for example `Source.objects.claimable()`).

### High

#### A-3: Gateway call signatures are unspecified, so `ai` either reads upward or the callers build incompatible payloads

- **Units:** U-FT (`quiz` calls `grade_free_text`) and U-GEN/U-SIMP (`studymat` calls the other three) × the `ai` unit.
- **`ai` unit obeys:** AD-2 lists four operation names; AD-6 says markers are "fixed in `ai`" and the adapter "sends only marked `SourceText`". It writes `generate_study_material(source)` and builds the marked prompt itself via `source.sourcetext_set` (a reverse accessor, so no forbidden `import`), and `grade_free_text(answer)` walking `answer.question.source…`.
- **U-FT obeys:** AD-1: "A lower app needs data from a higher one only as an explicit argument." It calls `grade_free_text(student, prompt=…, model_answer=…, answer_text=…, reference_text=…)`.
- **Clash:** the two signatures don't fit. Even if they are unified on model instances, `ai` silently depends on `ingestion`, `studymat` and `quiz` models (G-2), so renaming a `related_name` in `ingestion` breaks `ai`. The privacy and NeedsKey checks (AD-3 step 1, AD-17) also need to know the Source (Sample or not) and the Student for every operation, and nothing says how they reach the gateway.
- **Severity:** High.
- **Tightening (AD-2):** every gateway operation takes `student` plus one request DTO from `ai/schemas.py`, for example `GenerateRequest(source_id, source_sha256, language, detail_level, locations: list[LocationText])` and `GradeRequest(source_id, source_sha256, language, question, model_answer, reference_text, answer_text)`. Callers build the DTOs, and `ai` never touches a model above `courses`. Marker insertion lives in `ai` and works on `locations`. AD-1 adds: "The graph governs model access, including reverse relations and attribute traversal, not only `import` lines."

#### A-4: Nobody may create ReviewState, and "the only writer" contradicts "does the day's introductions"

- **Units:** U-GEN (creates Flashcards) × U-REV (ReviewState, Due cards) × U-PROG (Due counts, next Due date).
- **U-GEN obeys:** AD-5 saves "all Study material" in one transaction. It cannot import `review` (G-3), so it creates no ReviewState.
- **U-REV obeys:** AD-11 says `rate()` is "the only writer", so `due_cards()` must not write. Yet AD-11 also says `due_cards()` "does the day's introductions". One builder creates ReviewState lazily inside `due_cards()` on a GET. Another adds a `post_save` signal on Flashcard. A third reads "only writer" literally and makes `rate()` create the row on the first rating, so new cards never get due.
- **U-PROG obeys:** "Forecasts count only non-null dates." It counts ReviewState rows.
- **Clash:**
  1. Depending on which builder wins, a Flashcard can have no ReviewState, so it never enters Due today (FR-15, SM-2 check 7).
  2. Introductions depend on which page was visited first: is the scope of `due_cards(student, scope=topic)` the scope of the *introduction*, or only of the *filter*? A Topic Review could introduce 20 cards from that Topic, and Home would then see none from other Courses that day.
  3. Two concurrent GETs (Home and an HTMX refresh) both read "0 introduced today" and both introduce. That is harmless only if both choose the same 20, which nothing guarantees.
- **Severity:** High.
- **Tightening (AD-11):**
  - ReviewState is created **in `review`** by a `post_save` receiver on `studymat.Flashcard`, registered in `review.apps.ready()`. This is legal because `review` → `studymat`. The new row has `box = 1, due_date = null`.
  - `review.services` has exactly two writers: `introduce_today(student)` (idempotent, global generation order, guarded by a per-Student-per-day marker) and `rate()`.
  - `due_cards(student, scope)` calls `introduce_today(student)` first, then **filters** by scope. The scope never changes which cards are introduced.

#### A-5: OOB composite regions force feature views to import upward

- **Units:** U-QUIZ, U-REV, U-DEL, U-UP (feature POSTs on composite pages) × U-PROG and the `web` pages (band, tab counts).
- **Feature units obey:** AD-1 says "Feature apps own their own forms, dialogs and session pages." AD-18 says a mutating POST may answer with "one named region plus listed `hx-swap-oob` regions (`band`, `tab-counts`, …)".
- **Clash:**
  - U-DEL deletes a Flashcard on the Topic page (`studymat` view) and wants to refresh `tab-counts`, which include Due counts (`review`) and Quiz counts (`quiz`). `studymat` can reach neither.
  - U-REV's `rate()` view wants to refresh `band` (Next step on Home), but `review` cannot reach `progress`.
  - One builder breaks AD-1 to do it. Another answers with `HX-Location`. A third uses `HX-Trigger` plus a region that re-fetches itself, which is a lazy load and breaks AD-13.
  - The result is three refresh styles, which AD-18 exists to prevent.
- **Severity:** High.
- **Tightening (AD-18):** "A region whose content needs data from an app the view can't reach (`band`, `tab-counts`) is emitted only by `web` views. A feature-app POST that changes such data answers with `HX-Location`. A view emits only the OOB regions whose data its own app can reach." Optionally give `web` thin POST wrappers for the high-frequency cases, which call the feature service and render the composites.

#### A-6: Empty Quizzes have no legal deleter, and history divides by zero

- **Units:** U-DEL (`studymat.services.delete_question`), plus Topic/Source deletion in `courses` × U-RETRY (Quiz history and result).
- **U-DEL obeys:** AD-8 says cascade delete; QuizQuestion and Answers go with the Question. U-DEL cannot import `quiz` (G-4), so it does nothing more.
- **U-RETRY obeys:** AD-8 says "A Quiz left with no QuizQuestions is deleted with them", so it assumes none exist and computes `correct / total`.
- **Clash:** deleting the only Question of a Retry round, or a Topic that a one-Topic Quiz drew from (the Quiz FK is to the Course, so the Quiz survives), leaves a Quiz with 0 QuizQuestions. The history row crashes on 0/0 or shows "0 of 0". "Newest Quiz" in FR-27 may now be an empty one, which hides the real Retry button. The `parent_quiz` `on_delete` is also unstated.
- **Severity:** High.
- **Tightening (AD-8):** "`quiz` owns empty-Quiz cleanup through a `post_delete` receiver on `QuizQuestion` (registered in `quiz.apps.ready()`), which deletes the Quiz when its last QuizQuestion goes. `parent_quiz` uses `on_delete=SET_NULL`. History and result code still guard `total == 0`."

#### A-7: "The 20 most recent Answers" and "the latest Quiz" have no timestamp, and `effective_grade` has no query form

- **Units:** U-QUIZ, U-FT, U-EXAM (write Answers) × U-PROG (Topic score, trend) × U-RETRY (history order "newest first").
- **Writer units obey:** AD-9 lists the Answer fields with no timestamp. One adds `created_at`. U-EXAM, which "updates Answers in place", adds `updated_at = auto_now`. U-FT's override saves the row again, which bumps `updated_at`.
- **U-PROG obeys:** AD-10: "20 most recent Answers… whose `effective_grade` is neither null nor `not_graded`." It orders by `-id`, or by whatever field exists. Because `effective_grade` is a Python property (AD-9 says only that every consumer "reads" it), U-PROG either loads every Answer in the Topic into Python, or filters on `grade` in SQL and **ignores overrides**, which breaks FR-12 and FR-16.
- **Clash:** overriding an old Answer moves it into or out of the window, depending on the field used. The trend ("latest non-retry Quiz") needs a Quiz timestamp, but AD-9 gives only exam Quizzes `started_at`. History order and the date column likewise have no field.
- **Severity:** High. Topic score is SM-2 check 8 and the base of FR-17 and FR-28.
- **Tightening (AD-9/AD-10):**
  - `Quiz.started_at` exists for every kind (set by `quiz.services.start`).
  - `Answer.answered_at` is set once, at first save, and never changes on regrade, override or exam edit.
  - "Most recent" means `answered_at` descending, ties broken by `id`.
  - `quiz` exposes the single query form, `Answer.objects.with_effective_grade()` (a `Coalesce(override_grade, grade)` annotation). Every consumer uses it, and filtering on `grade` directly is forbidden.

#### A-8: Exam Free-text grading "one request per Answer" contradicts "no lazy loading", and in-progress exams leak into scores

- **Units:** U-EXAM × U-PROG (and AD-13 for every page).
- **U-EXAM obeys:** AD-9: "After submission, the result page grades each Free-text Answer with its own request." It renders pending cells with `hx-trigger="load"` and `hx-get` to the grade endpoint. That breaks AD-13 ("no lazily loaded sections") and turns a GET into a mutation (AD-18 speaks of mutating POSTs). A builder who honours AD-13 instead grades in the page request: 20 Free-text Answers × 15 s = 300 s, which is over AD-16's 150 s floor.
- **Second clash:** AD-9 does not say when Multiple-choice Answers in an exam get their Grade. If they are graded at save (the "comparison in code" path shared with practice), U-PROG counts them while the exam is still running, and the Home band changes mid-exam. If they are graded at submit, an exam that is abandoned and never revisited stays ungraded forever, because auto-submit happens only "on the next request it sees", and the spine doesn't say whose request.
- **Severity:** High. FR-18 is Should, but the fix is cheap and the contradiction is real.
- **Tightening:**
  - AD-13 adds a named exception: "A pending-Grade cell may self-trigger one POST with `hx-trigger="load"`, and nothing else is lazy."
  - AD-9 adds `Quiz.effective_submitted_at` (submitted, or `started_at + time_limit` if overdue), derived like `effective_status`. `quiz.services.submit()` grades Multiple-choice Answers in code at submission. AD-10 counts exam Answers only once `effective_submitted_at` is set.

#### A-9: How the Sample document is recognised is not tied to anything stored

- **Units:** U-UP (`ingestion`) × U-MOCK (`ai/mock`, AD-3 step 1, AD-4).
- **U-UP obeys:** AD-5 step 1 stores `SourceText` rows and a `pending` Source. Nothing says to keep the file bytes or a hash, and AD-18 says the server "keeps nothing" for rejected files. U-UP stores no hash.
- **U-MOCK obeys:** AD-4 recognises the Sample "by the SHA-256 of its file bytes". At generate time it has no bytes. One builder re-hashes the concatenated `SourceText`, which never matches the recorded hash. Another adds a `sha256` field to Source and expects `ingestion` to fill it, which nothing tells `ingestion` to do. `ingestion` also cannot read the Sample hash in `ai/mock` to mark `needs_key` at upload (`ingestion` ↛ `ai`), and the AD-5 diagram's `pending → failed: needs_key` doesn't say which step does it.
- **Clash:** in the most likely build, the Sample is never recognised, so the Examiner's path (UJ-5, SM-2 checks 1–3) gets `NeedsKey`.
- **Severity:** High.
- **Tightening (AD-4/AD-5):** "`ingestion` computes `sha256` over the uploaded file bytes and stores it on `Source.content_sha256` (a `courses` field) at step 1. Pasted text hashes its UTF-8 bytes. `ai` compares only that field. `needs_key` is set only at step 2 by the orchestrator, after the gateway raises `NeedsKey`."

### Medium

#### A-10: Failure reasons have no shared vocabulary

- **Units:** U-GEN (writes the reason) × U-TOPIC (renders the message for a failed Source).
- **U-GEN obeys:** AD-5: "sets `failed` and stores a reason code." Only `needs_key` and `timed_out` are named, so it stores `type(exc).__name__` (`"RateLimited"`).
- **U-TOPIC obeys:** Conventions: `core/messages.py` maps **exceptions** to text. On a later page load there is no exception, only a stored string, and U-TOPIC expects lowercase TextChoices (`rate_limited`).
- **Clash:** every failed Source renders a fallback message, which breaks FR-9 ("a message says what failed").
- **Tightening:** a closed `courses.FailureReason` TextChoices (`needs_key`, `timed_out`, `rate_limited`, `refused`, `truncated`, `invalid_format`, `key_rejected`, `provider_unavailable`, `daily_limit`, `privacy_not_accepted`). Every typed error carries `code`, matching one value. `core.messages` is keyed by code (see A-12).

#### A-11: NextStep URLs point at mutating endpoints, and the shapes of `scope` and `topic_ids` are open

- **Units:** U-PROG (builds `NextStep.url`) × U-QUIZ/U-REV (start endpoints).
- **U-PROG obeys:** AD-10 fixes the `NextStep(… url …)` shape, rendered by `components/next_step_band.html` as a link. It builds `/quizzes/start/?topics=3,7`. It passes `scope` as a `Course` instance or `None`.
- **U-QUIZ obeys:** starting a Quiz creates rows, so it is a POST (AD-18, CSRF) with `topic_ids` as repeated form fields. U-REV's `due_cards(student, scope)` expects `("course", 12)`.
- **Clash:** the band's button returns 405, or a GET creates a Quiz (prefetch or a Back navigation creates duplicates). Scope objects pass type checks nowhere. Next step is SM-2 check 10.
- **Tightening:** "`NextStep.url` always points to a GET setup page or dialog (FR-10's question-count choice), never to a mutating endpoint. Quiz and Review start are POSTs. One `Scope` type (`all | course_id | topic_id`), defined in `courses`, is used by `review`, `progress` and `web`. The Quiz setup page takes `?topic=<id>` repeated."

#### A-12: `core` is outside the graph, and `core.messages` must import upward

- **Units:** U-EXAM (adds `quiz.errors.ExamClosed`) × any unit that owns `core/messages.py`.
- **Both obey:** Conventions: "Services raise typed exceptions… `core/messages.py` maps each one." U-EXAM adds an import of `quiz.errors` to `core.messages`. `quiz` imports `core.time`. `core` now depends on `quiz` and `ai`, and AD-1 gives no rule for `core` at all (G-1).
- **Tightening (AD-1):** "`core` is the bottom layer: any app may import it, and it imports no app. Errors carry a string `code`, and `core.messages` is a plain dict `code → text`."

#### A-13: Saving an Answer is "idempotent", but practice needs first-write-wins and exam needs last-write-wins

- **Units:** U-QUIZ (practice) × U-EXAM, both through `quiz.services.save_answer`.
- **U-QUIZ obeys:** AD-18 says saving is idempotent. A second POST after feedback is ignored, which is right: otherwise the Student could change their Answer after seeing the correct option.
- **U-EXAM obeys:** AD-9: "Answers are updated in place until submission." It upserts.
- **Clash:** whichever builder edits the shared service second breaks the other mode. Also unstated: the service must check that the Question is a QuizQuestion of *this* Quiz. Otherwise an owned Question from another Quiz is accepted (AD-7 passes) and counts toward the score.
- **Tightening (AD-9):** "`save_answer`: for practice and retry, insert or return the existing Answer unchanged. For exam, upsert while `effective_submitted_at` is null. The Question must be in the Quiz's QuizQuestions, or the response is 404."

#### A-14: `rate()` is idempotent without an idempotency key

- **Units:** U-REV (Review session) × U-PROG/Home (forecast, due counts).
- **The clash:** AD-18 says `rate()` is idempotent. An *Again* card legitimately comes back and is rated again in the same Review, so "(review, flashcard) once" drops real ratings. Treating every POST as new lets a double tap across a reload (`hx-sync` covers only the same form) move a card up 2 boxes.
- **Tightening (AD-11):** "Each card shown in a Review carries a `step` (the count of Ratings so far in that Review). `rate(review, flashcard, rating, step)` is a no-op when a Rating with that step exists." Also add `return_url` to `Review`, which AD-18 requires but AD-11's field list omits.

#### A-15: Who owns the upload view, and where the Detail level and the privacy notice live

- **Units:** U-UP (`ingestion`: upload limits, AD-5 step 1) × U-GEN (`studymat`: "upload dialog (D05)") × `accounts` (privacy acceptance, D04).
- **U-UP obeys:** it builds the upload POST in `ingestion`, because it owns limits and creation. It needs `ai.gateway.mode()` to decide whether to show D04, and it can't import `ai` (G-6).
- **U-GEN obeys:** it builds D05 in `studymat` per the app table. It passes the chosen Detail level in the `POST generate` body (`hx-vals`), because nothing stores it on Source.
- **Clash:** two upload views. On retry (FR-9) the Detail level is gone, because the retry button has no `hx-vals`, so a retry silently uses a default level.
- **Tightening:** "D04 and D05 views live in `studymat`, which calls `ingestion.services.ingest(…)` for step 1. `Source.detail_level` (a `courses` field) is set at upload and read by generate and retry. The acceptance write is `accounts.services.accept_privacy(student)`."

#### A-16: Grade weights live where `quiz` can't read them

- **Units:** U-RETRY / U-EXAM (result "7 of 10", score per Topic, FR-13 and FR-18) × U-PROG (AD-10 weights in `progress/rules.py`).
- **The clash:** `quiz` cannot import `progress.rules` (G-7), so it writes its own weights, perhaps counting partial as 0 or as 1 instead of 0.5. The exam's "score per Topic" and the Topic score then disagree on the same Answers.
- **Tightening:** "Grade weights live in `quiz/rules.py` (the owner of Grade). `progress` imports them, and `progress/rules.py` keeps only the window, minimum, threshold and minutes. The FR-27 row shows counts. The result and exam scores use the shared weights."

#### A-17: Grade enum values at the AI edge are not mapped

- **Units:** `ai` (U-FT's gateway half, `GradeResult` schema) × `quiz` (U-FT's storage half).
- **`ai` obeys:** AD-2 lowercases enums, and `ai` can't import `quiz`, so it writes `Literal["correct", "partially correct", "incorrect"]`, using the PRD wording.
- **`quiz` obeys:** Conventions fix `correct/partial/incorrect/not_graded`. It assigns `result.grade` straight to the field. Django doesn't validate `choices` on `save()`.
- **Clash:** `"partially correct"` is stored, `effective_grade` filters miss it, Retry rounds drop partial Questions (FR-13), and scores ignore them.
- **Tightening (AD-2):** "Response enums in `ai/schemas.py` use exactly the stored values in Conventions (`partial`, not `partially_correct`). `quiz.services` asserts the value is in `Grade.values` before saving."

#### A-18: A stale run that finishes after a retry saves Study material twice

- **Units:** U-GEN run 1 (slow, past 5 minutes) × U-GEN run 2 (a retry that claims the stale row, now legal after A-2).
- **The clash:** both runs reach "save all and set `ready`". Each obeys AD-5, but the Source gets two sets of Key concepts, Flashcards and Questions, and `removed_count` is overwritten.
- **Tightening (AD-5):** "The claim returns a token (the new `started_at`). The final transaction first runs `UPDATE … SET status = 'ready' WHERE id = … AND status = 'generating' AND started_at = token`. If no row matches, it saves nothing."

### Low

#### A-19: Theme preference has two owners

- **Units:** `accounts` (the app table: "theme preference") × the `web` shell (Conventions: "a `theme` cookie, rendered server-side").
- **The clash:** one unit stores `Student.theme`. The other reads only the cookie, so the setting doesn't follow the Student to a phone, or is ignored.
- **Tightening:** pick one store. A cookie only is simplest, and then `accounts` drops "theme preference" from the table.

#### A-20: The shape of Simpler explanation and the Mock lookup key are open

- **Units:** U-SIMP × U-MOCK × U-REV (shows a Flashcard's Simpler explanation in a Review).
- **The open shape:** the ERD shows `o|` links from both KeyConcept and Flashcard. It is unclear whether this is one model with two nullable FKs or two models. "Make a new one" might replace the row or add another, which would break the `o|`.
- **The open lookup key:** recordings are keyed by response index (`record_mock`) or by term (U-SIMP). Indices shift after the Reference check removes the wrong-page item.
- **The missing Mock case:** a Mock Simpler explanation for a Sample *Flashcard* has no recording and no error path.
- **The double request:** two concurrent requests both pay, and the second gets an IntegrityError.
- **Tightening:** one `SimplerExplanation` model with exactly one of the two FKs set, unique per item, replaced on "new". Recordings are keyed by the normalised Key-concept `term`. Mock Flashcard requests raise `NeedsKey`, which counts nothing.

#### A-21: `regenerate_summary` and Simpler explanation have no claim

- **Units:** two tabs of U-TOPIC.
- **The clash:** AD-18 lists only generate, `rate` and saving an Answer as idempotent. Two regenerations both count toward NFR-7 and race to replace the one Summary row.
- **Tightening:** a per-item in-flight marker using a conditional UPDATE, like AD-5's claim. Or accept this explicitly as a known double charge.

#### A-22: The "child's `student` equals its parent's" rule is bypassed by `bulk_create`

- **Units:** U-GEN (bulk-creates items in AD-5's one transaction) × U-PROG/`for_student` queries.
- **The clash:** AD-7 says "On save…", and a builder enforces it in `Model.save()`, which `bulk_create` skips.
- **Tightening:** the rule is enforced in services, which set `student` from the parent explicitly, plus one test per model.

#### A-23: The Reference display has no shared component

- **Units:** U-TOPIC, U-QUIZ (feedback), U-REV (back of the card), U-SIMP.
- **The clash:** each renders "side 14" plus the quote its own way, and resolves the Location kind (`page`, `paragraph` or `heading` with its label) differently.
- **Tightening:** `templates/components/reference.html` plus one `studymat` helper that resolves `(source, location_index)` to the kind and label.

#### A-24: `return_url` validation is undefined

- **Units:** U-QUIZ and U-REV (store it) × U-PROG/`web` (supply it).
- **The clash:** "validated" without a rule lets one unit accept any URL (an open redirect) while another rejects `?tab=` query strings.
- **Tightening:** `url_has_allowed_host_and_scheme`, relative paths only, with the query kept.

#### A-25: Starting a Quiz or Review is not idempotent across tabs

- **Units:** U-QUIZ × U-RETRY (the "newest Quiz" in FR-27).
- **The clash:** two tabs pressing "start Retry round" create two rounds. The newer, empty-handed one becomes "newest", and the history row loses its Retry button.
- **Tightening:** starting a Retry round reuses an unanswered Retry round of the same parent, if one exists.

---

## Part 3: Suggested AD changes (summary)

| AD | Change | Closes |
| --- | --- | --- |
| AD-1 | `core` is the bottom layer and imports no app. The graph governs model access, including reverse relations | A-3, A-12, G-1 |
| AD-2 | Gateway operations take `student` plus request DTOs. Response enums use the stored values | A-3, A-17 |
| AD-3 / AD-5 | Transaction boundaries: no gateway call inside `atomic()`, a committed claim, a conditional counter UPDATE, a separate failure write, SQLite `IMMEDIATE` | A-1 |
| AD-5 | One claimable predicate shared with `effective_status`. The claim resets `started_at` and returns a token, and the final save checks it. `Source.content_sha256`, `Source.detail_level`, `FailureReason` TextChoices | A-2, A-9, A-10, A-15, A-18 |
| AD-8 | `quiz` cleans up empty Quizzes through a receiver. `parent_quiz` uses `SET_NULL` | A-6 |
| AD-9 | `Quiz.started_at` for every kind, `Answer.answered_at`, an `effective_grade` annotation, `effective_submitted_at`, `save_answer` semantics per kind, Grade weights in `quiz/rules.py` | A-7, A-8, A-13, A-16 |
| AD-10 | Exam Answers count only once submitted. NextStep URLs point to GET pages. One `Scope` type | A-8, A-11 |
| AD-11 | ReviewState created by a `review` receiver. Writers are `introduce_today` and `rate`. Scope filters, never introduces. A `step` key on `rate`. `Review.return_url` | A-4, A-14 |
| AD-13 | One named exception for pending-Grade cells | A-8 |
| AD-18 | Composite OOB regions are emitted only by `web` views; feature POSTs answer with `HX-Location` | A-5 |
