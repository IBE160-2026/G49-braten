# Acceptance criteria

Testable consequences per PRD requirement, grouped by capability. Every consequence that runs without a Key gets an automated test named after its FR (NFR-5). Values marked † are starting values; see the last section.

## CAP-1 Accounts (FR-1)
- After sign-out and sign-in, or an app restart, Courses, Topics, Sources, Study material, Answers and review dates are unchanged.
- A request for another Student's Source or Study material is refused and reveals nothing.
- Email and password only; no third-party login.

## CAP-2 Courses, Topics, Sources (FR-2)
- Every Source belongs to exactly one Topic, every Topic to exactly one Course.
- Deleting a Course, Topic or Source asks for confirmation, then removes everything under it, including Study material and Answers. No undo.
- The Course overview lists its Topics with each Topic score.

## CAP-3 Upload, Location, language (FR-3, FR-4, FR-6)
- PDF over 50 pages†, file over 10 MB†, or text over 150,000 characters† is rejected before processing, naming the limit.
- A PDF with no extractable text (scanned) is rejected: scanned documents are not supported in v1.
- Other file types are rejected with the list of supported types.
- One upload holds one file; several files become separate Sources.
- PDF Location is the viewer page index from 1, not the printed page number; the Sample document's stored text carries the right page index.
- Plain and pasted text: Location is the paragraph number.
- Text from two pages is never stored under one Location.
- Only PDF text is read: images and figures are skipped (a figure-only page gives no text); tables become plain text.
- A Norwegian Source gives Norwegian Study material, an English one English. A mixed-language Source uses its main language; no override in v1.

## CAP-4 Generation (FR-7, FR-9)
- After the Reference check, the Sample document gives a Summary, ≥ 5 Key concepts†, ≥ 10 Flashcards, ≥ 10 Questions† with both kinds present.
- Every Multiple-choice question has four options, exactly one correct, and an Explanation per option.
- A Key-concept definition is at most two sentences. A Hint is one sentence and never contains the correct option.
- The Summary can be regenerated at another Detail level without regenerating the rest.
- Generation runs while the Student waits, with a progress indicator.
- An interrupted generation shows as failed on return, never generating forever.
- An AI-provider error, refusal, cut-off or wrongly formatted response saves and shows nothing from that attempt; a message says what failed and offers retry.
- A rate-limit response asks the Student to wait and try later; the Source becomes failed with no partial Study material.
- Retry works without uploading again.

## CAP-5 Reference check (FR-8)
- Before an item is shown, its Location must exist in the Source and its quote must appear at that Location.
- A failing item is removed, not shown with a warning; the Topic shows the number removed.
- The quote is ≥ 5 words† and not text repeated on most pages (headers, footers).
- Matching normalizes whitespace, line breaks and hyphenation. The check does not judge content correctness.
- Explanations and Simpler explanations reuse their item's Reference; they add none.
- Mock recordings for the Sample document contain exactly one item with a wrong page index, so the Topic shows one removed item.
- No AI confidence score is shown anywhere.

## CAP-6 Topic page and deletion (FR-23, FR-24)
- A Topic has four areas: Summary (opens first), Quiz, Self-test, Sources.
- Summary area: one Summary per ready Source, newest first, each followed by its Key concepts with Location. No combined Topic Summary.
- Quiz area: start a Practice-mode Quiz; see Quiz history.
- Self-test area: browse Flashcards, start a Review of the Topic's Due cards, set up an Exam-mode Quiz (Should).
- Sources area: add a Source; see each Source status.
- Questions appear only inside a Quiz.
- A Key concept or Flashcard can be deleted from the Topic; a Question from a Quiz's feedback or result.
- A deleted item no longer appears in the Topic, Quizzes, Retry rounds or Due today; Answers to a deleted Question no longer count toward the Topic score.

