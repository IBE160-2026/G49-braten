# Polish review: AI Study Buddy UX spines

Finalize polish, run 2026-11-05 with `skill:bmad-review lenses=structure,prose` on `DESIGN.md` (3,490 words, 818 of them YAML tokens) and `EXPERIENCE.md` (5,226 words). The structure lens ran first, and the prose lens ran on top of its findings. Reader type: humans, with AI coding agents as a second consumer. Style guide: Microsoft Writing Style Guide. Length target: shorter where possible, no number given. Nothing has been applied yet; the Author accepts or rejects each row.

**Read of the documents.** The two spines exist to give the Author and the workflows that follow (architecture, epics and stories, the build, human or AI) one binding contract: `DESIGN.md` for how AI Study Buddy looks, and `EXPERIENCE.md` for how it behaves.

**Structure model.** Reference/Database for both (random access, consistent schema, mutually exclusive sections). `DESIGN.md` Brand & Style is read as Explanation.

**Voice to preserve (prose pass).** Terse, declarative English with Glossary terms capitalized; component names as kebab-case identifiers; Norwegian microcopy in «»; FR and UJ references in parentheses.

## Findings

| ID | Pass | Original Text | Revised Text | Changes |
|---|---|---|---|---|
| S1 | structure | `EXPERIENCE.md`, Component Patterns: state behavior inside the rows source-row (generating, removed items, failure), score-meter (too few Answers), due-today-panel (nothing due, no Flashcards), free-text-answer (grading, not graded), result-summary (not graded) and upload-panel (rejection) | MERGE into State Patterns, which already has a row for each of these states. Each component row keeps its own interaction rules and ends with "States: see State Patterns." The wait-time copy (NFR-3) moves to the "Generating" row. | The same behavior is written twice in different words, so the two can drift apart. One source per state. Saves ~180 words. |
| S2 | structure | `DESIGN.md`, Colors: the Light and Dark columns of the token table (50 hex values) | CONDENSE: drop both columns; keep Token, Used for and Never for. | The frontmatter is the source of truth for values, and a second copy drifts. Saves ~60 words. Trade-off: a human reader looks up the hex values in the frontmatter. |
| S3 | structure | `DESIGN.md`, Typography: the column "Size / line height / weight" | CONDENSE: drop it; keep Role and Used for. | Repeats the frontmatter. Saves ~35 words. |
| S4 | structure | `DESIGN.md`, Layout & Spacing: the Home and Topic bullets | MERGE with `EXPERIENCE.md`, Responsive & Platform. `DESIGN.md` keeps only the two-thirds and one-third proportion; which column shows what, at which width, stays in `EXPERIENCE.md`. The `[ASSUMPTION]` moves with it. | The same layout is stated in both spines. Saves ~40 words. |
| S5 | structure | `DESIGN.md`, Brand & Style, last paragraph ("No UI component library is chosen yet…") | CUT. | Repeats the frontmatter description and `EXPERIENCE.md` Foundation, which owns the UI-system decision. Saves ~30 words. |
| S6 | structure | Focus rules for dialog and feedback-panel, in both `EXPERIENCE.md` Component Patterns and Accessibility Floor | MERGE: keep them in Accessibility Floor, and cut the focus sentences from the two component rows. | The same rule twice. Saves ~30 words. |
| S7 | structure | `EXPERIENCE.md` rows that restate PRD rules: dialog (the wording of the privacy notice, FR-22), question-card ("the Hint never contains the answer", FR-7), result-summary (which Questions a Retry round holds, FR-13) | CONDENSE each to its FR reference. | Restates the source; the PRD owns these rules. Saves ~35 words. |
| S8 | structure | `EXPERIENCE.md`, Inspiration & Anti-patterns, "Rejected" | MERGE: drop the items already in Interaction Primitives ("Banned") and in `DESIGN.md` Do's and Don'ts (streaks, points, confetti, sounds, red for Weak topics). Keep dense dashboards, the chat interface and endless feeds. | Mentioned three times. Saves ~20 words. |
| S9 | structure | `DESIGN.md`, Components prose (1,115 words) | QUESTION: CONDENSE each bullet to anatomy and state appearance, and leave colors and sizes to the frontmatter `components` tokens? | Much of the prose repeats the token map. Saves ~300 words. Trade-off: a human reader, such as the Examiner, must read the YAML to see colors and sizes. The shipped examples keep token names in prose, so keeping it is defensible. |
| S10 | structure | `DESIGN.md` frontmatter: `fontFamily` repeated in all nine typography roles | PRESERVE | Each role stays self-contained for code that reads the tokens. |
| S11 | structure | `EXPERIENCE.md`, the Voice and Tone label table and Key Flows | PRESERVE | The longest prose outside the tables, but it is what stories and the build read. |
| S12 | structure | `DESIGN.md`, Do's and Don'ts | PRESERVE | A recap of rules stated above; the spec keeps it as the closing section. |
| P1 | prose | `DESIGN.md`, flashcard: "or a crossfade when reduced motion is on." | "or changes instantly when reduced motion is on." | Conflicts with `EXPERIENCE.md` Interaction Primitives ("flips and slides become instant changes"), which owns motion behavior. |
| P2 | prose | `DESIGN.md`, session-header: "Next to it, the progress as text in `label` and a 4 px bar." | "In the middle, the progress as text in `label` and a 4 px bar." | `EXPERIENCE.md` and the quiz mock put the progress in the middle. |
| P3 | prose | `EXPERIENCE.md`, top-bar: "«I dag» shows the Due-card count when it is above 0 and opens Review." | "«I dag» opens Review and shows the Due-card count when the count is above 0." | "It" could mean «I dag» or the count. |
| P4 | prose | `DESIGN.md`, Colors: "A Weak topic means "practise this"" | "A Weak topic means "practice this"" | US spelling, per the Microsoft style guide. |
| P5 | prose | `EXPERIENCE.md`, Foundation: "and tablet sits in between." | "and the tablet sits in between." | Missing article. |
| P6 | prose | `EXPERIENCE.md`, State Patterns, Few Questions: "The Quiz length cannot exceed the Questions available (FR-10)." | "A Quiz cannot hold more Questions than are available (FR-10)." | Compares a length with a set. |
| P7 | prose | `EXPERIENCE.md`, Accessibility Floor: "which is below the PRD's 360 px floor." | "a stricter requirement than the PRD's 360 px." | "Below the floor" reads as failing it. |
| P8 | prose | `EXPERIENCE.md`, Interaction Primitives: "course-card and topic-row are clickable as a whole." | "The course-card and the topic-row are clickable as a whole." | A sentence should not start with a lowercase identifier. |

