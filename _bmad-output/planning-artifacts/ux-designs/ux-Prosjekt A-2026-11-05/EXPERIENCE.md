---
name: AI Study Buddy
status: final
sources:
  - '{planning_artifacts}/prds/prd-Prosjekt A-2026-10-29/prd.md'
  - '{planning_artifacts}/prds/prd-Prosjekt A-2026-10-29/addendum.md'
  - '{planning_artifacts}/briefs/brief-Prosjekt A-2026-09-15/brief.md'
  - '{project-root}/tilbakemelding-product-brief.md'
updated: 2026-11-05
---

# AI Study Buddy — Experience Spine

## Foundation

- **Form factor:** a responsive web app in the browser (PRD NFR-1). Laptop and desktop carry uploading and Quizzes, the phone carries Reviews (UJ-2), and the tablet sits in between. It works from 360 px wide in the latest Chrome, Safari and Firefox. There are no native apps (PRD §6).
- **UI system:** none chosen yet; architecture picks it. The tokens in DESIGN.md are library-agnostic, and this spine specifies behavior whichever library is chosen. `[ASSUMPTION]`
- **Visual identity:** DESIGN.md is the reference; this spine is the experience.
- **Language:** the interface is in Norwegian bokmål (PRD NFR-6). Study material appears in the language of its Source (PRD FR-6).
- **Themes:** light and dark. The app follows the device setting, and the Student can override it in the account menu. `[ASSUMPTION: the override]`
- **Terms:** exactly as in the PRD Glossary. Voice and Tone gives the Norwegian label for each.
- **Modes:** Mock mode and Real mode (PRD FR-20, FR-21) behave the same, except where State Patterns says otherwise.

## Information Architecture

| Surface | Reached from | Purpose | PRD |
|---|---|---|---|
| Sign in / Create account | Opening the app while signed out | Email and password; no «Glemt passordet?» link (PRD §6) | FR-1 |
| Home | Opening the app while signed in; the app name in the top-bar | The due-today-panel, the Courses as course-cards, and «Nytt fag» | FR-2, FR-15 |
| Course overview | A course-card | The Topics with their Topic scores and Weak topics first; start a Practice-mode Quiz on Weak topics or an Exam-mode Quiz; «Nytt tema» | FR-2, FR-16, FR-17, FR-18 |
| Topic | A topic-row | The Study material grouped by Source, each Source with its status; start a Practice-mode Quiz; browse Flashcards; «Legg til kilde» | FR-3, FR-9, FR-19, FR-23, FR-24 |
| Add Source (dialog) | «Legg til kilde» in a Topic | Upload a file or paste text, and choose the Detail level. The privacy notice comes first the first time in Real mode | FR-3, FR-5, FR-22 |
| Quiz | The Topic; the Course overview (Weak topics); Exam setup | One Question at a time | FR-10, FR-11, FR-12, FR-18 |
| Quiz result | The end of a Quiz | The score, the Grade of every Answer, and the Retry round | FR-13 |
| Flashcards | «Bla i kort» in a Topic | Flip through the Topic's Flashcards | FR-14 |
| Review | The due-today-panel; «I dag» in the top-bar | Rate the Due cards, then see the end summary | FR-15 |
| Exam setup (dialog, Should) | «Prøveeksamen» in the Course overview | Choose Topics, the number of Questions and the time limit | FR-18 |
| Account menu | The top-bar | Theme, and «Logg ut» | FR-1 |

Navigation rules:

- **top-bar:** on every signed-in surface except sessions. It holds the app name (to Home), «I dag» with the Due-card count (to Review), and the account menu.
- **Hierarchy:** Home › Course overview › Topic. From 600 px there is a breadcrumb; below 600 px, a back link to the parent.
- **Sessions:** Quiz, Quiz result, Flashcards and Review replace the top-bar with a session-header that has an exit. The exit returns to the surface the session started from.
- **Dialogs:** one level deep, never stacked.
- **No bottom tab bar:** on the phone only Home and Review matter, and the top-bar reaches both.

Key-screen mocks show four surfaces, each in a desktop frame with the light theme and a phone frame with the dark theme. The spines win on any conflict with a mock.

