# Polish review: AI Study Buddy PRD

Finalize step 5, run 2026-11-01 with `skill:bmad-review lenses=structure,prose` on `prd.md` (5,437 words) and `addendum.md` (653 words). The structure lens ran first, and the prose lens ran on top of its findings. Reader type: humans. Style guide: Microsoft Writing Style Guide. Length target for `prd.md`: about 4,400 words. Nothing has been applied yet; the Author accepts or rejects each row.

**Read of the documents.** `prd.md` exists to help the Author, the Examiner and the BMad workflows that follow (UX, architecture, epics) know exactly what v1 of AI Study Buddy must do, in testable terms, and what is out. `addendum.md` exists to give architecture and stories the technical detail and deferred context that the PRD leaves out.

**Structure models.** Strategic/Context (Pyramid) for `prd.md`; Reference/Database for `addendum.md`.

**Voice to preserve (prose pass).** Plain, declarative present tense; Glossary terms capitalized as a deliberate convention; the user referred to as "the Author" in the third person; ISO dates; short fragments in the Glossary.

## Findings

| ID | Pass | Original Text | Revised Text | Changes |
|---|---|---|---|---|
| S1 | structure | `prd.md` §0, "Changes from the product brief": the whole table (250 words) | MOVE to `addendum.md` as a section "Changes from the product brief" before "Pointers". In §0, end the last sentence with "…with notes in `addendum.md`, which also lists the changes from the product brief." | The table records how the PRD departs from the brief; §4 and §7 already state the resulting scope, so it is history, not requirement. §1 Vision then follows the purpose directly. Trade-off: the Examiner opens the addendum to see the changes. Alternative with no saving: MOVE it to §7 as "7.4 Changes from the product brief". Saves ~242 words. |
| S2 | structure | `prd.md` §10 Assumptions Index (266 words, 29 lines) | QUESTION: keep it, or CONDENSE to "Unconfirmed inferences are tagged `[ASSUMPTION]` in FR-1 to FR-12, FR-15 to FR-19, FR-22, FR-23, FR-25, NFR-1 to NFR-3, NFR-5, §6, SM-1, SM-3 and SM-4." | Each line repeats an inline tag almost word for word. It earns its place if the Author uses it as the checklist when the deferred assumptions are revisited after own use (step 4 triage). Condensed, it saves ~235 words. |
| S3 | structure | FR-11, second sentence: "The AI provider writes an Explanation for every option when it generates the Question, so grading needs no call to the AI provider." | CUT, and end the first sentence with "(FR-7)". | FR-7 already requires an Explanation for each option, and FR-11's first consequence already rules out a call at answer time. Saves ~22 words. |
| S4 | structure | The nine "Realizes UJ-n." lines under §4.1 to §4.9 | CUT; keep the FR-level lines. | The section lines repeat the FR lines. QUESTION: §4.4 names UJ-1 and UJ-3, but FR-10 to FR-13 name only UJ-1. Add UJ-3 to the FRs that UJ-3 uses (FR-10 to FR-12?), or drop it. FR-3 to FR-6, FR-9, FR-21 and FR-24 then name no journey, which the template does not require. Saves ~25 words. |
| S5 | structure | (a) FR-23: "and each Source shows whether its generation is running, done or failed"; (b) FR-25: "The Examiner's local path in FR-20 and NFR-2 does not depend on it."; (c) FR-1's tag: "and no password reset" | (a) "and each Source shows its status from FR-9"; (b) CUT, since NFR-2 says "without the Hosted instance"; (c) CUT from FR-1's tag and from §10's FR-1 line, and add "no password reset" to §10's §6 line, since §6 states it. | Three small duplicates, each with one source of truth. Saves ~21 words. |
| S6 | structure | Tags that restate the sentence they qualify: NFR-3 "[ASSUMPTION: all three limits.]", SM-1 "[ASSUMPTION: the targets.]", SM-3 "[ASSUMPTION: 90 %.]", SM-4 "[ASSUMPTION: the target.]", and the tag bullets in FR-15 and FR-19 | CONDENSE to a bare `[ASSUMPTION]` right after the sentence or clause it qualifies (in FR-15 and FR-19, after consequences 1 and 2). | Matches the bare form already used in FR-2, FR-8, FR-9 and FR-23 when the whole sentence is assumed. Detailed tags stay where a sentence mixes confirmed and assumed values (FR-7, FR-16, FR-18). Saves ~29 words. |
| S7 | structure | §3 Glossary (611 words, 11 % of the PRD) | PRESERVE | The largest section and the obvious cut, but it anchors the terms that UX, architecture and epics must reuse. Cutting it brings back the term drift the review fixed. |
| S8 | structure | §2.1 Key User Journeys, with their edge cases (459 words) | PRESERVE | The edge cases repeat FR-3 and FR-20, but as concrete examples they are what `bmad-ux` builds screens from. |
| S9 | structure | FR-23 and FR-24 inside §4.3; FR-25 inside §4.9 | PRESERVE | Out of numeric order because IDs are stable; renumbering would break references in `.memlog.md` and `review-rubric.md`. |
| S10 | structure | `addendum.md`, "Implementation notes": ten notes in discovery order, with two separate notes on FR-12 | MOVE: sort the notes by FR number (FR-5, FR-6, FR-8, FR-9, FR-11, FR-12, FR-15, FR-16/17, FR-25). MERGE the two FR-12 notes by appending "In Mock mode, a fixed rule, for example word overlap with the model answer, gives a placeholder Grade marked as mock; it tests the flow, not the quality of the AI provider." to the grading note. | The addendum is read by lookup from an FR, so FR order makes each note easy to find. Saves ~3 words. |
| S11 | structure | `addendum.md`, Topic score: "A window of 20 graded Answers, 0.5 for partially correct, a minimum of 5 Answers and a 60 % threshold are starting values. Tune them after the Author's own use." | CONDENSE: "The window, weights, minimum and threshold are starting values; tune them after the Author's own use." | FR-16 and FR-17 state the numbers; only "starting values" is new here. Saves ~14 words. |
| S12 | structure | `addendum.md`, Deferred features, Images: "The teacher's feedback named the OCR deferral as a strength of the brief." | CUT, only if S1 is accepted. | The moved table's Images row says the same. Saves ~13 words. |
| P1 | prose | FR-8: "A Generated item that fails the check is hidden, not shown with a warning, and the Topic shows how many were removed." | "A Generated item that fails the check is removed, not shown with a warning, and the Topic shows the number removed." | "Hidden" and "removed" name the same outcome; UJ-5, FR-8's Mock-mode consequence and SM-2 check 2 say "removed". "Hidden" came in when the Author confirmed hide versus flag today. |
| P2 | prose | FR-9: "The Student sees whether generation of a Source is running, done or failed." | "The Student sees the status of each Source: generating, ready or failed." | The same three states have two sets of names; FR-9's first consequence and the addendum say "generating, ready, failed". If S5 is rejected, use the same words in FR-23. |
| P3 | prose | FR-13: "left out until it is graded." / "until every Question is correct" | "left out until that Answer is graded." / "until every Question is answered correctly" | "It" could mean the Question or the Answer, and Grades belong to Answers (§3). |
| P4 | prose | §7.1: "FR-20 is fully checked at the end of this step, since its Review needs FR-15." | "FR-20 is fully checked at the end of this step: the Examiner's path in it includes a Review, which needs FR-15." | "Its Review" has no clear owner. |
| P5 | prose | §1: "what the Student practises next" / "That replaces passive re-reading, and chat conversations with ChatGPT or Claude that vanish into a chat log, with material the Student can practise on all semester." | "what the Student practices next" / "Instead of passive re-reading, or chat conversations with ChatGPT or Claude that vanish into a chat log, the Student gets material to practice on all semester." | "Replaces X, and Y, with Z" is hard to parse with two instances of "with". US spelling, as in the rest of the document. |
| P6 | prose | FR-5 and `addendum.md` (Word files): "the nearest heading" | Consider: "the nearest heading above the text"? | "Nearest" could also mean the next heading below; an implementer needs one rule. |
| P7 | prose | FR-9 and FR-12: "the message says what failed" | "a message says what failed" | No message has been introduced, so "the" points to nothing. |
| P8 | prose | FR-21: "Setting a Key, and the AI provider it belongs to, in the environment configuration switches the app to Real mode." | "Setting a Key and its AI provider in the environment configuration switches the app to Real mode." | The inserted clause splits the subject from its verb. |
| P9 | prose | FR-3's tag: "to be confirmed by tests on the Author's own notes and the token limits of free tiers." | "to be confirmed by tests on the Author's own notes and against the token limits of free tiers." | As written, the tests run "on" the token limits. |
| P10 | prose | NFR-4: "Passwords are stored only with a hash function made for passwords (slow and salted)." | "Passwords are stored only as hashes from a function made for passwords (slow and salted)." | What is stored is the hash, not the function. |
| P11 | prose | NFR-5: "run without a Key and without network:" | "run without a Key and without network access:" | "Without network" reads as a fragment. |
| P12 | prose | §3 (Retry round) and FR-13: "in the Quiz before" | "in the previous Quiz" | Standard phrasing, same meaning. |
| P13 | prose | Headings in title case: "Document Purpose", "Target User", "Key User Journeys", "Cross-Cutting NFRs", "Non-Goals", "MVP Scope", "Out of Scope for v1", "Success Metrics", "Open Questions", "Assumptions Index" | Consider: sentence case ("Document purpose", "Target user", …), as in §4 and per the Microsoft style guide? | Two capitalization styles in one set of headings. Keep title case if later BMad workflows look up the template's section names. |
| P14 | prose | "60 %", "45 %", "90 %" and nine more, in both documents | Consider: "60%" without a space, per the Microsoft style guide? | The space is the Norwegian convention. Low impact. |
| P15 | prose | `addendum.md`, Spaced repetition: "hold for Leitner boxes and the SuperMemo-2 algorithm" | "can be met with either Leitner boxes or the SuperMemo-2 algorithm" | "Hold for" is vague. |

