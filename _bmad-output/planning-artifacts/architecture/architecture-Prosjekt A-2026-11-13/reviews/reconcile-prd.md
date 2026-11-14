---
title: 'Reconcile: ARCHITECTURE-SPINE.md against PRD + addendum'
spine: '../ARCHITECTURE-SPINE.md (draft, 2026-11-13)'
inputs:
  - '../../../prds/prd-Prosjekt A-2026-10-29/prd.md (final, updated 2026-11-13)'
  - '../../../prds/prd-Prosjekt A-2026-10-29/addendum.md'
date: '2026-11-13'
scope: 'Only gaps that matter architecturally: contradictions, shared shapes/state/ownership left undecided where two builders could diverge, and dropped quiet requirements. FR behaviour that the PRD already pins down and that one module owns alone is not reported.'
---

# Reconcile: spine vs PRD

**Totals:** 5 high, 9 medium, 7 low (21 findings).

**No numeric contradictions found.** Every number the spine repeats matches the PRD: Leitner intervals start 1, 3, 7 and are capped at 180; 20 new cards a day; quotes of 5 words; 20-Answer window with weights 1 / 0.5 / 0; Mock mode has exactly one removed item. The contradictions below are about state and structure, not numbers.

## High

### R-01 — Regenerating a Summary goes through the all-or-nothing Source lifecycle (contradiction)
- **Problem:** AD-5's state diagram has `ready --> generating: regenerate Summary only (keeps items)`. AD-5 also says that on any error the orchestrator "saves nothing, sets `failed`", and that a retry from `failed` regenerates and saves **all** Study material. So if a Summary regeneration fails, a Source that already has Key concepts, Flashcards, Questions, Answers and review dates becomes `failed`. While it is `generating` or `failed` it drops out of the FR-23 Summary area ("one Summary per **ready** Source"), and a retry from there would regenerate every item, either duplicating items or replacing them, which would cascade-delete Answers and ReviewState under AD-8. The spine also leaves open whether Questions and Flashcards of a Source in `generating` or `failed` still appear in Quizzes, Due today and browsing.
- **PRD:** FR-7 ("regenerate the Summary at another Detail level without regenerating the rest"), FR-23, FR-9, NFR-7.
- **Suggested spine fix:** Make Summary regeneration a separate operation that never touches `Source.status`: success adds or replaces only the Summary, failure keeps the old Summary and shows an error. A full-generation retry is allowed only when the Source has no Study material.

### R-02 — The ERD gives a Quiz exactly one Topic, but the PRD needs Quizzes that span Topics
- **Problem:** The ERD has `TOPIC ||--o{ QUIZ`, and AD-8 cascades Quizzes from their Topic. But a Weak-topics Quiz draws from "one or more Weak topics" (FR-17, and it is step 2 of the Next step on Home and the Course overview, FR-28), and an Exam-mode Quiz draws from "one or more Topics in a Course" (FR-18). Three things are left undecided. First, whether a Quiz links to a Course plus a set of Topics, or to a single Topic. Second, which Topic's Quiz history (FR-27) lists a Quiz that spans Topics. Third, what deleting one of its Topics does to it. AD-10 also does not say that an Answer's Topic comes from `Question → Source → Topic` rather than from `Quiz.topic`. Builders of the Quiz, scoring and history features could each pick a different answer.
- **PRD:** FR-17, FR-18, FR-27, FR-28 step 2, FR-16, Glossary "Question ... belongs to the Topic of its Source".
- **Suggested spine fix:** Give `Quiz` a `course` FK plus a `topics` M2M (or derive its Topics from its Questions). Topic membership for scoring and history always comes from `Question.source.topic`. A Quiz appears in the history of every Topic it touches.

### R-03 — The set of Questions in a Quiz is never stored
- **Problem:** The spine stores only `Quiz` and `Answer`. A Quiz also has to know which Questions it holds and in what order before they are answered. The runner needs this to show "3 of 10" and to survive a reload (AD-13). An abandoned Quiz needs it (FR-10). Exam mode needs it to treat unanswered Questions at the timeout and to compute the score per Topic (FR-18). FR-24 removes a Question from an in-progress Quiz when the Student deletes it from the feedback. A Retry round needs it to know "the Questions" of the previous Quiz. Builders could choose between a stored ordered list (a `QuizQuestion` table or JSON), drawing a fresh Question on each step, or using Answers alone. The spine also does not say whether `(quiz, question)` is unique on Answer, which matters because "try again" in FR-12 regrades the same Answer.
- **PRD:** FR-10, FR-13, FR-18, FR-24, FR-27.
- **Suggested spine fix:** Add `QuizQuestion(quiz, question, position)`, created when the Quiz starts and removed by cascade when its Question is deleted. Make `Answer` unique on `(quiz, question)`. Count the score's total from QuizQuestion, not from Answers.

