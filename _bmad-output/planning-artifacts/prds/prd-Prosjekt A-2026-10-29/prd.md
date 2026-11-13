---
title: "PRD: AI Study Buddy"
status: final
created: 2026-10-29
updated: 2026-11-13
---

# PRD: AI Study Buddy

## 0. Document purpose

This PRD defines what version 1 of AI Study Buddy must do, for the Author who builds it, the Examiner who assesses it, and the BMad workflows that follow (UX, architecture, epics and stories); the written report for the course is outside it. It builds on the product brief and its addendum (`_bmad-output/planning-artifacts/briefs/brief-Prosjekt A-2026-09-15/`), the technical research (`_bmad-output/planning-artifacts/research/technical-llm-choice-and-pdf-extraction-for-ai-stu-2026-10-28/research.md`) and the teacher's feedback on the brief (`tilbakemelding-product-brief.md`) and on this PRD (`tilbakemelding-prd.md` in this folder, handled on 2026-11-13), all in Norwegian. Terms in §3 are used exactly as defined; each FR is **Must** (required on 7 December 2026) or **Should** (built only after every Must FR is done and tested); everything without a tag is decided, while starting values that will be tuned are tagged `[ASSUMPTION]` with the test that tunes them and listed in §10; technology choices are left to architecture, with notes in `addendum.md`, which also lists the changes from the product brief.

## 1. Vision

AI Study Buddy is a responsive web app that turns a student's own course material into active self-testing. The Student uploads lecture slides, notes or textbook chapters into a Course and Topic, and gets a Summary, Key concepts, Flashcards and a Quiz of Multiple-choice and Free-text questions. Every Key concept, Flashcard and Question points back to the Location it came from.

Generating study material is not new; Quizlet, StudyFetch and Quizgecko already do it. This product bets on closing the loop between testing and repetition: every Answer decides what the Student practices next. Questions answered incorrectly or partially correctly return in a Retry round, Flashcards come back on a schedule set by how well they were remembered, and Topic scores show which Topics need work before the exam. Instead of passive re-reading, or chat conversations with ChatGPT or Claude that vanish into a chat log, the Student gets material to practice on all semester.

The Author builds the app alone as the course project in IBE160, due 7 December 2026, and will use it in the Author's own courses. It must also run on the Examiner's machine without the Author's Key.

## 2. Target user

The primary Student is the Author, who today re-reads notes and asks ChatGPT when something is unclear, with no system for repetition or self-testing. The app is meant for students in any subject, and nothing in it is tailored to one field. In the journeys below, Ida stands in for the Author and Jonas is the Examiner.

### 2.1 Key user journeys

- **UJ-1. Ida turns Monday's lecture into a quiz the same evening.** (Must) Signed in on a laptop, Ida opens the Course "Databases" and creates the Topic "Normalization". The first time, Ida reads and accepts the privacy notice, then uploads the 32-page lecture slides as a PDF with Detail level medium. After a progress indicator, the Topic shows the Summary, Key concepts and Flashcards. Ida starts a Practice-mode Quiz of 10 Questions, opens the Hint on one, and gets every Answer graded right away. An incorrect Answer to a Multiple-choice question shows the correct option, why the chosen option is wrong, and "page 14" with the quoted sentence. The result shows 7 of 10, and Ida takes the Retry round with the three missed Questions straight away. **Edge case:** a 70-page compendium is rejected at upload with a message stating the 50-page limit, so Ida uploads one chapter at a time.
- **UJ-2. Ida clears Due today on the bus.** (Must; using the phone away from home needs the Hosted instance in FR-25, which is Should) On the phone, Ida opens Due today: 14 Due cards from two Courses. Ida flips each card and rates it Again, Hard, Good or Easy; cards rated Again come back before the Review ends. The Review ends with the number of cards reviewed and when the next cards are due.
- **UJ-3. Two weeks before the exam, Ida drills Weak topics and sits a mock exam.** (Must; Exam mode is Should) The Course overview shows two Weak topics: "Normalization" at 45% and "Transactions" at 55%. Ida starts a Practice-mode Quiz from both, then an Exam-mode Quiz: 20 Questions from the whole Course, 30 minutes, no Hints and no feedback along the way. After submission, the result shows the score per Topic, and the Topic scores update.
- **UJ-4. Ida gets a Simpler explanation of a Key concept that does not click.** (Should) In the Topic, the Key concept "third normal form" makes no sense to Ida. Ida asks for a Simpler explanation and gets a short, plain version in the language of the slides, with the page it is based on.
- **UJ-5. Jonas runs the app from the README without a Key.** (Must) Jonas clones the repository, copies `.env.example` to `.env` without adding a Key, and starts the app as the README describes. The app shows that it runs in Mock mode. Jonas creates an account and uploads the Sample document; the Topic shows its Study material and one Generated item removed by the Reference check. Jonas takes a Quiz and a Retry round and does a Review. **Edge case:** when Jonas uploads another PDF, the app stores it and says that generating Study material for it needs a Key.