- [`mockups/key-home.html`](mockups/key-home.html): Home, with the top-bar, the due-today-panel and course-cards (UJ-2, step 1).
- [`mockups/key-course-overview.html`](mockups/key-course-overview.html): Course overview, with the breadcrumb, topic-rows, score-meters and status-badges (UJ-3, steps 1 and 2).
- [`mockups/key-topic.html`](mockups/key-topic.html): Topic with Study material, with source-rows, a summary-block and key-concept-items, one of them showing its Simpler explanation (UJ-1, steps 5 and 6; UJ-4).
- [`mockups/key-quiz.html`](mockups/key-quiz.html): a Practice-mode Quiz after an incorrect Answer, with the session-header, question-card, option-rows, feedback-panel and reference (UJ-1, step 8).

The other surfaces are built from the tables in these spines alone.

**Surface closure:** every PRD capability has a surface in the table, and every surface appears in a Key Flow, with two exceptions:
- **Flashcards** is reached from the Topic (FR-14), not in a journey.
- **Account menu** serves sign-out (FR-1) and the Author's choice of both themes.

## Voice and Tone

Microcopy, in Norwegian bokmål. The brand voice lives in DESIGN.md, Brand & Style.

- Speak to the Student as «du».
- Be calm and plain: say what happened, then what to do next.
- No exclamation marks, no emojis, no inflated praise.
- Write numbers as digits and dates as «12. november». Use sentence case; the app's own nouns (fag, tema, kort) stay lowercase in running text.

| Do | Don't |
|---|---|
| «7 av 10 riktige. Øv på de 3 du ikke fikk til.» | «Supert jobba! 🎉» |
| «Dette temaet trenger mer øving.» | «Svakt tema!» or «Du er dårlig på dette.» |
| «2 elementer ble fjernet fordi kildehenvisningen ikke stemte.» | «Referansefeil (kode 422)» |
| «Filen har 70 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.» | «Ugyldig fil.» |
| «Lager studiemateriell … Du kan gå fra siden imens.» | «Vennligst vent …» |
| «Kunne ikke rette svaret fordi KI-tjenesten ikke svarte. Prøv igjen.» | «Noe gikk galt.» |

Labels for Glossary terms:

| Glossary term | Label in the interface |
|---|---|
| Course / Topic / Source | fag / tema / kilde |
| Course overview | The Course's own name as the screen title |
| Study material / Summary / Key concept | studiemateriell / sammendrag / nøkkelbegrep |
| Detail level | detaljnivå: «Kortfattet», «Middels», «Detaljert» («kort» is taken by Flashcards) |
| Simpler explanation | «Forklar enklere» (the action), «Enklere forklaring» (the heading) |
| Flashcard / Review / Due today | kort / repetisjon / «I dag» |
| Question, with Multiple-choice question and Free-text question | spørsmål, with the type labels «Flervalg» and «Fritekst» |
| Hint / Quiz / Answer / Explanation | hint / quiz / svar / forklaring |
| Practice mode / Exam mode | øving / prøveeksamen |
| Grade: correct, partially correct, incorrect, not graded | «Riktig», «Delvis riktig», «Feil», «Ikke rettet» |
| Retry round | «Øv på feilene» |
| Topic score / Weak topic | mestring («Mestring 45 %») / «Trenger øving» |
| Reference | «Side 14» for PDF, the heading for Word, «Avsnitt 3» for plain text, followed by the quote |
| Generated item | element (only in counts) |
| Sample document / Mock mode | eksempeldokumentet / demomodus |
| AI provider / Key | KI-tjenesten / API-nøkkel |
| The ratings Again, Hard, Good, Easy | «Igjen», «Vanskelig», «Bra», «Lett» |

## Component Patterns

Behavioral rules only; the visual specs live in DESIGN.md, Components.