### R-04 — The spine does not say where privacy acceptance is enforced
- **Problem:** AD-7 lists "the privacy acceptance" as a Student-owned row, and `accounts` owns it. Nothing says which code checks it. The PRD rule is "No Source text is sent to an AI provider before the Student has accepted". If only the upload view checks it, Source text can still be sent without acceptance in three ways. A Source uploaded in Mock mode, where no notice is shown, can be retried after a Key is added. Free-text grading sends Source text at the Reference (FR-12). A Simpler explanation sends the item's Source text (FR-19). The spine also does not say whether the notice appears in Mock mode, where UJ-1 shows it and FR-22 says "In Real mode".
- **PRD:** FR-22, UJ-1, FR-12, FR-19.
- **Suggested spine fix:** Make `ai.gateway` refuse, with a typed error such as `PrivacyNotAccepted`, any Real-mode call that carries Source text for a Student who has not accepted. The upload view shows the notice as well, but the gateway is the guard.

### R-05 — The intake of new Flashcards into Due today is unspecified
- **Problem:** AD-11 says new Flashcards enter "in the order they were generated, at most 20 per day". It does not define four things. (a) How a new card is represented: does a `ReviewState` exist with `due_date = null`, and is its intake date stored? (b) Whether the cap is per Student across all Courses (Due today spans all Courses, UJ-2) or per Course or Topic. (c) How the cap interacts with the three Review scopes: all Courses (Home), one Course (the Next step on the Course overview, FR-28) and one Topic (FR-15, FR-23). (d) How the "next Due card" date in FR-15 and FR-28 step 4 handles cards still waiting for intake. The `review` service, the Due-today count on Home and the Next step in `progress` must all count Due cards the same way, so this needs one shared definition.
- **PRD:** FR-15, FR-23, FR-28 steps 1 and 4, Glossary "Due card" and "Due today", SM-2 check 7.
- **Suggested spine fix:** Make `review.services.due_cards(student, scope)` the only definition of Due, used by both `review` and `progress`. New cards have `due_date = null` and get an `introduced_on` date when a day's intake picks them. The cap of 20 is per Student per Oslo day across all Courses, filled in global generation order, and scoped Reviews only filter that set.

## Medium

### R-06 — Summary per Detail level: the spine does not say which Summary is current
- **Problem:** The ERD shows `SOURCE ||--o{ SUMMARY : "per Detail level"`, but FR-23 shows one Summary per Source. The spine does not decide whether regenerating replaces the Summary or adds another one next to it. If several are kept, nothing marks which one is shown, for example `Source.detail_level` or `Summary.is_current`. It also does not decide whether going back to a level used before reuses the stored Summary or makes a new Generation call. Mock mode needs recorded Summaries at all three levels for a Key-free FR-7 test.
- **PRD:** FR-3, FR-7, FR-23, NFR-5, NFR-7.
- **Suggested spine fix:** Keep one Summary row per Source, with `detail_level` on it, and replace it on regeneration. `ai/mock/` holds the Sample document's Summary at short, medium and detailed.

### R-07 — How Retry-round membership works with `not_graded` Answers
- **Problem:** FR-13 says a Question whose Answer is not graded "is left out until that Answer is graded". AD-9 only adds `parent_quiz`. The spine does not say three things. Is membership fixed when the Retry round starts? If a `not_graded` Answer in the parent is graded later and comes out incorrect, can another Retry round start from the same parent, even though FR-27 only offers a Retry round on the **newest** Quiz? Can one parent have more than one Retry round? Without rules, such Questions can be lost, and different builders would answer these questions differently.
- **PRD:** FR-13, FR-27, FR-12.
- **Suggested spine fix:** Fix a Retry round's members when it starts: the parent's Questions whose `effective_grade` is in {incorrect, partial}. One parent may have several Retry rounds. Any Quiz with eligible Questions can start one from its result page; the history row only shortcuts this for the newest Quiz.

