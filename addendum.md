# Addendum: AI Study Buddy

Supporting context that does not belong in the brief itself, but is useful for downstream work (PRD, architecture).

## Technical decision points named by the assignment

The official oppgavetekst explicitly flags these as open "beslutningspunkter" for the build. They are architecture-level, not brief-level, decisions — captured here so the Architecture phase starts from them instead of rediscovering them:

- **Valg av LLM og konfidensnivå** — which model/provider to use, and how to handle or surface the model's confidence in generated content.
- **Granularitet på sammendrag** — how much control the user gets over summary detail level, and how that is implemented (e.g. prompt parameters vs. multiple passes).
- **Håndtering av tabeller/figurer** — how uploaded PDFs/slides with tables or figures are parsed and represented in generated summaries/flashcards/quiz, since these do not reduce cleanly to plain text.
- **Lokal behandling vs. sky** — whether note processing happens via a cloud LLM API, a locally-run model, or a hybrid, with implications for cost, privacy (relevant given login/storage of user material), and offline capability.

## Competitive landscape (background, not for the brief)

Research conducted during brief creation (Sept 2026) found the space crowded at the "upload notes → flashcards/summary/quiz" layer: Quizlet (Magic Notes), StudyFetch, Quizgecko, Wisdolia, and several smaller near-identical tools all do this already, mostly web-first with mobile added later. AI-in-education funding has cooled since 2020's peak; no comparable tool emphasizes teaching the user *how* AI processing works (the closest analog exists only in K-12 teacher-facing tools). This confirmed there is no product-level moat to claim here — consistent with the brief's "What Makes This Different" section, which deliberately does not compete on features.

## Rejected/descoped ideas (with rationale)

- **AI-generated answers to practice exercises, web-verified before showing to the student.** Considered early, then dropped entirely — not just deferred — because it required live web-search grounding and a verification layer, which is real added complexity against an assignment rated "Enkel" and a solo, ~3-month build. Not part of any future phase as currently scoped.
- **Four simultaneous platforms (mobile, web, iPad, desktop).** The original ambition. Descoped to a single responsive web app after checking it against the assignment's own difficulty rating and the fact that no comparable tool has ever launched multi-platform simultaneously (all research subjects sequenced web-first, mobile later). If revisited post-submission, mobile would be the natural next platform, not native iPad/desktop.
- **OCR of handwritten/photographed notes.** Explicitly deferred (not rejected) — PDF and typed text only for the December submission; images could be a real future extension.