| Component | Use | Behavioral rules |
|---|---|---|
| top-bar | Every signed-in surface except sessions | The app name goes to Home. «I dag» opens Review and shows the Due-card count when the count is above 0. The account menu holds the theme (System, Lys, Mørk) and «Logg ut». |
| mode-banner | Under the top-bar, and on Sign in, whenever Mock mode is on | One line: «Demomodus: appen bruker innspilte svar for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.» It cannot be closed, because FR-20 requires the app to show its mode. |
| breadcrumb | Course overview and Topic, from 600 px | Every level except the current one is a link. Below 600 px it is replaced by a back link to the parent («‹ Databases»). |
| button | Everywhere | At most one `button-primary` per region: the next step. `button-destructive` appears only inside a confirm dialog. A button is never disabled without a visible reason next to it. While an action runs, the button keeps its label, shows a spinner and ignores further presses. |
| text-input | Sign in, Create account, Course and Topic names, pasted text | The label is above the field and always visible. Errors appear below the field in words and are linked to it. Enter submits the form. |
| segmented-control | Detail level in Add Source and in the summary-block; theme in the account menu; presets in Exam setup | Exactly one option is selected. Changing the Detail level of an existing Summary regenerates only the Summary (FR-7), with no confirm. |
| card | Containers on Home, in the Topic and in the result | A static container. Only course-card is clickable as a whole. |
| course-card | Home | The whole card opens the Course overview. It shows the Course name, the optional course code, the number of Topics, the Due-card count, and the Weak-topic count («2 temaer trenger øving»). Colors `course-1` to `course-6` are assigned in order of creation and repeat after six. A «⋯» menu offers rename and delete; delete opens a confirm dialog. `[ASSUMPTION: automatic colors]` |
| topic-row | Course overview | The whole row opens the Topic. It shows the Topic name, a score-meter, a «Trenger øving» status-badge for a Weak topic, and the number of Sources. A «⋯» menu offers rename and delete; delete opens a confirm dialog (FR-2). Weak topics come first, lowest Topic score first (FR-17); the other Topics follow in order of creation. `[ASSUMPTION: the order of the rest]` |
| score-meter | topic-row, Topic header, result-summary | Shows the Topic score as a bar and as text («Mestring 45 %»). In the Topic it adds «Basert på de 20 siste svarene dine.» It updates when a Quiz ends. States: see State Patterns. |
| status-badge | source-row, topic-row, feedback-panel | Always text, with color as support. The states are generating, ready and failed for a Source; «Trenger øving» for a Weak topic; and «Demo» next to a mock Grade (FR-12). |
| due-today-panel | The top of Home | Shows the number of Due cards from all Courses, plus a count per Course with its color, and «Start repetisjon». States: see State Patterns. |
| source-row | Topic, as the header of each Source's section | Shows the name, the type, the page count, the Detail level and the status. Sources are listed newest first. `[ASSUMPTION]` The status updates without a reload and is announced politely. A «⋯» menu offers rename and delete; delete opens a confirm dialog (FR-2). States: see State Patterns. |
| upload-panel | The Add Source dialog | Offers a drop zone from 600 px, «Velg fil», and a «Lim inn tekst» option. The limits are shown up front («PDF eller tekstfil · maks 50 sider eller 10 MB»). Size, type and length are checked before upload (FR-3). Detail level defaults to «Middels» `[ASSUMPTION]`. In Mock mode the panel offers «Bruk eksempeldokumentet», which uploads the Sample document in one step. Word files are accepted when FR-5 ships. States: see State Patterns. |
| dialog | Add Source, Exam setup, «Nytt fag», «Nytt tema», rename, confirm delete, the privacy notice | Opens over the current surface. «Nytt fag» asks for a name and an optional course code; «Nytt tema» and rename ask for a name only (FR-2). «Avbryt» and Esc close it. A confirm-delete dialog names what goes and everything under it: «Slette faget Databases? 4 temaer, 9 kilder og alle svar slettes. Dette kan ikke angres.» Its destructive button repeats the verb («Slett faget»). The privacy-notice variant shows the notice in FR-22 once per Student, before the first upload in Real mode. The buttons are «Jeg forstår, fortsett» and «Avbryt»; Esc counts as «Avbryt», and then nothing is uploaded. |
| summary-block | Each Source's section in the Topic | Shows the full Summary at reading width, not truncated. Its header carries the Detail level control (FR-7). A Summary has no Reference in v1, so none is shown. |
| key-concept-item | Each Source's section in the Topic | Shows the term, the definition and the Location («Side 14», FR-23). «Vis kilde» opens the reference. «Forklar enklere» (Should, FR-19) opens the Simpler explanation in a panel below. Once saved, it shows instantly next time, with «Lag ny» to replace it. The «⋯» menu offers «Slett», which opens a confirm dialog (FR-24). `[ASSUMPTION: the quote opens on demand]` |
| reference | feedback-panel, the back of a flashcard, key-concept-item | The Location comes first, then the verbatim quote in the Source's language. It is never a link that leaves the app. |
| session-header | Quiz, Review, Flashcards | **Left:** «Avslutt», which leaves at once, since Answers and ratings are already saved (FR-10). **Middle:** the progress («3 av 10»). **Right, in Exam mode:** the time left, always visible (FR-18). There the exit is «Lever», with a confirm dialog that names how many Questions are unanswered. |
| question-card | Quiz | One Question per screen, with its type label. In Practice mode, «Vis hint» shows the Hint inline (FR-7). Exam mode has no Hint (FR-18). |
| option-row | Quiz, for Multiple-choice questions | There are four options, A to D (FR-7), and clicking or pressing 1 to 4 selects one. «Svar» submits. In Practice mode the options then lock, and the chosen and correct options are marked in words and icons, with the feedback-panel below. In Exam mode, selecting is all that happens until submission. |
| free-text-answer | Quiz, for Free-text questions | «Svar» submits. After grading, «Vis fasit» shows the model answer. States: see State Patterns. |
| feedback-panel | Quiz in Practice mode; the Question rows in the Quiz result | Shows the Grade in words with an icon, the Explanation and the reference. For an incorrect Multiple-choice Answer it adds the correct option and why the chosen one is wrong (FR-11). Its actions are «Neste spørsmål» and «Slett spørsmålet» (FR-24, with a confirm dialog). |
| result-summary | Quiz result | Shows the score («7 av 10»), and in Exam mode the score per Topic (FR-18). Each Question appears with its Grade and opens its feedback-panel. «Øv på feilene (3)» starts the Retry round (FR-13). «Tilbake» returns to where the Quiz started. States: see State Patterns. |
| flashcard | Flashcards, Review | The front shows first. A click, a tap or Space flips it to the back, which shows the answer and the reference (FR-14). In Flashcards, ← and → move between cards and the position shows («4 av 22»). The «⋯» menu offers «Forklar enklere» (Should, FR-19) and «Slett kortet» (FR-24, with a confirm dialog). |
| rating-bar | Review, after the flashcard is flipped | Appears only once the card is flipped. «Igjen», «Vanskelig», «Bra» and «Lett» (keys 1 to 4) save the rating at once and show the next card. A card rated «Igjen» returns later in the same Review (FR-15). There is no undo in v1. `[ASSUMPTION]` |
| topic-picker | Course overview, for Weak topics; Exam setup | A checkbox list of the Course's Topics with their Topic scores. Weak topics are preselected when it is opened from «Øv på svake temaer». The start button shows how many Questions are available. |
| empty-state | Home, Course overview, Topic, Review, Flashcards | A heading, one sentence and one primary action, for example «Ingen fag ennå» / «Lag ett fag for hvert emne du tar, og legg temaer inn under det.» / «Nytt fag». |
| inline-message | Where a problem happens: upload, generation, grading, network, the Key | Appears in place, not as a toast. It says what happened and what to do, and it stays until the problem is solved or dismissed. It is announced politely, or assertively when it blocks the current action. |
| skeleton | First load of Home, Course overview and Topic | Shown only if loading takes more than 300 ms, so it never flickers. Its shapes match the final layout, and it is replaced in place. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Signed out | Any | Sign in. After signing in, the Student returns to the surface they asked for. `[ASSUMPTION]` |
| Sign-up closed | Sign in, on the Hosted instance (FR-25) | «Opprett konto» is hidden. A direct visit to sign-up shows «Registrering er stengt på denne installasjonen.» |
| First load | Home, Course overview, Topic | A skeleton, replaced in place. |
| No Courses | Home | An empty-state («Ingen fag ennå», «Nytt fag»). The due-today-panel is hidden. |
| No Topics | Course overview | An empty-state («Ingen temaer ennå», «Nytt tema»). |
| No Sources | Topic | An empty-state («Ingen kilder ennå», «Legg til kilde»). Quiz and Flashcard actions are hidden. |
| No Flashcards yet | Home | The due-today-panel is hidden. |
| Generating | Topic | The source-row shows that it is generating, with «Vanligvis under 2 minutter. Du kan gå fra siden imens.» (NFR-3). That Source's Questions and Flashcards are not used until it is ready; other Sources work as normal. On return, the current status shows (FR-9). |
| Items removed by the Reference check | Topic | The source-row reads «Klar · 2 elementer fjernet». Clicking the count opens an inline-message that explains the check (FR-8). |
| Generation failed | Topic | The source-row shows failed, with an inline-message saying what failed and «Prøv igjen», which retries without a new upload. Nothing from the failed attempt is shown (FR-9). |
| Upload rejected | Add Source | An inline-message in the upload-panel gives the reason and the limit: pages, megabytes, characters, a scanned PDF or the file type (FR-3). Nothing is uploaded. |
| Privacy notice declined | Add Source | The dialog closes and nothing is uploaded. The notice shows again at the next upload (FR-22). |
| Mock mode | All | The mode-banner (FR-20). |
| Mock mode, another file | Topic | The file is stored, and an inline-message says: «I demomodus lages studiemateriell bare for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.» (FR-20) |
| Key rejected | Topic, Quiz | An inline-message: «KI-tjenesten godtok ikke API-nøkkelen. Sjekk nøkkelen i .env og start appen på nytt.» Existing Study material keeps working (FR-21). |
| Few Questions | Topic | A Quiz cannot hold more Questions than are available (FR-10). With none ready, «Start quiz» is hidden. |
| Grading | Quiz, Free-text questions | «Retter svaret …» shows where the feedback will appear, and the field is locked. Grading takes at most 15 seconds (NFR-3). |
| Not graded | Quiz, Quiz result | The feedback-panel reads «Ikke rettet», with «Prøv igjen» (FR-12); in the Quiz result the Answer is listed with «Prøv å rette igjen». The Question stays out of the Retry round until it is graded (FR-13). |
| Mock Grade | Quiz | A «Demo» status-badge next to the Grade (FR-12). |
| Quiz left mid-way | Quiz | «Avslutt» leaves at once. The Answers given so far are saved and count (FR-10). |
| Time running out | Quiz, Exam mode | The timer is announced once at 5 minutes and once at 1 minute. At 0 the Answers are submitted and the Quiz result opens (FR-18). |
| Exam left mid-way | Quiz, Exam mode | The clock keeps running. Returning before time is up resumes the exam; after that, the Answers given so far are submitted. |
| All correct | Quiz result | «Øv på feilene» is hidden, and the text reads «Alle svarene var riktige.» |
| Too few Answers | Course overview, Topic | With fewer than 5 graded Answers, the score-meter shows «Ikke nok data ennå» and no bar, and the Topic is not a Weak topic (FR-16). |
| Nothing due | Home, Review | The due-today-panel reads «Ingen kort i dag. Neste kort kommer {dato}.»; Review shows an empty-state. |
| Daily limit on new cards reached | The end of Review | «I dag fikk du 20 nye kort. Flere kommer i morgen.» (FR-15) |
| Network lost | Where an action failed | An inline-message with «Prøv igjen». An Answer or rating does not count until it is saved. There is no offline mode (PRD §6). |
| Not found, or another Student's data | Any | «Fant ikke siden», with a link to Home. Nothing about the data is shown (FR-1). |
| Item deleted | Topic, Flashcards, Quiz | After the confirm dialog, the item disappears and the counts update. There is no success message. `[ASSUMPTION]` |

