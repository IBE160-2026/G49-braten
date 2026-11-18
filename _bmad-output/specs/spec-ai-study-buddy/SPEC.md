---
id: SPEC-ai-study-buddy
companions:
  - glossary.md
  - acceptance-criteria.md
  - user-journeys.md
  - delivery-plan.md
  - success-metrics.md
  - practice-loop.md
  - '../../planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '../../planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/SETUP-GUIDE.md'
  - '../../planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '../../planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
sources:
  - '../../planning-artifacts/prds/prd-Prosjekt A-2026-10-29/prd.md'
  - '../../planning-artifacts/prds/prd-Prosjekt A-2026-10-29/addendum.md'
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# AI Study Buddy v1

## Why

A pain and a mandate. Students, starting with the Author, process course material by re-reading and copying notes, and their ChatGPT or Claude chats vanish into a chat log instead of becoming something to practice on. AI Study Buddy turns the Student's own slides, notes and chapters into active self-testing, organized by Course and Topic. Generating study material is not new (Quizlet, StudyFetch, Quizgecko); the bet is closing the loop between testing and repetition: every Answer decides what the Student practices next (`practice-loop.md`). Trust comes from References checked in code, not from the model rating itself. It is the Author's solo course project in IBE160 at Høgskolen i Molde, due 7 December 2026, rated simple by the teacher, so quality of design, tests, process and README carries the grade. It must run on the Examiner's machine without the Author's Key.

## Capabilities

Testable consequences per capability: `acceptance-criteria.md`. Priority and build step: `delivery-plan.md`.

- **CAP-1** (Must; FR-1)
  - **intent:** A person can sign up, sign in and sign out with email and password, and sees only their own data.
  - **success:** After sign-out/sign-in or an app restart all of a Student's data is unchanged; a request for another Student's data is refused and reveals nothing.
- **CAP-2** (Must; FR-2)
  - **intent:** The Student organizes material into Courses, Topics within a Course, and Sources within a Topic, and can create, rename and delete each.
  - **success:** Deleting asks for confirmation and then removes everything beneath, including Study material and Answers; each Source has exactly one Topic and each Topic one Course.
- **CAP-3** (Must; FR-3, FR-4, FR-6)
  - **intent:** The Student adds a PDF, plain-text file or pasted text to a Topic with a Detail level, and the system keeps the text with its Location and generates in the Source's language.
  - **success:** Oversized, scanned or unsupported uploads are rejected naming the reason; the Sample document's stored text carries correct page indexes; a Norwegian Source yields Norwegian Study material.
- **CAP-4** (Must; FR-7, FR-9)
  - **intent:** For each Source the AI provider generates a Summary, Key concepts, Flashcards and Multiple-choice and Free-text Questions with Hints, while the Student sees the Source status.
  - **success:** The Sample document yields a Summary, ≥ 5 Key concepts, ≥ 10 Flashcards and ≥ 10 Questions of both kinds; any failed attempt saves nothing, never hangs as generating, and can be retried without re-upload.
- **CAP-5** (Must; FR-8)
  - **intent:** Every Generated item is shown only after the system confirms its Location exists and its quote stands there.
  - **success:** In Mock mode the one planted wrong-page item is removed and the Topic shows "1 removed"; no confidence score appears anywhere.
- **CAP-6** (Must; FR-23, FR-24)
  - **intent:** The Student reaches everything in a Topic through Summary, Quiz, Self-test and Sources areas, and can delete a single Generated item.
  - **success:** Questions appear only inside a Quiz; a deleted item vanishes from the Topic, Quizzes, Retry rounds and Due today, and its Answers stop counting.
- **CAP-7** (Must; FR-10, FR-11, FR-12)
  - **intent:** The Student takes a Practice-mode Quiz with Hints on request and gets a Grade, Explanation and Reference after each Answer.
  - **success:** Multiple-choice Answers are graded in code within 1 s; Free-text Answers are graded by the AI provider, can fail to "not graded" with retry, and can be overridden by the Student with the override marked and used.
- **CAP-8** (Must; FR-13, FR-27)
  - **intent:** After a Quiz the Student sees the result, can drill the missed Questions in Retry rounds, and sees the Topic's Quiz history.
  - **success:** A Retry round holds exactly the incorrect and partially correct Questions and can repeat until all are correct; history lists Quizzes newest first and states Retry rounds do not count.
- **CAP-9** (Must; FR-14, FR-15)
  - **intent:** The Student browses Flashcards and reviews Due today, rating each card so it returns on a schedule set by how well it was remembered.
  - **success:** Again returns the card within the Review; successive Good ratings lengthen the interval up to 180 days; at most 20 new cards a day; browsing never changes dates.
- **CAP-10** (Must; FR-16, FR-17)
  - **intent:** The Student sees how well they know each Topic and Course, and which Topics need practice.
  - **success:** Seeded Answers giving 40%, 55% and 80% list the first two as Weak topics in that order; Retry-round Answers do not move the score; a Quiz from Weak topics draws only from them.
- **CAP-11** (Must; FR-28)
  - **intent:** Home and the Course overview each show exactly one Next step, so the Student always knows what to do now.
  - **success:** With both Due cards and Weak topics the Next step is the Review; without Due cards it is the Weak-topic Quiz; then a Topic without Sources; otherwise a calm message with the next Due date.