## 3. Glossary

- **Student** — a signed-in user of the app; the only role.
- **Author** — the student who builds the app; also its primary Student.
- **Examiner** — the person who assesses the course project by running the app locally from the README.
- **Course** — a subject the Student studies, with a name and an optional course code. Has many Topics.
- **Topic** — a chapter or theme within one Course. Has many Sources.
- **Home** — the first screen after signing in: all of the Student's Courses with their Course scores, Due today and the Next step.
- **Course overview** — the screen that lists a Course's Topics with their Topic scores and Weak topics, with the Course score and the Next step.
- **Course score** — how well the Student knows a Course: the mean of the Topic scores of its Topics that have one (FR-16).
- **Next step** — the one recommended action on Home and the Course overview (FR-28).
- **Source** — one uploaded file or pasted text in one Topic.
- **Source status** — where generation for a Source stands: generating, ready or failed (FR-9).
- **Location** — where in a Source a piece of text sits: a page for PDF, a heading for Word, a paragraph for plain text.
- **Reference** — a Location plus a verbatim quote from the Source.
- **Generated item** — a Key concept, Flashcard or Question. Each has a Reference.
- **Sample document** — a copyright-free PDF of about 20 pages in the repository, with recorded responses for Mock mode.
- **Study material** — everything generated from one Source: its Summary and its Generated items.
- **Summary** — a generated summary of one Source at a chosen Detail level. Has no Reference in v1.
- **Detail level** — how detailed a Summary is.
- **Key concept** — a term from the Source with a definition.
- **Simpler explanation** — a plainer explanation of a Key concept or Flashcard, made on request (Should).
- **Flashcard** — a card with a front (a question or term), a back (the answer) and a next review date.
- **Review** — a session in which the Student rates Due cards, which sets their next review dates.
- **Due card** — a Flashcard whose next review date is today or earlier.
- **Due today** — the list of Due cards from all of the Student's Courses.
- **Question** — a quiz item generated from a Source, with a Hint: either a Multiple-choice question or a Free-text question. Belongs to the Topic of its Source.
- **Multiple-choice question** — a Question answered by picking one of several options.
- **Free-text question** — a Question answered in the Student's own words, with a model answer.
- **Hint** — a nudge toward the answer, generated with its Question.
- **Quiz** — one run of Questions answered by the Student, in Practice mode or Exam mode.
- **Practice mode** — the Quiz mode with Hints and feedback after each Answer.
- **Exam mode** — the Quiz mode that imitates an exam (Should).
- **Answer** — the Student's response to one Question in a Quiz.
- **Grade** — the result of grading an Answer: correct, partially correct (Free-text questions only), incorrect, or not graded (grading failed). The Student can override the Grade of an Answer to a Free-text question (FR-12).
- **Explanation** — why an Answer is correct or incorrect.
- **Retry round** — a Quiz with the Questions graded incorrect or partially correct in the previous Quiz.
- **Topic score** — how well the Student knows a Topic, computed from recent Answers.
- **Weak topic** — a Topic whose Topic score is below a threshold.
- **AI provider** — the language model service that generates Study material, grades Answers to Free-text questions and writes Simpler explanations.
- **Generation call** — a call to the AI provider that makes or remakes Study material or a Simpler explanation; counted against the daily limit in NFR-7. Grading is not a Generation call.
- **Key** — the secret credential for an AI provider, kept in the environment configuration.
- **Mock mode** — the mode used when no Key is set: recorded responses for the Sample document replace the AI provider.
- **Real mode** — the mode used when a Key is set: the AI provider is called.
- **Hosted instance** — the Author's own copy of the app on a server, reachable from a phone (Should).