### R-08 — No Grade state for an Answer that is saved but not yet graded (Exam mode, abandoned Quizzes)
- **Problem:** AD-9 saves an Answer as soon as it is given, and its Grade values are `correct/partial/incorrect/not_graded`, where `not_graded` means grading failed (FR-12). In Exam mode, a Free-text Answer is graded only at submission (FR-18). So between saving and submission, or for good if the Exam-mode Quiz is abandoned, the Answer has no valid value. Using `not_graded` would show "grading failed, try again" for an Answer that was never sent for grading. The spine also does not say where Exam mode's deadline is stored. FR-18 needs automatic submission that survives a reload, and the spine leaves the timer to a JavaScript file only.
- **PRD:** FR-18, FR-12, FR-10, FR-16.
- **Suggested spine fix:** Make `grade` nullable (null means pending) or add a `pending` value, and leave pending Answers out of scores. Store `Quiz.time_limit` and `Quiz.started_at`; the server rejects Answers after the deadline and submits the Quiz automatically when it next sees it.

### R-09 — No stored shape for Question and Answer, which `studymat`, `quiz` and `ai` all share
- **Problem:** `studymat` writes Questions, `quiz` reads them for grading and display, and `ai/schemas.py` defines the response. The stored shape is not fixed. A Question needs a kind (`multiple_choice` or `free_text`, missing from the Enums row), 4 options with exactly one correct, one Explanation **per option** (FR-7, FR-11), a Hint, a model answer for Free-text, and a Reference. Options could be stored as JSON or as an Option table. An Answer needs the chosen option or the free text, and the grading Explanation for Free-text, which is not on AD-9's Answer.
- **PRD:** FR-7, FR-11, FR-12, addendum "Grading Answers to Multiple-choice questions".
- **Suggested spine fix:** Add one line to AD-9 or AD-6 that fixes the fields: `Question(kind, prompt, hint, options JSON[4]{text, explanation}, correct_index, model_answer, location_index, quote)` and `Answer(chosen_index | text, grade, override_grade, explanation, is_mock)`.

### R-10 — No rule for what happens when a length check or structural check fails
- **Problem:** The Conventions row says code checks lengths after schema validation, and AD-4 runs the "length checks" on Mock recordings too. Several FR-7 rules are such checks: a Key concept definition is at most 2 sentences; a Hint is 1 sentence and never contains the correct option; a Multiple-choice question has 4 options with exactly 1 correct. FR-19 limits a Simpler explanation to 3 sentences. Nothing says whether a failing item is dropped or whether the whole attempt fails (the AD-5 `failed` path). Nor does it say whether dropped items are added to `removed_count`. If they were, the FR-8 invariant that the Mock Topic shows exactly one removed item could break.
- **PRD:** FR-7, FR-8, FR-19, AD-4.
- **Suggested spine fix:** An item that fails a length or structure check is dropped and counted separately from Reference-check removals; `removed_count` counts only the FR-8 Reference check. For a Simpler explanation, failing the check fails that call.

### R-11 — The order of the gateway's checks is undecided (NeedsKey, privacy, the daily limit)
- **Problem:** AD-3 increments the counter before anything is sent, and AD-4 raises `NeedsKey` for a non-Sample Source in Mock mode. The spine does not say which runs first. If the increment runs first, an Examiner who uploads a few other PDFs (UJ-5 edge case) uses up the daily limit with no AI call made. The spine also does not say which Source status and reason a NeedsKey Source gets (`failed` with reason `needs_key`?), or whether it can be retried once a Key is set.
- **PRD:** NFR-7, FR-20, FR-9, UJ-5.
- **Suggested spine fix:** Fix the order in `ai.gateway`: mode/NeedsKey, then privacy (R-04), then limit check and increment, then send. A NeedsKey Source is `failed` with reason `needs_key`, can be retried, and uses up no Generation call.

### R-12 — Reviews and ratings are not stored, so a Review cannot survive a reload and SM-1 cannot be measured
- **Problem:** The spine stores only `ReviewState(box, due_date)`. A Review has state of its own: cards rated Again must come back before it ends, and at the end it shows "the number of cards reviewed and the date of the next Due card" (FR-15). That state must survive a full-page reload (AD-13). SM-1 is "measured from stored Answers and **Reviews**", per Course. Builders could keep a Review in the Django session, in a model or in the browser.
- **PRD:** FR-15, SM-1, AD-13.
- **Suggested spine fix:** Add `Review(student, scope, started_at, ended_at)` and `Rating(review, flashcard, rating, rated_at)`, both owned by `review`. Again-cards come back from the Ratings of the open Review.

### R-13 — The user model and email login are not decided
- **Problem:** FR-1 requires sign-in with email and password, and FR-25 / AD-14 match `SIGNUP_ALLOWED_EMAILS` against an email. "Student (Django user)" leaves open the default `User`, which has a username, versus a custom user with `USERNAME_FIELD = "email"`. In Django this has to be decided before the first migration, and every FK to the Student depends on it.
- **PRD:** FR-1, FR-25, NFR-4.
- **Suggested spine fix:** `accounts.Student` is a custom `AUTH_USER_MODEL`, created in the first migration, with a unique case-insensitive email as `USERNAME_FIELD`. Every FK uses `settings.AUTH_USER_MODEL`.