## Interaction Primitives

- **Pointer:** click or tap to act. The course-card and the topic-row are clickable as a whole.
- **Keyboard:**
  - Tab follows the reading order, Enter submits, and Esc closes the top dialog.
  - In a Quiz, 1 to 4 pick an option, Enter answers, and Enter again moves on.
  - In Review and Flashcards, Space flips the card. In Review, 1 to 4 rate it; in Flashcards, ← and → move between cards.
  - From 1024 px, the keys are hinted next to the controls. `[ASSUMPTION]`
- **Gestures:** none is ever the only way to do something. There is no swipe in v1. `[ASSUMPTION]`
- **Pace:** the Student sets it. The app never moves on to the next Question or card by itself, except when the time runs out in Exam mode.
- **Saving:** Answers and ratings are saved the moment they are given (FR-10). Only forms have save buttons.
- **Background work:** generation never blocks the Student, who can move around while it runs (FR-9).
- **Destructive actions:** a confirm dialog comes first (FR-2, FR-24). There is no undo in v1.
- **Motion:** panels and dialogs take 150 to 250 ms with an ease-out curve, and the flashcard flip takes 300 ms. Nothing animates when a page loads. With reduced motion on, flips and slides become instant changes.
- **Banned:**
  - confetti, streaks, points and sounds
  - moving on by itself in Practice mode
  - toasts for routine events
  - stacked dialogs
  - actions that only appear on hover
  - infinite scrolling