## 4. Features

### 4.1 Account and organization (Must)

#### FR-1: Sign-up and sign-in

A person can create an account, sign in and sign out. Realizes UJ-1, UJ-5.

**Consequences (testable):**
- After signing out and back in, or after the app is restarted, the Student's Courses, Topics, Sources, Study material, Answers and review dates are unchanged.
- A request for another Student's Source or Study material is refused, and nothing about it is shown.
- Sign-in uses email and password; there is no third-party login in v1.

#### FR-2: Courses, Topics and Sources

The Student can create, rename and delete Courses, Topics within a Course, and Sources within a Topic. Realizes UJ-1.

**Consequences (testable):**
- Every Source belongs to exactly one Topic, and every Topic to exactly one Course.
- Deleting a Course, Topic or Source asks for confirmation, then removes everything under it, including Study material and Answers.
- The Course overview lists the Course's Topics with each Topic score (FR-16).

### 4.2 Upload and text extraction (Must; FR-5 is Should)

#### FR-3: Upload a Source

The Student can upload a PDF or a plain-text file, or paste text, into a Topic, and choose a Detail level for the Summary: short, medium or detailed. Realizes UJ-1.

**Consequences (testable):**
- A PDF over 50 pages, a file over 10 MB, or plain or pasted text over 150,000 characters is rejected before processing, with a message that states the limit. `[ASSUMPTION: the limits; tuned by the extraction test in NFR-5 and the AI provider's token limits.]`
- A PDF with no extractable text, such as a scanned document, is rejected with a message that scanned documents are not supported in v1.
- Any other file type is rejected with a message that lists the supported types.
- One upload holds one file; several files go into a Topic as separate Sources.

#### FR-4: Keep the Location of extracted text

The system stores the extracted text of each Source with its Location. Realizes UJ-1.

**Consequences (testable):**
- For PDF, the Location is the page index as a PDF viewer shows it, starting at 1, not the printed page number. For the Sample document, the stored text of each page carries the right page index.
- For plain and pasted text, the Location is the paragraph number.
- Text from two pages is never stored under one Location.
- Only the text of a PDF is read. Images and figures are skipped, so a page with nothing but a figure gives no text; tables are stored as plain text. This is the v1 answer to the handling of tables and figures, a decision point named by the assignment.

#### FR-5 (Should): Word files

The Student can upload a Word file (.docx) as a Source. Its Location is the nearest heading above the text, because Word files have no fixed page numbers.

**Consequences (testable):**
- For a .docx with headings, every Reference names a heading that exists in the file.
- A .docx without headings uses paragraph numbers as Locations.

#### FR-6: Source language

Study material is generated in the language of its Source. Realizes UJ-4.

**Consequences (testable):**
- A Norwegian Source gives Norwegian Study material; an English Source gives English Study material.
- For a Source in more than one language, the main language is used, and the Student cannot override it in v1.

### 4.3 Study material (Must; FR-26 is Should)

#### FR-7: Generate Study material

For each Source, the AI provider generates a Summary at the chosen Detail level, Key concepts, Flashcards, and Questions of both kinds, each Question with a Hint. Realizes UJ-1.

**Consequences (testable):**
- After the check in FR-8, the Sample document gives a Summary, at least 5 Key concepts, at least 10 Flashcards and at least 10 Questions, with both Multiple-choice questions and Free-text questions among them. The minimum of 10 Flashcards comes from the brief.
- Every Multiple-choice question has four options, exactly one of them correct, and an Explanation for each option.
- A Key concept's definition is at most two sentences. A Hint is one sentence and never contains the correct option.
- The Student can regenerate the Summary at another Detail level without regenerating the rest of the Study material.
- `[ASSUMPTION: the minimums of 5 Key concepts and 10 Questions; tuned by the content check in NFR-5.]`

