# Product

> Drafted 2026-11-09 from the PRD, brief and UX docs without an init interview; facts marked (inferred) await the author's confirmation.

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Undecided; chosen in the architecture phase (bmad-architecture).

## Users

- **The Author, as the primary Student.** The student who builds AI Study Buddy alone as the course project in IBE160 Programmering med KI at Høgskolen i Molde, autumn 2026, and will use it in the Author's own courses through the semester. Today the Author re-reads notes, copies them out by hand and asks ChatGPT or Claude when something is unclear, with no system for repetition or self-testing. The planning documents call this student Ida.
- **Students in any subject.** Nothing in the app is tailored to one field; the Author's own study life is the reference for what is useful.
- **The Examiner,** who assesses the project by cloning the repository and running the app from the README without the Author's API key. The planning documents call the Examiner Jonas.
- The app has one role, Student. There are no teachers, shared spaces or other roles.

## Product Purpose

AI Study Buddy turns a student's own course material into active self-testing. The Student uploads lecture slides, notes or textbook chapters into a Course and a Topic and gets a Summary, Key concepts, Flashcards and a Quiz of Multiple-choice and Free-text questions. Every Key concept, Flashcard and Question points back to where in the Source it came from. The app exists because course material is processed by hand and unsystematically, and chats with ChatGPT or Claude vanish into a chat log instead of becoming something to practice on. In the Author's own words, active self-testing is what matters most (PRD memlog).

Success means:

- The Author really uses it through the semester: at least three Quizzes or Reviews a week, in at least two Courses, until delivery (SM-1; the target is a working value).
- The eight-point acceptance checklist passes, by following the README or by automated tests (SM-2).
- At least 90 % of Generated items pass the reference check on the Author's own material, and at least 60 % of missed Questions are answered correctly the next time they come up (SM-3, SM-4; working values).
- More Generated items or higher Topic scores are not goals in themselves (counter-metrics SM-C1, SM-C2).

## Positioning

- It does not compete with Quizlet, StudyFetch or Quizgecko. Generating study material is not new, and no product-level moat is claimed.
- The bet is closing the loop between testing and repetition: every Answer decides what the Student practices next. Missed Questions return in a Retry round, Flashcards come back on a schedule set by how well they were remembered, and Topic scores show which Topics need work before the exam.
- Trust comes from checked References, not from the model rating itself. The code verifies that each item's page exists and that its quote stands on that page. Items that fail are removed and counted, and no AI confidence score is shown.
- It is the Student's own free tool, organized around their own courses and topics, with no payment, subscription or advertising. Building it end to end is the course's learning goal.

## Operating Context

- **The evening after a lecture, on a laptop:** the Student adds the day's slides to a Topic and takes a Quiz the same evening (UJ-1).
- **On the phone, away from home:** the Student clears the day's Due cards. This needs the Author's Hosted instance (FR-25), a Should feature (UJ-2).
- **Before an exam:** the Student drills Weak topics and sits a timed mock exam (UJ-3; Exam mode is a Should feature).
- **Assessment:** the Examiner starts the app from a fresh clone within 15 minutes, in Mock mode and without a Key, and tries every core function on the Sample document (UJ-5, NFR-2). The teacher's feedback (2026-10-06) asked for sketches of the course and chapter overview and of the view of generated content, a responsive design for phone, tablet and desktop, and a well-worked design, since the project is rated simple.
- **Material:** text-based PDFs, plain-text files and pasted text; Word files are a Should feature. Study material comes out in the language of its Source, which may differ from the Norwegian interface.
- **Timeline:** delivery on 7 December 2026. If spaced repetition and Topic scores (FR-14 to FR-17) are not done by 30 November, Topic scores and Weak topics (FR-16, FR-17) move to Should.

## Capabilities and Constraints

**Must (7 December 2026):** sign-up and sign-in with email and password; create, rename and delete Courses, Topics and Sources, with a confirmation and no undo; upload one PDF or plain-text file, or paste text, with a Detail level of short, medium or detailed; generation in the background with the status generating, ready or failed, and a retry without a new upload; the reference check; reading the Study material per Source; deleting a single Generated item; Practice-mode Quizzes with Hints on request and feedback after each Answer; a result with a Retry round; browsing Flashcards; Reviews of Due today rated Again, Hard, Good or Easy; Topic scores and Weak topics; Mock mode by default and Real mode with a Key; the privacy notice before the first upload in Real mode.

**Should (built only after every Must is done and tested):** Word files, Exam mode, Simpler explanation, the Hosted instance.

**Out of v1:** images and handwriting (OCR), and breaking large exam tasks into sub-tasks. Non-goals: native apps, offline use, sharing and collaboration, teacher tools, free-form chat with the AI provider, password reset, export (for example to Anki), payment and advertising.

**Limits and rules:**

