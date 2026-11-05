# Input reconciliation: AI Study Buddy PRD

Finalize step 2, run 2026-11-01 against `prd.md` and `addendum.md`. Done inline rather than with one subagent per input, because every input had already been read in full in this session.

## Coverage per input

| Input | Covered | Gaps |
|---|---|---|
| Product brief (`brief.md`, updated 2026-10-29) | Problem and vision (§1), scope (§6, §7), the six functional criteria (SM-2 checks 1–6), privacy (FR-22), Mock mode (FR-20), size limit (FR-3), later platforms and OCR (§6, §7.3) | G4, G5, G6 |
| Brief addendum | Rejected ideas (§6), research direction (FR-8, FR-20 to FR-22). Decision points named by the assignment: choice of LLM (§9 question 3), summary granularity (Detail level, FR-7), local vs cloud (§9 question 3) | G1, G2 |
| Technical research (2026-10-28) | Recommendations 1, 3, 4, 6 and 7 (FR-20, FR-21, FR-9, FR-8, FR-3, NFR-5); 2 and 5 are left to architecture | None |
| Teacher feedback (2026-10-06) | Testable criteria (SM-2), Mock mode and `.env.example` (FR-20, FR-21), size limit (FR-3), building in steps (§7.1), an extension with its own logic (FR-13, FR-15 to FR-17), keys outside the repository (NFR-4) | G3 |
| Author's brain dump (2026-11-01) | Every item; see the change table in §0 | G7 |

## Gaps and proposed fixes

- **G1 Tables and figures.** The assignment names their handling as a decision point; the PRD says nothing. *Fix:* new consequence under FR-4: v1 reads only the text of a PDF; images and figures are skipped, and tables are read as plain text. `[ASSUMPTION]`
- **G2 Confidence level.** The assignment's decision point "konfidensnivå" is only covered indirectly, by FR-8. *Fix:* one sentence in the FR-8 description: the app shows no confidence score from the model; trust comes from the checked Reference.
- **G3 Fixed test material.** The teacher advises using the Author's own lecture notes, known well, as fixed test material for judging summaries and quizzes. *Fix:* add to NFR-5.
- **G4 Written report.** Part of the delivery, but not of the app. *Fix:* one sentence in §0 saying it is outside this PRD.
- **G5 Any subject.** The brief says the app is subject-agnostic. *Fix:* one line in §2.
- **G6 Course code.** The brief has course code as input. *Fix:* the Glossary entry for Course gets a name and an optional course code.
- **G7 Several files.** The brain dump says "laster inn diverse notater, dokumenter eller filer". *Fix:* consequence under FR-3: one file per upload, and a Topic can hold many Sources. `[ASSUMPTION]`

## Outcome

All seven fixes were applied on 2026-11-01 at the Author's request.