- **CAP-12** (Must; FR-20)
  - **intent:** Without a Key the app runs in Mock mode, says so, and lets anyone try every core function on the Sample document.
  - **success:** From a fresh clone and the README, the Examiner signs up, sees the Sample document's Study material, takes a Quiz and Retry round and does a Review, with no Key and no AI-provider network calls.
- **CAP-13** (Must; FR-21, FR-22, NFR-7)
  - **intent:** With a Key the app calls the AI provider, after the Student has accepted a privacy notice, within a daily limit on Generation calls.
  - **success:** No Source text leaves before acceptance; a rejected Key gives a named message and the app keeps running; the 21st Generation call in a day is blocked with the reset time, in Mock mode too.
- **CAP-14** (Should; FR-5)
  - **intent:** The Student can upload a Word file, with References pointing to headings.
  - **success:** Every Reference from a .docx with headings names a heading in the file; one without headings uses paragraph numbers.
- **CAP-15** (Should; FR-18)
  - **intent:** The Student sits a timed Exam-mode Quiz across chosen Topics of a Course.
  - **success:** No Hints or feedback before submission; time runs out into automatic submission; the result shows score per Topic and counts toward Topic scores.
- **CAP-16** (Should; FR-19)
  - **intent:** The Student asks for a Simpler explanation of a Key concept or Flashcard.
  - **success:** At most three sentences in the Source's language, based on the item's Reference, saved and reshown with an option to make a new one.
- **CAP-17** (Should; FR-25)
  - **intent:** The Author runs one Hosted instance reachable from a phone.
  - **success:** Sign-up is closed to all but the Author by configuration, and data survives restarts and deploys. If no zero-cost host meets the architecture's host requirements, CAP-17 is dropped from v1.
- **CAP-18** (Should; FR-26)
  - **intent:** Generation continues when the Student leaves the page.
  - **success:** After closing the browser mid-generation and returning, the Source shows its real status and any finished Study material.

## Constraints

- Delivery 7 December 2026. Step 1 (core loop) done and tested by 20 November, step 2 by 30 November, with fixed cut lines (`delivery-plan.md`). Should work starts only after every Must is done and tested.
- Solo Author; one role (Student). No teacher, sharing or admin roles.
- Runs from a fresh clone in Mock mode within 15 minutes using only the README and free tools; no paid account, Key or Hosted instance needed.
- No Key means Mock mode, always. Mock mode runs the real pipeline, including the Reference check, on recorded responses for a copyright-free Sample document in the repository.
- Default AI provider is Claude Haiku 5.5 (Anthropic; Author's choice 2026-11-13). No free tier: the Author pays, the Examiner uses Mock mode.
- The Key lives only in git-ignored environment configuration; never in the repository, logs or browser. Passwords are stored as slow, salted hashes. Every request checks that the data belongs to the signed-in Student.
- At most 20 Generation calls per Student per day; grading never counts, so a Quiz never stops partway.
- Upload limits: 50 PDF pages, 10 MB, 150,000 characters. Text only: no OCR, figures skipped, tables as plain text. Location is the PDF viewer page index, the paragraph number for plain text, the nearest heading for Word.
- Multiple-choice grading is deterministic code with no AI call at answer time. No AI confidence score is ever shown.
- Retry-round Answers, ungraded Answers and Flashcard ratings never count toward Topic scores.
- Interface text in Norwegian bokmål, addressing the Student as «du», calm and plain, no exclamation marks or emojis; Study material follows the Source's language.
- Responsive web from 360 px in the latest Chrome, Safari and Firefox, without horizontal scrolling; light and dark themes; WCAG 2.2 AA (EXPERIENCE.md, DESIGN.md).
- Response times: Study material for a 20-page PDF within 2 minutes and Free-text grading within 15 s in Real mode; every response within 5 s in Mock mode.
- Every Key-free testable consequence has an automated test that runs without a Key or network (NFR-5).
- Technology, module boundaries and data rules are fixed by the adopted architecture spine (Django modular monolith, SQLite, HTMX, Leitner scheduling).

## Non-goals

- Competing with Quizlet, StudyFetch or Quizgecko; payment, subscription or advertising.
- Native apps and offline use.
- Sharing, collaboration, teacher tools or any role other than Student.
- Free-form chat with the AI provider; the Simpler explanation is the only open request.
- Password reset by email; export (for example Flashcards to Anki).
- AI-made answers to practice exercises checked against the web.
- Images and handwriting (OCR), and breaking large exam tasks into sub-tasks, in v1 (`delivery-plan.md`).
- Optimizing the number of Generated items or Topic scores for their own sake (`success-metrics.md`, SM-C1, SM-C2).

## Success signal

- Every check in the SM-2 acceptance checklist (`success-metrics.md`) passes by following the README in Mock mode or by an automated test, and the Examiner completes UJ-5 from a fresh clone without a Key.
- The Author actually uses the app through the semester: at least three Quizzes or Reviews a week in at least two Courses until delivery (SM-1), with ≥ 60% of missed Questions answered correctly the next time (SM-4).

## Assumptions

- Numeric values marked † in `acceptance-criteria.md` are starting values, tuned by the tests named there; they are not open decisions.
- The adopted architecture spine supersedes the PRD addendum's implementation notes where they overlap (spaced repetition: Leitner, AD-11).

## Open Questions

- If images come into scope after v1, are they handwritten notes, or photos and screenshots of printed text and slides? (Author; not blocking v1.)
- Architecture OQ-1 to OQ-3 remain open: PDF extraction test on three slide decks (before 20 November), Real-mode generation time and rate tier (before 20 November), and host checks for the Hosted instance (when CAP-17 starts).