#### FR-8: Check References

Before a Generated item is shown, the system checks its Reference: the Location must exist in the Source, and the quote must appear at that Location. The app shows no confidence score from the AI provider; trust in a Generated item comes from its checked Reference. Realizes UJ-1, UJ-5.

**Consequences (testable):**
- A Generated item that fails the check is removed, not shown with a warning, and the Topic shows the number removed.
- The quote is at least 5 words long and is not text that repeats on most pages, such as a header or footer. `[ASSUMPTION: 5 words; tuned by SM-3.]`
- The check compares text after normalizing whitespace, line breaks and hyphenation. It does not judge whether the content is correct.
- Explanations and Simpler explanations reuse the Reference of their Question, Key concept or Flashcard, and add no new ones.
- In Mock mode, the recorded responses for the Sample document contain exactly one Generated item with a wrong page index, so the Topic shows one removed item.

#### FR-9: Progress and failed generation

The Student sees the Source status of each Source: generating, ready or failed. In v1, generation runs while the Student waits, with a progress indicator; generation that continues after the Student leaves is FR-26 (Should). Realizes UJ-1.

**Consequences (testable):**
- If generation is interrupted, for example because the Student closes the page, the Source shows as failed on return, never as generating forever.
- If the AI provider returns an error, a refusal, a cut-off response or a response in the wrong format, no Study material from that attempt is saved or shown, and a message says what failed and offers to try again.
- If the AI provider answers with a rate limit, a message asks the Student to wait and try again later, and the Source gets the status failed with no partial Study material.
- The Student can retry generation for the Source without uploading it again.

#### FR-26 (Should): Background generation

Generation continues if the Student leaves the page or closes the browser.

**Consequences (testable):**
- After the Student closes the browser during generation and comes back, the Source shows as generating, ready or failed, and Study material that finished in the meantime is shown.

#### FR-23: View Study material

The Student can open a Topic and reach everything in it from four areas: Summary, Quiz, Self-test and Sources. Opening a Topic shows the Summary area first. Realizes UJ-1, UJ-4.

**Consequences (testable):**
- **Summary area:** one Summary per ready Source, newest first, each followed by its Key concepts with their Location. There is no combined Summary for the whole Topic.
- **Quiz area:** the Student can start a Practice-mode Quiz (FR-10) and see the Quiz history (FR-27).
- **Self-test area:** the Student can browse the Topic's Flashcards (FR-14), start a Review of the Topic's Due cards (FR-15) and set up an Exam-mode Quiz (FR-18, Should).
- **Sources area:** the Student can add a Source and sees each Source with its Source status (FR-9).
- Questions appear only in a Quiz, so the Topic does not give the answers away.

#### FR-24: Delete a Generated item

The Student can delete a single Key concept or Flashcard from the Topic, or a Question from the feedback or result of a Quiz.

**Consequences (testable):**
- A deleted Generated item no longer appears in the Topic, in Quizzes, in Retry rounds or in Due today.
- Answers to a deleted Question no longer count toward the Topic score.

### 4.4 Quiz and grading (Must)

#### FR-10: Practice-mode Quiz

The Student can start a Practice-mode Quiz from a Topic and choose the number of Questions, up to the number of Questions in the Topic. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- Questions are drawn from the Topic's Study material in random order.
- The Hint of a Question is shown only when the Student asks for it.
- The Grade, Explanation and Reference appear right after each Answer.
- Answers are saved as they are given, so the Answers in an abandoned Quiz still count toward the Topic score.
- `[ASSUMPTION: 10 Questions by default; tuned by the Author's own use (SM-1).]`

#### FR-11: Grade Answers to Multiple-choice questions

The system grades an Answer to a Multiple-choice question against the correct option stored with the Question (FR-7). When the Answer is graded incorrect, the system shows the correct option, the Explanation for the chosen option, and the Reference. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- The Grade appears within 1 second, with no call to the AI provider at answer time. `[ASSUMPTION: 1 second; checked by an automated test.]`
- Grading works the same in Mock mode and Real mode.

#### FR-12: Grade Answers to Free-text questions

