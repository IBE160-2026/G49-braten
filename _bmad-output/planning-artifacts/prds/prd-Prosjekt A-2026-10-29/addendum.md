# Addendum: AI Study Buddy PRD

Detail for architecture and stories that does not belong in the PRD itself, plus the changes from the product brief. Terms follow the PRD Glossary.

## Implementation notes from discovery and review (2026-11-01)

- **Word files (FR-5).** A .docx stores no fixed page numbers; pagination depends on how the file is rendered. The Location is therefore the nearest heading above the text. Pick the extraction library with the stack (for example mammoth for JS/TS, python-docx for Python).
- **Source language (FR-6).** Either ask the model to detect the language and answer in it, or detect it with a library before the call. Record the Mock-mode responses in the Sample document's language.
- **Reference check (FR-8).** Put page markers in the text sent to the model, ask for a page number plus a verbatim quote, and normalize whitespace, line breaks and hyphenation before matching. Extraction from slides can split or merge words (research B2). Detect repeated headers and footers by finding text that appears on most pages.
- **Background generation (FR-9).** Generation that survives the Student leaving the page needs a background job with a stored status (generating, ready, failed) that the Topic reads, rather than one long request.
- **Grading Answers to Multiple-choice questions (FR-11).** Store the correct option and one Explanation per option when the Question is generated. Grading is then a comparison in code: instant, deterministic, and testable in Mock mode. This is the reading of the Author's wish "KI skal sjekke flervalg (retting med feil)" that the Author confirmed on 2026-11-01: the AI provider writes the Questions and Explanations, and the code checks the Answer.
- **Grading Answers to Free-text questions (FR-12).** Send the Question, the model answer, the Student's Answer and the Source text at the Reference Location, and ask for schema-constrained output (Grade and Explanation). Check for refusal and cut-off output before parsing (research A3). In Mock mode, a fixed rule, for example word overlap with the model answer, gives a placeholder Grade marked as mock; it tests the flow, not the quality of the AI provider.
- **Spaced repetition (FR-15).** Candidates: Leitner boxes (simplest), the SuperMemo-2 algorithm (classic, maps directly to four ratings) and FSRS (more accurate, more complex). FR-15's testable consequences, including the maximum interval and the daily limit on new Flashcards, can be met with either Leitner boxes or the SuperMemo-2 algorithm. Choose in architecture.
- **Topic score (FR-16, FR-17).** The window, weights, minimum and threshold are starting values; tune them after the Author's own use.
- **Hosted instance (FR-25).** Closing sign-up can be as simple as an environment setting that lists the one allowed email address. The data must live in storage that survives redeploys, which rules out a database file inside a container that is replaced on every deploy.

## Deferred features (context for later)

- **Images.** Two routes: a vision-capable model reads the image directly, or OCR runs before the call. The research covered neither, quality on handwriting is unknown, and both routes affect Mock mode and References, since an image has no page number.
- **Old exam tasks.** The Author's answer (2026-11-01), in the Author's words: «appen skal gjøre at studenten får mer kontroll over oppgavene til eksamensoppgavene. Komme med deloppgaver som gjør det enklere å svare på de større og vanskeligere oppgavene». In short: break a large, difficult exam task into smaller sub-tasks that build up to the whole task. Still open for later design: whether each sub-task is answered and graded on its own, and whether the sub-tasks draw on the Course's Sources. See PRD §7.3.

## Changes from the product brief

| Area | Product brief (updated 2026-10-29) | This PRD | Why |
|---|---|---|---|
| Question types | Short and open questions | Multiple-choice questions and Free-text questions | Author's request in PRD discovery, 2026-11-01 |
| Output language | Chosen per upload | Follows the language of the Source (FR-6) | Author's request; one input fewer |
| Flashcards | Browsed in the app | Browsed, plus Reviews scheduled by spaced repetition (FR-15) | Author's request: repetition over time |
| Quiz results | Retry round | Retry round, plus Topic score and Weak topics (FR-16, FR-17) | Author's request; logic in the app's own code that can be tested |
| Exam mode | Not mentioned | Should (FR-18) | Author's request |
| Simpler explanation | Not mentioned | Should (FR-19) | Author's request |
| Word files | Not mentioned | Should (FR-5); References point to headings | Word files have no fixed page numbers |
| Hosted instance | Not mentioned | Should (FR-25): the Author's own copy, with sign-up closed to others | Raised in the PRD review; the Author's choice, 2026-11-01 |
| Images (OCR) | Deferred from v1 | Still out of v1 (PRD §7.3) | Not covered by the research; the teacher's feedback named the deferral as a strength |
| Old exam tasks | Not mentioned | Out of v1 (PRD §7.3): break a large exam task into smaller sub-tasks | Deferred in the v1 split the Author confirmed on 2026-11-01 |

## Pointers

- Research recommendations 1–7 and the questions still open for architecture: the research report and the brief addendum ("Still open for architecture").
- PRD review and how its findings were handled: `review-rubric.md`, `review-polish.md` and `.memlog.md` in this folder.