## Accessibility Floor

Behavioral rules; visual contrast lives in DESIGN.md, Colors.

- **Standard:** WCAG 2.2 AA.
- **Not by color alone:** Grades, statuses and Weak topics are always written in words, with an icon.
- **Keyboard:** everything works by keyboard, and the focus ring is always visible.
- **Page titles:** each surface has its own title, for example «Normalization – Databases – AI Study Buddy».
- **Announcements:**
  - The feedback-panel, source-row status changes and Review progress are announced politely.
  - Errors that block the current action are announced assertively.
  - The Exam-mode timer is announced only at 5 minutes and at 1 minute.
- **Focus:**
  - A dialog keeps focus inside, starts on its title, and returns focus to its trigger.
  - After an Answer, focus moves to the feedback-panel heading. After «Neste spørsmål», it moves to the next Question.
- **Language:** the page is marked as Norwegian (`lang="nb"`). Each Source's Study material is marked with the Source's language, so screen readers pronounce it correctly (FR-6).
- **Touch targets:** at least 44 px, with 8 px between the rating-bar buttons.
- **Zoom and reflow:** text can be enlarged to 200 %. The layout reflows down to 320 px without horizontal scrolling (WCAG 1.4.10), a stricter requirement than the PRD's 360 px.
- **Time limit:** the Student sets Exam mode's time limit (FR-18), which meets WCAG 2.2.1.
- **Forms:** labels are visible, and errors are in words and linked to their field.