The AI provider grades an Answer to a Free-text question against the model answer and the Source text at the Question's Reference, as correct, partially correct or incorrect, with an Explanation. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- The Student can see the model answer after grading.
- If grading fails, the Grade is "not graded", a message says what failed, and the Student can try again.
- After grading, the Student can override the Grade of their own Answer with correct, partially correct or incorrect. The overridden Grade is marked as overridden wherever it is shown, and it is the Grade used in the Topic score (FR-16) and the Retry round (FR-13).
- In Mock mode, a fixed rule gives a placeholder Grade, marked as mock.

#### FR-13: Result and Retry round

After a Quiz, the Student sees the score and the Grade of every Answer, and can start a Retry round. Realizes UJ-1.

**Consequences (testable):**
- A Retry round contains exactly the Questions graded incorrect or partially correct in the previous Quiz. A Question whose Answer is not graded is left out until that Answer is graded.
- The Student can repeat Retry rounds until every Question is answered correctly, or stop at any time.

#### FR-27: Quiz history

The Quiz area of a Topic lists the Student's earlier Quizzes in that Topic, newest first. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- Each row shows the date, the number of Answers graded correct and partially correct out of the total, and the Grade of each Answer.
- On the newest Quiz, when it has Answers graded incorrect or partially correct, the Student can start its Retry round (FR-13). Every other row opens the Quiz's result.
- The list says that Retry rounds do not count toward the Topic score (FR-16).
- With no Quiz yet, the Topic says that no Quiz has been taken in it.

### 4.5 Flashcards and spaced repetition (Must)

#### FR-14: Browse Flashcards

The Student can flip through the Flashcards of a Topic. Realizes UJ-1.

**Consequences (testable):**
- A Flashcard shows its front first; flipping it shows the back and the Reference.
- The Student can move forward and back through the Topic's Flashcards, in the order they were generated.
- Browsing does not change any Flashcard's next review date.

#### FR-15: Review Due cards

The Student can do a Review of Due today, rating each card Again, Hard, Good or Easy. The rating sets the card's next review date. Realizes UJ-2.

**Consequences (testable):**
- New Flashcards enter Due today in the order they were generated, at most 20 a day. `[ASSUMPTION: 20 a day; tuned after the first week of the Author's own use (SM-1).]`
- A card rated Again comes back before the Review ends.
- The interval after Good grows with each Good in a row (for example 1, 3, then 7 days) and is never longer than 180 days.
- The Review ends with the number of cards reviewed and the date of the next Due card.
- A Review started from a Topic (FR-23) holds only that Topic's Due cards.

### 4.6 Topic score, Weak topics and Next step (Must)

#### FR-16: Topic score

The system computes the Topic score from the Student's 20 most recent graded Answers in the Topic: correct counts 1, partially correct 0.5, incorrect 0. Realizes UJ-3.

**Consequences (testable):**
- A Topic with fewer than 5 graded Answers shows "not enough data" instead of a score.
- The Topic score updates each time a Grade is saved, including an overridden Grade (FR-12), so an abandoned Quiz updates it too.
- Answers in Retry rounds do not count, because the Student has just seen the Explanation. Answers that are not graded, and Flashcard ratings, do not count either.
- The Course score is the mean of the Topic scores of the Course's Topics that have a score. A Course where no Topic has one shows "not enough data". Home and the Course overview show the Course score, with a line that explains how it is computed.
- `[ASSUMPTION: the window of 20 Answers, the weights and the minimum of 5; tuned after the first week of the Author's own data (SM-1).]`

#### FR-17: Weak topics

The Course overview marks Topics with a Topic score below 60% as Weak topics, lowest first. The Student can start a Practice-mode Quiz with Questions from one or more Weak topics. Realizes UJ-3.

**Consequences (testable):**
- With seeded Answers that give three Topics scores of 40%, 55% and 80%, the first two are listed as Weak topics, in that order.
- A Quiz started from Weak topics contains only Questions from the chosen Topics.
- `[ASSUMPTION: the 60% threshold; tuned after the first week of the Author's own data (SM-1).]`

#### FR-28: Next step