## Outside the lenses

The two frames in `mockups/key-topic.html` list the Sources in opposite orders, and neither spine says how Sources are ordered in a Topic. Proposal: list Sources newest first `[ASSUMPTION]`, so a Source that is still being generated sits on top. Add this to the source-row rule and fix the desktop frame.

## Summary

- **Recommendations:** 12 from the structure pass (eight changes, one of them a question, and three PRESERVE) and eight from the prose pass.
- **Estimated reduction if all are accepted except S9:** `DESIGN.md` about 165 words (4.7 %), to about 3,325; `EXPERIENCE.md` about 265 words (5.1 %), to about 4,960.
- **With S9:** `DESIGN.md` about 465 words (13.3 %), to about 3,025.
- **Length:** no number was given. Most of the length is contract content: 30 components, 28 states, five flows and the token map.
- **Comprehension trade-offs:** S2, and S9 if accepted. In both, a human reader must turn to the frontmatter for values.

## Findings as JSON

```json
[
  {"lens": "structure", "id": "S1", "location": "EXPERIENCE.md Component Patterns / State Patterns", "revised": "MERGE state behavior into State Patterns", "words": -180},
  {"lens": "structure", "id": "S2", "location": "DESIGN.md Colors token table", "revised": "CONDENSE: drop Light and Dark columns", "words": -60},
  {"lens": "structure", "id": "S3", "location": "DESIGN.md Typography table", "revised": "CONDENSE: drop size column", "words": -35},
  {"lens": "structure", "id": "S4", "location": "DESIGN.md Layout & Spacing; EXPERIENCE.md Responsive & Platform", "revised": "MERGE layout per breakpoint into EXPERIENCE.md", "words": -40},
  {"lens": "structure", "id": "S5", "location": "DESIGN.md Brand & Style, last paragraph", "revised": "CUT", "words": -30},
  {"lens": "structure", "id": "S6", "location": "EXPERIENCE.md Component Patterns / Accessibility Floor", "revised": "MERGE focus rules into Accessibility Floor", "words": -30},
  {"lens": "structure", "id": "S7", "location": "EXPERIENCE.md dialog, question-card, result-summary", "revised": "CONDENSE to FR references", "words": -35},
  {"lens": "structure", "id": "S8", "location": "EXPERIENCE.md Inspiration & Anti-patterns", "revised": "MERGE: drop items stated elsewhere", "words": -20},
  {"lens": "structure", "id": "S9", "location": "DESIGN.md Components prose", "revised": "QUESTION: CONDENSE to anatomy and states", "words": -300},
  {"lens": "structure", "id": "S10", "location": "DESIGN.md frontmatter typography", "revised": "PRESERVE", "words": 0},
  {"lens": "structure", "id": "S11", "location": "EXPERIENCE.md Voice and Tone, Key Flows", "revised": "PRESERVE", "words": 0},
  {"lens": "structure", "id": "S12", "location": "DESIGN.md Do's and Don'ts", "revised": "PRESERVE", "words": 0},
  {"lens": "prose", "id": "P1", "location": "DESIGN.md flashcard", "original": "or a crossfade when reduced motion is on.", "revised": "or changes instantly when reduced motion is on."},
  {"lens": "prose", "id": "P2", "location": "DESIGN.md session-header", "original": "Next to it, the progress", "revised": "In the middle, the progress"},
  {"lens": "prose", "id": "P3", "location": "EXPERIENCE.md top-bar", "original": "«I dag» shows the Due-card count when it is above 0 and opens Review.", "revised": "«I dag» opens Review and shows the Due-card count when the count is above 0."},
  {"lens": "prose", "id": "P4", "location": "DESIGN.md Colors", "original": "practise this", "revised": "practice this"},
  {"lens": "prose", "id": "P5", "location": "EXPERIENCE.md Foundation", "original": "and tablet sits in between.", "revised": "and the tablet sits in between."},
  {"lens": "prose", "id": "P6", "location": "EXPERIENCE.md State Patterns, Few Questions", "original": "The Quiz length cannot exceed the Questions available (FR-10).", "revised": "A Quiz cannot hold more Questions than are available (FR-10)."},
  {"lens": "prose", "id": "P7", "location": "EXPERIENCE.md Accessibility Floor", "original": "which is below the PRD's 360 px floor.", "revised": "a stricter requirement than the PRD's 360 px."},
  {"lens": "prose", "id": "P8", "location": "EXPERIENCE.md Interaction Primitives", "original": "course-card and topic-row are clickable as a whole.", "revised": "The course-card and the topic-row are clickable as a whole."}
]
```