## Responsive & Platform

Breakpoints `[ASSUMPTION]`: `sm` below 600 px (phone), `md` from 600 to 1023 px (tablet) and `lg` from 1024 px (laptop and desktop).

| Surface | `sm` | `md` | `lg` |
|---|---|---|---|
| Home | The due-today-panel on top, course-cards in one column | Two columns | Three columns |
| Course overview | One list, with the actions under the title | Same as `sm` | The actions to the right of the title |
| Topic | One column: the actions, then each Source's section | Same as `sm` | Study material on the left; a sticky side column with the Topic score and the actions `[ASSUMPTION]` |
| Quiz, Review, Flashcards | Full width; the main action («Svar», «Neste spørsmål» or the rating-bar) stays at the bottom edge, within thumb reach | Centered at reading width | Centered at reading width |
| dialog | A full-width sheet from the bottom | Centered | Centered |
| upload-panel | «Velg fil» only | Drop zone and «Velg fil» | Drop zone and «Velg fil» |

Using the phone away from home needs the Hosted instance (FR-25, Should). The interface is the same.

## Inspiration & Anti-patterns

- **Lifted from Apple's website, the Author's reference:**
  - whitespace as the main way to group
  - one large, plain heading per screen
  - neutral light surfaces and one quiet accent
  - restrained motion
- **Not lifted:** hero images at marketing scale, animation driven by scrolling, and Apple's own colors and typefaces. The system font gives a native look on each device without copying a brand.
- **Rejected** `[ASSUMPTION: inferred from «ro» and «trygghet»]`, besides the bans in Interaction Primitives and in DESIGN.md, Do's and Don'ts:
  - dense dashboards full of charts
  - a chat interface (PRD §6)
  - endless feeds

## Key Flows

### UJ-1. Ida turns Monday's lecture into a quiz the same evening