## CAP-7 Practice-mode Quiz and grading (FR-10, FR-11, FR-12)
- The Student chooses the number of Questions (default 10†, at most the Topic's count); drawn in random order.
- The Hint shows only on request. Grade, Explanation and Reference appear right after each Answer.
- Answers are saved as given; an abandoned Quiz's Answers still count.
- Multiple-choice: graded in code against the stored correct option within 1 second†, no AI call at answer time, same in Mock and Real mode. An incorrect Answer shows the correct option, the Explanation for the chosen option and the Reference.
- Free-text: the AI provider grades against the model answer and the Source text at the Reference, as correct, partially correct or incorrect, with an Explanation. The model answer is visible after grading.
- If grading fails, the Grade is not graded, a message says what failed, and retry is possible.
- The Student can override their own Free-text Grade; the override is marked wherever shown and is the Grade used for Topic score and Retry round. The original Grade is kept beside it.
- Mock mode: a fixed rule gives a placeholder Grade marked as mock.

## CAP-8 Result, Retry round, history (FR-13, FR-27)
- After a Quiz: the score and every Answer's Grade.
- A Retry round holds exactly the Questions graded incorrect or partially correct in the previous Quiz; not-graded ones are left out until graded.
- Retry rounds repeat until all correct, or stop any time.
- History lists the Topic's Quizzes newest first: date, correct and partially correct out of total, each Answer's Grade.
- Only the newest Quiz with incorrect or partial Answers offers its Retry round; other rows open the result.
- The list states that Retry rounds do not count toward the Topic score. With no Quiz yet, the Topic says so.

## CAP-9 Flashcards and Review (FR-14, FR-15)
- A Flashcard shows its front first; flipping shows back and Reference. Browse forward and back in generation order. Browsing never changes a review date.
- Review rates each card Again, Hard, Good or Easy; the rating sets the next review date.
- New Flashcards enter Due today in generation order, at most 20 a day†.
- A card rated Again returns before the Review ends.
- The interval after Good grows with each Good in a row (e.g. 1, 3, 7 days), never above 180 days.
- The Review ends with the number reviewed and the date of the next Due card.
- A Review started from a Topic holds only that Topic's Due cards.

## CAP-10 Scores and Weak topics (FR-16, FR-17)
- Topic score = weighted mean of the 20 most recent graded Answers in the Topic†: correct 1, partially correct 0.5, incorrect 0†.
- Fewer than 5 graded Answers† shows "not enough data".
- Updates whenever a Grade is saved, overrides included.
- Excluded: Retry-round Answers, not-graded Answers, Flashcard ratings.
- Course score = mean of Topic scores that exist; none gives "not enough data". Home and Course overview show it with a line explaining the computation.
- Weak topic: Topic score below 60%†, listed lowest first. Seeded scores 40%, 55%, 80% list the first two, in that order.
- A Quiz started from Weak topics holds only Questions from the chosen Topics.

## CAP-11 Next step (FR-28)
- Home (all Courses) and Course overview (one Course) each show exactly one Next step: action, reason with numbers, start button. First that applies:
  1. Due cards today: start a Review.
  2. Weak topics: Practice-mode Quiz from them.
  3. A Topic without Sources: add a Source.
  4. Otherwise: a short message, no button, giving the next Due date.
- With both Due cards and Weak topics, it is the Review; with no Due cards, the Weak-topic Quiz.
- On the Course overview only that Course's data counts.
- Every other action on the page is secondary to it.

## CAP-12 Mock mode (FR-20)
- No Key means Mock mode whatever else is set, and the app shows it.
- From a fresh clone via the README, the Examiner can sign up, upload the Sample document, see its Study material, take a Quiz and a Retry round, and do a Review, with no Key and no network calls to an AI provider.
- The Sample document and its recorded responses are in the repository and copyright-free.
- Another Source is stored, with a message that generating Study material needs a Key; nothing is made up for it.

## CAP-13 Real mode, privacy, daily limit (FR-21, FR-22, NFR-7)
- Setting a Key and provider in the environment switches to Real mode. Default provider: Claude Haiku 5.5 (Anthropic). `.env.example` lists every setting with no Key filled in.
- The Key is never written to the repository, logs or browser.
- A rejected Key gives a message naming the problem; the app keeps running.
- In Real mode, before the first upload, the Student is told Source text is sent to the AI provider and that some free tiers may use it to improve products; the Student must accept. No Source text is sent before acceptance. Shown once per Student.
- At most 20 Generation calls† per Student per day: generate, retry, regenerate Summary, new Simpler explanation. Grading never counts. At the limit a message says when it resets and no call is sent. Applies in Mock mode too.

## CAP-14 Word files (FR-5, Should)
- For a .docx with headings, every Reference names a heading that exists in the file; without headings, paragraph numbers are used.

## CAP-15 Exam mode (FR-18, Should)
- Started from one or more Topics in a Course; the Student chooses the number of Questions and the time limit (default 30 minutes†).
- No Hints; no Grade or Explanation before submission.
- Remaining time always visible; at zero, Answers so far are submitted automatically.
- After submission: score per Topic; Free-text Answers graded then. Exam Answers count toward the Topic score.

## CAP-16 Simpler explanation (FR-19, Should)
- Written by the AI provider in the Source's language from the text at the item's Reference; at most three sentences†.
- Saved; asking again shows the saved one with an option to make a new one.
- In Mock mode the Sample document's Key concepts have recorded Simpler explanations.

## CAP-17 Hosted instance (FR-25, Should)
- Sign-up closed to everyone but the Author by an environment setting.
- Data survives restarts and new deployments.

## CAP-18 Background generation (FR-26, Should)
- After closing the browser during generation and returning, the Source shows generating, ready or failed, and Study material finished meanwhile is shown.

## Cross-cutting (NFR-1 to NFR-6)
- **NFR-1** UJ-1, UJ-2, UJ-3, UJ-5 work in the latest Chrome, Safari and Firefox on desktop and phone, from 360 px wide, without horizontal scrolling.
- **NFR-2** From a fresh clone, the Examiner starts Mock mode within 15 minutes† using only the README and free tools; no paid account, no Hosted instance.
- **NFR-3** Real mode: Study material for a 20-page PDF within 2 minutes†; Free-text grading within 15 seconds†. Mock mode: every response within 5 seconds†.
- **NFR-4** Passwords stored only as slow, salted password hashes. Every request checks ownership. Secrets only in git-ignored environment configuration.
- **NFR-5** Automated tests without Key or network cover upload limits, Reference checks, MC grading, Retry rounds, review dates, Topic scores and the daily limit; the README says how to run them. Before the stack is locked, text extraction is tested on ≥ 3 of the Author's slide decks and written down. Real-mode content check on one fixed 10–20 page set of the Author's notes: ≥ 12 of 15 Questions† correct and answerable from the Source; ≥ 8 of 10† AI Free-text Grades match the Author's. Both written down. Mock mode tests flow only.
- **NFR-6** Buttons, messages and the privacy notice in Norwegian bokmål, whatever the Study material's language.

## Starting values to tune (†)

| Where | Starting value | Tuned by |
|---|---|---|
| FR-3 | 50 pages, 10 MB, 150,000 characters | NFR-5 extraction test; AI provider token limits |
| FR-7 | ≥ 5 Key concepts, ≥ 10 Questions | NFR-5 content check |
| FR-8 | Quotes ≥ 5 words | SM-3 |
| FR-10 | 10 Questions default | Own use (SM-1) |
| FR-11 | Grade within 1 s | Automated test |
| FR-15 | 20 new Flashcards a day | First week of own use |
| FR-16 | Window 20, weights, minimum 5 | First week of own data |
| FR-17 | Threshold 60% | First week of own data |
| FR-18 | 30-minute default | Own use |
| FR-19 | ≤ 3 sentences | NFR-5 content check |
| NFR-2 | 15 minutes | Fresh-clone run on another machine |
| NFR-3 | Response times | Real mode on own material |
| NFR-5 | 12 of 15; 8 of 10 | Content check at delivery |
| NFR-7 | 20 calls a day | AI provider limits and Author's cost |
| SM-1, SM-3, SM-4 | Targets | Judged at delivery |
