# Addendum: AI Study Buddy

Supporting context that does not belong in the brief itself, but is useful for downstream work (PRD, architecture).

## Technical decision points named by the assignment

The official "oppgavetekst" explicitly flags these as open "beslutningspunkter" for the build. They are architecture-level, not brief-level, decisions — captured here so the Architecture phase starts from them instead of rediscovering them:

- **Valg av LLM og konfidensnivå** — which model/provider to use, and how to handle or surface the model's confidence in generated content. **Direction after research (2026-10-28):** one provider layer with a deterministic mock provider as default and a real provider chosen via `.env`; a cheap cloud model for development (under ~2 cents per 20-page PDF). Confidence is handled by checking page numbers and quotes in code, not by model self-rating.
- **Granularitet på sammendrag** — how much control the user gets over summary detail level, and how that is implemented (e.g. prompt parameters vs. multiple passes).
- **Håndtering av tabeller/figurer** — how uploaded PDFs/slides with tables or figures are parsed and represented in generated summaries/flashcards/quizzes, since these do not reduce cleanly to plain text. **Direction:** own per-page extraction with page markers; no dated benchmark exists for lecture slides, so test on the author's own slides before the stack is locked.
- **Lokal behandling vs. sky** — whether note processing happens via a cloud LLM API, a locally-run model, or a hybrid, with implications for cost, privacy (relevant given login/storage of user material), and offline capability. **Direction:** cloud as the main route; local Ollama only as an optional provider (default context is 4k tokens on laptops under 24 GiB VRAM, and no Norwegian quality evidence was found). Gemini's free tier may use submitted content to improve Google's products, so sample material in the repo must be copyright-free.

## Competitive landscape (background)

Research conducted during brief creation (Sept 2026) found the space crowded at the "upload notes → flashcards/summary/quiz" layer. Quizlet (Magic Notes), StudyFetch, Quizgecko, Wisdolia, and several smaller near-identical tools already do this, mostly web-first with mobile added later. AI-in-education funding has cooled since 2020's peak, and no comparable tool emphasizes teaching the user *how* AI processing works (the closest analog exists only in K-12 teacher-facing tools). This confirmed there is no product-level moat to claim here — consistent with the brief's "What Makes This Different" section, which deliberately does not compete on features.

## Rejected/descoped ideas (with rationale)

- **AI-generated answers to practice exercises, web-verified before showing to the student.** Considered early, then dropped entirely — not just deferred — because it required live web-search grounding and a verification layer, which is real added complexity against an assignment rated "Enkel" and a solo, ~3-month build. Not part of any future phase as currently scoped.
- **Four simultaneous platforms (mobile, web, iPad, desktop).** The original ambition. Descoped to a single responsive web app after weighing it against the assignment's own difficulty rating and the fact that no comparable tool has ever launched multi-platform simultaneously (all research subjects sequenced web-first, mobile later). If revisited post-submission, mobile would be the natural next platform, not native iPad/desktop.
- **OCR of handwritten/photographed notes.** Explicitly deferred (not rejected) — PDF and typed text only for the December submission; images could be a real future extension.
- **Sending the native PDF to the model and using Claude Citations.** Considered during research, not chosen: Citations cannot be combined with structured JSON output, and a native PDF costs more tokens per page than own extraction.
- **Local model (Ollama) as the default.** Rejected as default: heavier setup for the examiner and unverified Norwegian quality. Kept as an optional provider.

## Research findings (2026-10-28)

Full report: `_bmad-output/planning-artifacts/research/technical-llm-choice-and-pdf-extraction-for-ai-stu-2026-10-28/research.md`. What it changes for PRD and architecture:

- **Mock mode tests plumbing, not AI quality.** Recorded fixtures prove the flow works for the examiner; real quality needs a key and the author's own test material.
- **Structured output.** All three major providers offer schema-constrained JSON; validate with Zod (JS) or Pydantic (Python) and check `stop_reason`/refusal before parsing.
- **Page references.** Insert page markers in the text sent to the model, ask for page number plus a verbatim quote, and verify both in code.
- **Libraries.** JS/TS: unpdf (MIT). Python: pypdf (BSD) or pdfplumber (MIT). PyMuPDF only after assessing its AGPL licence.
- **Size limit.** 50 pages / 10 MB is the author's judgment, not a sourced number; binding constraints are tokens per minute on free tiers and local context length.
- **Still open for architecture.** Real Gemini free-tier limits (read in AI Studio), stack choice (JS vs Python), login/storage solution, and whether to include a bring-your-own-key field in the UI.