- A PDF over 50 pages, a file over 10 MB, or text over 150,000 characters is rejected before processing, with the limit named (working values). Scanned PDFs are rejected.
- Only text is read: figures are skipped and tables become plain text.
- The Location is the PDF page index, the paragraph number for plain text, or the nearest heading for Word.
- Answers to Multiple-choice questions are graded in code within 1 second. The AI provider grades Answers to Free-text questions within 15 seconds, and Study material for a 20-page PDF is ready within 2 minutes (NFR-3; working values).
- The Key lives only in the environment configuration, never in the repository, logs or browser. Every request checks that the data belongs to the signed-in Student.

**Terminology:** the PRD Glossary (Course, Topic, Source, Study material, Summary, Key concept, Flashcard, Question, Quiz, Retry round, Topic score, Weak topic, Mock mode, Real mode and the rest). The interface uses the Norwegian labels in the 2026-11-05 EXPERIENCE.md, Voice and Tone: fag, tema, kilde, studiemateriell, sammendrag, nøkkelbegrep, kort, repetisjon, «I dag», «Øv på feilene», mestring, «Trenger øving», øving, prøveeksamen, demomodus, eksempeldokumentet, KI-tjenesten.

**Undecided:**

- the default AI provider for Real mode and its free-tier limits;
- the technology stack, the UI library, and the login and storage solution;
- the spaced-repetition algorithm;
- which copyright-free Sample document ships;
- 29 PRD assumptions (PRD §10) and 18 UX assumptions from 2026-11-05, deferred until the Author has used the app or the screens are built.

## Brand Commitments

- **Name:** AI Study Buddy.
- **Feel:** «trygghet, ro og oversiktlighet» (safety, calm and overview), in the Author's own words on 2026-11-05.
- **Overview first:** on 2026-11-09 the Author made oversiktlighet the most important quality («Det viktigste er at det er oversiktlig»). The Author also reopened the visual direction by asking for ten widely varied design concepts before going into detail.
- **The earlier look is a candidate:** the 2026-11-05 look (light colours, one calm blue accent, apple.com as the Author's reference) is one candidate among the new concepts, not a commitment. Open: whether the 2026-11-05 wish for light colours still holds.
- **Themes:** a light and a dark theme are both required (the Author, 2026-11-05).
- **Language:** buttons, messages and the privacy notice are in Norwegian bokmål, whatever the language of the Study material (NFR-6, confirmed by the Author on 2026-11-01). On 2026-11-05 the Author confirmed the names fag, tema, mestring, «Trenger øving» and demomodus, and the ratings «Igjen», «Vanskelig», «Bra» and «Lett».
- **Voice** (the final 2026-11-05 UX spine): speak to the Student as «du». Be calm and plain: say what happened, then what to do next. Use no exclamation marks, emojis or inflated praise. A Weak topic means "practice this", never failure.

## Evidence on Hand

- Planning documents in `_bmad-output/planning-artifacts/`:
  - the product brief and addendum (`briefs/brief-Prosjekt A-2026-09-15/`)
  - the PRD and addendum (`prds/prd-Prosjekt A-2026-10-29/`)
  - the technical research on LLM choice and PDF extraction (`research/technical-llm-choice-and-pdf-extraction-for-ai-stu-2026-10-28/`)
  - the 2026-11-05 UX spines with four key-screen mocks (`ux-designs/ux-Prosjekt A-2026-11-05/`)
- The teacher's feedback on the brief: `tilbakemelding-product-brief.md`.
- Absent, and not to be fabricated:
  - application code, or screenshots of a running app
  - the Sample document and its recorded responses
  - a logo or other brand assets beyond the name
  - usage data, users other than the Author, testimonials or metrics

## Product Principles

Derived from the sources cited; the selection and wording are (inferred).

1. **Every Answer decides what comes next.** Testing feeds repetition: missed Questions return, Flashcards come back by how well they were remembered, and Topic scores point to what needs work (PRD §1).
2. **Show where everything comes from.** Each Generated item carries a checked Reference. What fails the check is removed and counted, not shown with a warning (FR-8, confirmed on 2026-11-01).
3. **Overview before anything else.** On any screen the Student can tell where they are, what to practice next and how far they have come (the Author's priority on 2026-11-09; the three questions are drawn from the brief and the PRD).
4. **Calm and safe, never surprising.** The Student sets the pace, nothing is deleted without asking, and the app says what happened and what to do next (the Author's feel from 2026-11-05; the final UX spine).
5. **It runs for anyone without a key, and says so.** Mock mode is the default and always visible, so the Examiner can try every core function from the README (FR-20, NFR-2).

## Accessibility & Inclusion

- WCAG 2.2 AA, set in the 2026-11-05 UX spine; the PRD names no standard.
- Works from 360 px wide in the latest Chrome, Safari and Firefox on desktop and phone, without horizontal scrolling (NFR-1). The UX spine also requires reflow down to 320 px, with text enlarged to 200 %.
- Grades, statuses and Weak topics are said in words with an icon, never by colour alone. Everything works by keyboard with a visible focus ring, touch targets are at least 44 px, and reduced motion is respected.
- Pages are marked as Norwegian (`lang="nb"`). Each Source's Study material carries its own language, so screen readers pronounce it correctly (FR-6).
- In Exam mode the Student sets the time limit (WCAG 2.2.1).
- The app is subject-agnostic, for students in any field.