## Summary

- **Recommendations:** 12 from the structure pass (six changes to `prd.md`, one of them a question; three PRESERVE; three in `addendum.md`) and 15 from the prose pass.
- **Estimated reduction in `prd.md` if all are accepted:** about 339 words (6.2 %), from 5,437 to about 5,100. With S2 condensed: about 574 words (10.6 %), to about 4,860. The prose rows change the count by only a few words.
- **`addendum.md`:** from 653 to about 873 words with S1, or about 636 without it.
- **Length target (about 4,400):** not met. The remaining 460 to 700 words would have to come from requirements, journeys or the Glossary. That is a content decision, not an editorial one.
- **Comprehension trade-offs:** S1 (the Examiner opens the addendum to see the changes from the brief) and, if condensed, S2 (the Author searches for tags instead of reading one list).

## Findings as JSON

```json
[
  {"lens": "structure", "id": "S1", "location": "prd.md §0 Changes from the product brief", "revised": "MOVE to addendum.md; pointer in §0", "words": -242},
  {"lens": "structure", "id": "S2", "location": "prd.md §10 Assumptions Index", "revised": "QUESTION: keep, or CONDENSE to one sentence", "words": -235},
  {"lens": "structure", "id": "S3", "location": "prd.md FR-11 description", "revised": "CUT second sentence; add (FR-7)", "words": -22},
  {"lens": "structure", "id": "S4", "location": "prd.md §4.1-§4.9 Realizes lines", "revised": "CUT; QUESTION on UJ-3 in §4.4", "words": -25},
  {"lens": "structure", "id": "S5", "location": "prd.md FR-23, FR-25, FR-1 tag, §10", "revised": "CONDENSE three duplicates", "words": -21},
  {"lens": "structure", "id": "S6", "location": "prd.md NFR-3, SM-1, SM-3, SM-4, FR-15, FR-19 tags", "revised": "CONDENSE to bare tags", "words": -29},
  {"lens": "structure", "id": "S7", "location": "prd.md §3 Glossary", "revised": "PRESERVE", "words": 0},
  {"lens": "structure", "id": "S8", "location": "prd.md §2.1 Key User Journeys", "revised": "PRESERVE", "words": 0},
  {"lens": "structure", "id": "S9", "location": "prd.md FR-23, FR-24, FR-25 placement", "revised": "PRESERVE", "words": 0},
  {"lens": "structure", "id": "S10", "location": "addendum.md Implementation notes", "revised": "MOVE into FR order; MERGE FR-12 notes", "words": -3},
  {"lens": "structure", "id": "S11", "location": "addendum.md Topic score note", "revised": "CONDENSE", "words": -14},
  {"lens": "structure", "id": "S12", "location": "addendum.md Deferred features, Images", "revised": "CUT if S1 is accepted", "words": -13},
  {"lens": "prose", "id": "P1", "location": "prd.md FR-8", "original": "is hidden, not shown with a warning, and the Topic shows how many were removed.", "revised": "is removed, not shown with a warning, and the Topic shows the number removed."},
  {"lens": "prose", "id": "P2", "location": "prd.md FR-9 (and FR-23)", "original": "whether generation of a Source is running, done or failed.", "revised": "the status of each Source: generating, ready or failed."},
  {"lens": "prose", "id": "P3", "location": "prd.md FR-13", "original": "until it is graded. / until every Question is correct", "revised": "until that Answer is graded. / until every Question is answered correctly"},
  {"lens": "prose", "id": "P4", "location": "prd.md §7.1", "original": "since its Review needs FR-15.", "revised": ": the Examiner's path in it includes a Review, which needs FR-15."},
  {"lens": "prose", "id": "P5", "location": "prd.md §1", "original": "practises / That replaces passive re-reading, and chat conversations ... with material the Student can practise on all semester.", "revised": "practices / Instead of passive re-reading, or chat conversations ... the Student gets material to practice on all semester."},
  {"lens": "prose", "id": "P6", "location": "prd.md FR-5; addendum.md Word files", "original": "the nearest heading", "revised": "Consider: the nearest heading above the text?"},
  {"lens": "prose", "id": "P7", "location": "prd.md FR-9, FR-12", "original": "the message says what failed", "revised": "a message says what failed"},
  {"lens": "prose", "id": "P8", "location": "prd.md FR-21", "original": "Setting a Key, and the AI provider it belongs to, in the environment configuration", "revised": "Setting a Key and its AI provider in the environment configuration"},
  {"lens": "prose", "id": "P9", "location": "prd.md FR-3 tag", "original": "and the token limits of free tiers", "revised": "and against the token limits of free tiers"},
  {"lens": "prose", "id": "P10", "location": "prd.md NFR-4", "original": "stored only with a hash function made for passwords", "revised": "stored only as hashes from a function made for passwords"},
  {"lens": "prose", "id": "P11", "location": "prd.md NFR-5", "original": "without network:", "revised": "without network access:"},
  {"lens": "prose", "id": "P12", "location": "prd.md §3, FR-13", "original": "in the Quiz before", "revised": "in the previous Quiz"},
  {"lens": "prose", "id": "P13", "location": "prd.md headings in title case", "original": "Document Purpose, Target User, ...", "revised": "Consider: sentence case?"},
  {"lens": "prose", "id": "P14", "location": "prd.md, addendum.md percentages", "original": "60 %", "revised": "Consider: 60%?"},
  {"lens": "prose", "id": "P15", "location": "addendum.md Spaced repetition", "original": "hold for Leitner boxes and the SuperMemo-2 algorithm", "revised": "can be met with either Leitner boxes or the SuperMemo-2 algorithm"}
]
```