Home and the Course overview each show exactly one Next step: one action, the reason for it with the numbers, and a button that starts it. Within the page's scope (all Courses on Home, one Course on the Course overview), the first of these that applies is chosen. Realizes UJ-2, UJ-3.

1. Due cards today: start a Review.
2. Weak topics: start a Practice-mode Quiz from the Weak topics (FR-17).
3. A Topic without Sources: add a Source to it.
4. Otherwise: a short message with no button, giving the date of the next Due card.

**Consequences (testable):**
- With seeded data that has both Due cards and Weak topics, the Next step is the Review. With no Due cards, it is the Quiz from the Weak topics.
- On the Course overview, only that Course's Due cards, Topics and Sources count.
- Every other action on the page is shown as secondary to the Next step.

### 4.7 Exam mode (Should)

#### FR-18: Exam-mode Quiz

The Student can start an Exam-mode Quiz from one or more Topics in a Course, choosing the number of Questions and the time limit. Realizes UJ-3.

**Consequences (testable):**
- No Hints are available, and no Grade or Explanation is shown before submission.
- The remaining time is always visible. When it runs out, the Answers given so far are submitted automatically.
- After submission, the result shows the score per Topic, and Answers to Free-text questions are graded then.
- Exam-mode Answers count toward the Topic score.
- `[ASSUMPTION: a default time limit of 30 minutes; tuned by the Author's own use.]`

### 4.8 Simpler explanation (Should)

#### FR-19: Ask for a Simpler explanation

The Student can ask for a Simpler explanation of a Key concept or a Flashcard. The AI provider writes it in the language of the Source, based on the text at the item's Reference. Realizes UJ-4.

**Consequences (testable):**
- A Simpler explanation is at most three sentences long. `[ASSUMPTION: three sentences; tuned by the content check in NFR-5.]`
- It is saved; asking again shows the saved one, with an option to make a new one.
- In Mock mode, the Key concepts of the Sample document have recorded Simpler explanations.

### 4.9 Running the app: Mock mode, Real mode and privacy (Must; FR-25 is Should)

#### FR-20: Mock mode by default

With no Key set, the app runs in Mock mode, whatever else is set, and shows that it does. Realizes UJ-5.

**Consequences (testable):**
- On a fresh clone, following the README, the Examiner can sign up, upload the Sample document, see its Study material, take a Quiz and a Retry round, and do a Review, without a Key and without network calls to an AI provider.
- The Sample document is copyright-free and stored in the repository together with its recorded responses.
- A Source other than the Sample document is stored in Mock mode, but the app says that generating Study material for it needs a Key; no Study material is made up for it.

#### FR-21: Real mode

Setting a Key and its AI provider in the environment configuration switches the app to Real mode. `.env.example` lists every setting, with no Key filled in. The default AI provider is Claude Haiku 5.5 from Anthropic, chosen by the Author on 2026-11-13; it has no free tier, so the Author pays for the Key, and the Examiner uses Mock mode. Realizes UJ-1.

**Consequences (testable):**
- The Key is never written to the repository, to logs or to the browser.
- A Key that the AI provider rejects gives a message that names the problem, and the app keeps running.

#### FR-22: Privacy notice

In Real mode, before the first upload, the Student is told that Source text is sent to the AI provider, and that some free tiers may use submitted content to improve the provider's products. The Student must accept before uploading. Realizes UJ-1.

**Consequences (testable):**
- No Source text is sent to an AI provider before the Student has accepted.
- The notice is shown once per Student.

#### FR-25 (Should): Hosted instance

The Author can run one Hosted instance for personal use, reachable from a phone. Realizes UJ-2.

**Consequences (testable):**
- Sign-up on the Hosted instance is closed to everyone except the Author, by a setting in the environment configuration.
- Data on the Hosted instance survives restarts and new deployments.

## 5. Cross-cutting NFRs