1. Signed in on her laptop, Ida opens Home and clicks the course-card «Databases».
2. In the Course overview she clicks «Nytt tema» and names it «Normalization». The new Topic opens with its empty-state.
3. She clicks «Legg til kilde». Since this is her first upload in Real mode, the privacy notice explains where the text goes. She clicks «Jeg forstår, fortsett».
4. In the upload-panel she drops the 32-page PDF, keeps «Middels» and clicks «Last opp».
5. The source-row shows «Lager studiemateriell …». Ida could leave the page now.
6. The status turns «Klar». The Summary and the Key concepts appear under the Source, and «Bla i kort (22)» becomes available.
7. She clicks «Start quiz» and keeps 10 Questions. On the third, she clicks «Vis hint».
8. She answers a Multiple-choice question incorrectly. The feedback-panel shows «Feil», the correct option, why hers is wrong, and «Side 14» with the quoted sentence.
9. **Climax:** the result-summary reads «7 av 10 riktige». She clicks «Øv på feilene (3)», and the three Questions she missed are back in front of her. The evening's lecture has become practice, not reading.

**Failure:**
- The 70-page compendium is rejected in the upload-panel before anything is uploaded: «Filen har 70 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.»
- If generation fails, the source-row says what failed and offers «Prøv igjen» without a new upload.

### UJ-2. Ida clears Due today on the bus

1. On her phone, Ida opens the app on the Hosted instance (FR-25). The due-today-panel reads «14 kort i dag», with counts from two Courses.
2. She taps «Start repetisjon». The Review opens with a session-header showing «1 av 14».
3. She reads the front and taps to flip. The back shows the answer and the reference.
4. The rating-bar appears. She taps «Bra», and the next card shows.
5. A card she rates «Igjen» comes back before the end.
6. **Climax:** «Du repeterte 14 kort. Neste kort kommer i morgen.» Due today is empty, and she knows when to come back.

**Failure:** if the connection drops mid-Review, an inline-message says the rating was not saved and offers «Prøv igjen». The card stays until the rating is saved.

### UJ-3. Two weeks before the exam, Ida drills Weak topics and sits a mock exam

1. Ida opens the Course overview for «Databases». At the top, two topic-rows are marked «Trenger øving»: «Normalization» at 45 % and «Transactions» at 55 %.
2. She clicks «Øv på svake temaer». The topic-picker has both preselected, and she starts a Practice-mode Quiz.
3. Later she clicks «Prøveeksamen» (Should). In Exam setup she chooses the whole Course, 20 Questions and 30 minutes.
4. The Exam-mode Quiz runs without Hints or feedback. The session-header always shows the time left.
5. She clicks «Lever» and confirms. If the time runs out first, her Answers are submitted for her.
6. **Climax:** the result-summary shows her score per Topic. Back in the Course overview, the score-meters have moved, and she can see where she stands.

**Failure:** she closes the tab mid-exam. If she reopens it before the time is up, the exam resumes; after that, her Answers so far are submitted.

### UJ-4. Ida gets a Simpler explanation of a Key concept that does not click (Should)

1. In the Topic «Normalization», Ida reads the key-concept-item «third normal form», which is in the language of the slides.
2. She clicks «Forklar enklere».
3. The panel opens under the definition, first with a loading line, then with at most three sentences in the language of the slides. It also names the page the explanation is based on.
4. **Climax:** the concept clicks. The explanation is saved, so «Forklar enklere» shows it at once next time, with «Lag ny» if she wants another.

**Failure:** if the AI provider fails, an inline-message inside the panel offers «Prøv igjen».

### UJ-5. Jonas runs the app from the README without a Key

1. Jonas starts the app as the README describes. Sign in shows the mode-banner for Mock mode.
2. He creates an account. Home shows «Ingen fag ennå».
3. He creates a Course and a Topic, opens Add Source and clicks «Bruk eksempeldokumentet».
4. The Study material appears. The source-row reads «Klar · 1 element fjernet»: the Reference check caught the one wrong page in the recorded responses (FR-8).
5. He takes a Quiz. His Free-text Answer gets a Grade marked «Demo».
6. He takes the Retry round and then does a Review.
7. **Climax:** every core function has worked without a Key. The removed item even shows him the Reference check at work.

**Failure:** when he uploads another PDF, it is stored, and an inline-message explains that Mock mode only generates Study material for the Sample document.
