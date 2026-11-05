# Input reconciliation: AI Study Buddy UX

Finalize step "Inputs reconciled", run 2026-11-05 against `DESIGN.md` and `EXPERIENCE.md`. Done inline rather than with one subagent per input, because every input had been read in full in this session.

## Coverage per input

| Input | Covered | Gaps |
|---|---|---|
| PRD (`prd.md`) | All five journeys as Key Flows (UJ-1 to UJ-5). Every FR with a user-facing surface is in Information Architecture, Component Patterns or State Patterns. NFR-1 (browsers, 360 px), NFR-3 (wait times) and NFR-6 (Norwegian interface). The §6 Non-goals: no chat, offline mode, password reset, sharing or export | G1, G2, G3 |
| PRD addendum | Background generation with a stored status (FR-9), one Explanation per option (FR-11), Word headings as the Location (FR-5) | None |
| Product brief | A simple, responsive web app for phone, tablet and desktop; the course code as input; after generation, the Student browses Flashcards, reads the Summary and takes the Quiz in the app | None |
| Teacher feedback (2026-10-06) | Sketches of the course and chapter overview and of the view of generated content (`mockups/key-course-overview.html`, `mockups/key-topic.html`); responsive design as a clear requirement; a polished design for a project rated as simple | None |

## Gaps and fixes

All three were applied on 2026-11-05.

- **G1. Renaming and deleting (FR-2).** The draft let the Student rename and delete Courses, but not rename or delete Topics, or rename Sources. *Fix:* a «⋯» menu with rename and delete on topic-row and source-row.
- **G2. Creating Courses and Topics (FR-2).** «Nytt fag» and «Nytt tema» had no defined surface. *Fix:* both open a dialog that asks for a name, plus an optional course code for a Course.
- **G3. Waiting for generation (NFR-3).** The Student was not told how long generation takes. *Fix:* while generating, the source-row adds «Vanligvis under 2 minutter. Du kan gå fra siden imens.»

## Qualitative ideas

The Author's «trygghet, ro og oversiktlighet», «lyse farger» and the Apple reference are carried in `DESIGN.md` (Brand & Style, Colors) and in `EXPERIENCE.md` (Inspiration & Anti-patterns). None were dropped.