### R-14 — "Make a new Simpler explanation" may not count the first one as a Generation call
- **Problem:** AD-3 counts "make a new Simpler explanation", copying the wording of NFR-7. The Glossary defines a Generation call as one that "makes **or** remakes Study material **or a Simpler explanation**", so the first request also counts. Only showing the saved one again (FR-19) is free. A builder reading AD-3 alone could let the first Simpler explanation skip the counter.
- **PRD:** Glossary "Generation call", NFR-7, FR-19.
- **Suggested spine fix:** Reword AD-3 to "...or make any Simpler explanation (the first one or a new one); showing a saved one makes no call."

## Low

### R-15 — A `heading` Location has no field for the heading text
- **Problem:** FR-5 requires that "every Reference names a heading that exists in the file", but AD-6's `SourceText(kind, index, text)` has nowhere to store the heading's text for display. A .docx with no headings falls back to `paragraph`, so the kind can differ between Sources of the same file type.
- **PRD:** FR-5.
- **Suggested spine fix:** Add `label` to `SourceText` (the heading text, or null) and display the Location as `label` or as "page/paragraph N".

### R-16 — Pages with only a figure, and the count behind the header/footer rule
- **Problem:** FR-4 says a page with only a figure "gives no text". The spine does not say whether that page gets a `SourceText` row with empty text or no row. This changes "Location must exist" and the count of Locations that "most Locations" (the header/footer rule) is measured against.
- **PRD:** FR-4, FR-8.
- **Suggested spine fix:** Store one row per page, with empty text for pages without text. "Most Locations" counts only rows that have text.

### R-17 — The language of a Source is not stored
- **Problem:** FR-6 says Study material follows the Source's language. FR-19 also requires Simpler explanations in that language, and Free-text grading Explanations should probably follow it too. These calls are made later from other modules (`quiz`, `studymat`), and each prompt may detect the language again on its own.
- **PRD:** FR-6, FR-19, FR-12.
- **Suggested spine fix:** Store `Source.language`, returned by the generation schema, and pass it to every later prompt about that Source.

### R-18 — The Simpler explanation model is missing from AD-7, the ERD and the AD-8 cascade
- **Problem:** FR-19 saves Simpler explanations, which must belong to a Student and be deleted along with their Key concept or Flashcard. The spine does not say whether "make a new one" replaces the saved one or keeps a history. (AD-7's list is illustrative, but this Student-owned model is the one it leaves out.)
- **PRD:** FR-19, FR-24, NFR-4.
- **Suggested spine fix:** Add `SimplerExplanation` (in `studymat`, one per item, replaced when a new one is made) to AD-7's list and the ERD, and cascade it from its item.

### R-19 — Quiet constraints on the AI interface were dropped
- **Problem:** Two constraints are missing. FR-8: "The app shows no confidence score from the AI provider", so schemas should not ask for one. §6 Non-goals: the Simpler explanation is "the only open request" (no free chat). AD-2 does not limit the gateway to a closed set of operations.
- **PRD:** FR-8, §6.
- **Suggested spine fix:** AD-2: the gateway exposes only `generate_study_material`, `regenerate_summary`, `grade_free_text` and `simpler_explanation`; no schema has a confidence field.

### R-20 — The time budgets in NFR-3 are not linked to any setting
- **Problem:** AD-16 fixes a host timeout of at least 150 s for generation. Nothing links Free-text grading to its 15-second budget, or Mock mode to its 5-second budget. A grading call with the SDK's default timeout and retries can block a Quiz step far longer than 15 s.
- **PRD:** NFR-3, FR-12.
- **Suggested spine fix:** Set a timeout and retry count per gateway operation in `ai` settings: grading at about 15 s total, then `not_graded`; generation below the 150 s host timeout.

### R-21 — Signing in by default and starting a Weak-topics Quiz across modules
- **Problem:** NFR-4 says "every request checks that the data belongs to the signed-in Student". AD-7 covers objects but not whether every view requires sign-in; Django 5.1 and later offers `LoginRequiredMiddleware` for this. Separately, `quiz` may not import `progress`, so the Weak-topics Quiz that the Next step starts has to get Topic ids from outside.
- **PRD:** NFR-4, FR-17, FR-28.
- **Suggested spine fix:** Turn on `LoginRequiredMiddleware`, with sign-in, sign-up and static files exempt. `quiz.services.start(topics=[...])` receives Topic ids explicitly and checks that they are owned and in one Course.