- **NFR-1 Responsive web.** UJ-1, UJ-2, UJ-3 and UJ-5 work in the latest Chrome, Safari and Firefox on desktop and phone, from a 360 px wide screen and up, without horizontal scrolling.
- **NFR-2 Runnable from the README.** From a fresh clone, the Examiner can start the app in Mock mode within 15 minutes, using only the README and free tools, with no paid account and without the Hosted instance. `[ASSUMPTION: 15 minutes; checked by a run from a fresh clone on another machine.]`
- **NFR-3 Response times.** In Real mode, the Study material for a 20-page PDF is ready within 2 minutes, and an Answer to a Free-text question is graded within 15 seconds. In Mock mode, every response comes within 5 seconds. `[ASSUMPTION: the time limits; measured in Real mode on the Author's own material.]`
- **NFR-4 Security.** Passwords are stored only as hashes from a function made for passwords (slow and salted). Every request checks that the data belongs to the signed-in Student. Keys and other secrets live only in the environment configuration, which git ignores.
- **NFR-5 Testability.** The logic in the app's own code has automated tests that run without a Key and without network access: upload limits, Reference checks, grading of Answers to Multiple-choice questions, Retry rounds, review dates, Topic scores and the daily limit in NFR-7. The README says how to run them. Before the technology stack is locked, text extraction is tested on at least three of the Author's own slide decks, and the result is written down. **Content check in Real mode:** for one fixed set of the Author's own lecture notes of 10–20 pages, which the Author knows well, the Author judges 15 Questions against the Source; at least 12 must be correct and answerable from the Source. The Author also grades 10 Answers to Free-text questions independently; at least 8 of the AI provider's Grades must match the Author's. Both results are written down. Mock mode tests only the flow, not the quality of the content. `[ASSUMPTION: 12 of 15 and 8 of 10.]`
- **NFR-6 Interface language.** Buttons, messages and the privacy notice are in Norwegian (bokmål), whatever the language of the Study material.
- **NFR-7 Daily limit on Generation calls.** Each Student can make at most 20 Generation calls a day: generating Study material, retrying generation, regenerating a Summary and making a new Simpler explanation. Grading Answers to Free-text questions does not count, so a Quiz never stops partway. When the limit is reached, a message says when it resets, and no call is sent. The limit applies in Mock mode too, so an automated test can check it without a Key. `[ASSUMPTION: 20 a day; tuned against the AI provider's limits and the Author's cost.]`

## 6. Non-goals

- Competing with Quizlet, StudyFetch or Quizgecko. There is no payment, subscription or advertising.
- Native apps for phone, tablet or desktop, and offline use.
- Sharing, collaboration, tools for teachers, or any role other than Student.
- Free-form chat with the AI provider about the material; the Simpler explanation (FR-19) is the only open request to it.
- Password reset by email (FR-1), and export, for example of Flashcards to Anki.
- AI-made answers to practice exercises, checked against the web, which the brief dropped.

## 7. MVP scope

The Author confirmed this split and the build order on 2026-11-01. On 2026-11-13, the Author revised the cut lines after the teacher's feedback and added FR-27 and FR-28 from the UX work, both in step 2.

### 7.1 Must (delivered 7 December 2026)

FR-1 to FR-4, FR-6 to FR-17, FR-20 to FR-24, FR-27, FR-28, and NFR-1 to NFR-7.

Build order:
1. Core loop, done and tested by 20 November 2026: FR-1 to FR-4, FR-6 to FR-13, FR-20 to FR-24.
2. Practice over time, done by 30 November 2026: FR-14 to FR-17, FR-27 and FR-28. FR-20 is fully checked at the end of this step: the Examiner's path in it includes a Review, which needs FR-15.

Cut lines. Either cut is recorded by the Author when it happens.
- **20 November 2026:** if step 1 is not done and tested, FR-24 moves to Should. This cut leaves the bet in §1 intact.
- **30 November 2026:** if step 2 is not done, FR-16 and FR-17 move to Should, and with them the Course score and step 2 of the Next step (FR-28). UJ-3 then becomes Should, and SM-4 and SM-2 check 8 are dropped, since they measure FR-16 and FR-17.

### 7.2 Should (only after every Must FR is done and tested)

FR-5 Word files, FR-18 Exam mode, FR-19 Simpler explanation, FR-25 Hosted instance, FR-26 Background generation.

### 7.3 Out of scope for v1

- **Images and handwriting (OCR).** Not covered by the research, and an image has no page to point to. `[NOTE FOR PM: the Author asked for images; revisit if the Must FRs are done early, after answering §9 question 1.]`
- **Old exam tasks:** breaking a large exam task into smaller sub-tasks; see `addendum.md`. `[NOTE FOR PM: the Author asked for this; revisit if the Must FRs are done early.]`
- Everything in §6.

## 8. Success metrics

**Primary**
- **SM-1 Personal use.** From the first working version until delivery, the Author completes at least three Quizzes or Reviews a week, in at least two Courses, measured from stored Answers and Reviews. `[ASSUMPTION: the target; judged at delivery.]` Validates FR-10 to FR-17.
- **SM-2 Acceptance checklist.** Every check passes, either by following the README (R) or by an automated test from NFR-5 (T). Checks 1–6 are the brief's functional criteria.
  1. (R) The Sample document gives the Study material in FR-7.
  2. (R) The Generated item with a wrong Reference is removed (FR-8).
  3. (R) The app runs in Mock mode without a Key (FR-20, NFR-2).
  4. (R) Uploads over the limits are rejected (FR-3).
  5. (R) Quizzes are graded, and Questions graded incorrect or partially correct go into a Retry round (FR-11 to FR-13).
  6. (R) Data is stored per Student, Course and Topic, and is still there after signing in again (FR-1, FR-2).
  7. (T) Review dates follow FR-15.
  8. (T) Weak topics are shown as in FR-17.
  9. (T) Generation calls stop at the daily limit in NFR-7.
  10. (T) The Next step follows the order in FR-28.

**Secondary**
- **SM-3 Reference quality.** On the Author's own material in Real mode, at least 90% of Generated items pass the check in FR-8. `[ASSUMPTION: the target; judged at delivery.]` Validates FR-8.
- **SM-4 Loop effect.** Of the Questions the Author answers incorrectly or partially correctly, at least 60% are answered correctly the next time they come up in a later Quiz that is not a Retry round, measured from stored Answers. `[ASSUMPTION: the target; judged at delivery.]` Validates the bet in §1 and FR-13, FR-16, FR-17. Dropped if the 30 November cut line in §7.1 is used.

**Counter-metrics (do not optimize)**
- **SM-C1 Number of Generated items.** Beyond the minimums in FR-7, more Flashcards or Questions are not better if fewer of them pass the check in FR-8. Counterbalances SM-2 check 1.
- **SM-C2 Topic score.** A high Topic score can come from seeing the same Questions again and again. Do not make Questions easier or repeat them to raise scores. Counterbalances SM-1, SM-4 and FR-16.

## 9. Open questions

1. **Images:** if they come into scope, are they handwritten notes, or photos and screenshots of printed text and slides? Owner: the Author. Not blocking v1.

## 10. Starting values to tune

The Author confirmed on 2026-11-13 that every other former assumption is a decision; those carry no tag. Each value below is a starting value, tuned by the test named.

| Where | Starting value | Tuned by |
|---|---|---|
| FR-3 | Upload limits: 50 pages, 10 MB, 150,000 characters | Extraction test in NFR-5; AI provider's token limits |
| FR-7 | At least 5 Key concepts and 10 Questions | Content check in NFR-5 |
| FR-8 | Quotes of at least 5 words | SM-3 |
| FR-10 | 10 Questions by default | Own use (SM-1) |
| FR-11 | Grade within 1 second | Automated test |
| FR-15 | 20 new Flashcards a day | First week of own use (SM-1) |
| FR-16 | Window of 20 Answers, weights, minimum of 5 | First week of own data (SM-1) |
| FR-17 | Weak-topic threshold of 60% | First week of own data (SM-1) |
| FR-18 | Default time limit of 30 minutes | Own use |
| FR-19 | Simpler explanation of at most three sentences | Content check in NFR-5 |
| NFR-2 | Running in 15 minutes | Run from a fresh clone on another machine |
| NFR-3 | Response times | Measured in Real mode on own material |
| NFR-5 | 12 of 15 Questions; 8 of 10 Grades | Content check itself, at delivery |
| NFR-7 | 20 Generation calls a day | AI provider's limits and the Author's cost |
| SM-1, SM-3, SM-4 | Targets | Judged at delivery |
