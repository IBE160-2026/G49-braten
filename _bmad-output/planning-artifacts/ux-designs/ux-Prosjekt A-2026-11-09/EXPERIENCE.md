---
name: AI Study Buddy
status: final
sources:
  - '{planning_artifacts}/prds/prd-Prosjekt A-2026-10-29/prd.md'
  - '{planning_artifacts}/prds/prd-Prosjekt A-2026-10-29/addendum.md'
  - '{planning_artifacts}/briefs/brief-Prosjekt A-2026-09-15/brief.md'
  - '{project-root}/tilbakemelding-product-brief.md'
  - '{planning_artifacts}/ux-designs/ux-Prosjekt A-2026-11-05/DESIGN.md'
  - '{planning_artifacts}/ux-designs/ux-Prosjekt A-2026-11-05/EXPERIENCE.md'
  - '{planning_artifacts}/ux-designs/ux-Prosjekt A-2026-11-09/mockups/14-fagskinnen.html'
updated: 2026-11-13
---

# AI Study Buddy — Experience Spine

This spine builds on the 2026-11-05 spine. Its priorities are every fag in view, one next step per screen, and an adult look. The decision history is in `.memlog.md`.

On 2026-11-13 it was brought in line with the PRD as updated after the teacher's feedback. That update covers the following, and the spine now follows the PRD on each point:

- generation while the Student waits (FR-9), with background generation as Should (FR-26);
- the rate-limit and daily-limit messages (FR-9, NFR-7);
- the Grade override (FR-12);
- the Course score (FR-16);
- the quiz history (FR-27);
- the Next step (FR-28).

## Foundation

- **Form factor:** a responsive web app in the browser (PRD NFR-1). The laptop and desktop carry uploading and Quizzes, the phone carries Reviews (UJ-2), and the tablet sits in between. It works from 360 px wide in the latest Chrome, Safari and Firefox. There are no native apps (PRD §6).
- **UI system:** none chosen yet; architecture picks it. The DESIGN.md tokens are library-agnostic, and this spine specifies behavior whatever library is chosen. `[ASSUMPTION]`
- **Visual identity:** DESIGN.md is the reference: a petrol shell with the fag-rail, a white workspace, one copper accent, and Public Sans. This spine is the experience.
- **Audience and posture:** adult students, from 20 years and up. The product behaves like a work tool, not a game. There is no gamification of any kind (see Interaction Primitives, Banned).
- **Language:** the interface is in Norwegian bokmål (PRD NFR-6). Study material appears in the language of its Source (PRD FR-6).
- **Themes:** light and dark, both complete. The app follows the device setting, and the Student can override it in the account menu. `[ASSUMPTION: the override]`
- **Terms:** exactly as in the PRD Glossary. Voice and Tone gives the Norwegian label for each.
- **Modes:** Mock mode and Real mode (PRD FR-20, FR-21) behave the same, except where State Patterns says otherwise.
- **The three questions every signed-in page answers without hunting:**
  - *Where am I?* The fag-rail's current-item mark, then the breadcrumb, then the one page title.
  - *What do I do next?* One next-step-band.
  - *How far have I come?* Mastery, trend, the forecast and session progress.

## Information Architecture

| Surface | Mock ID | Reached from | Purpose | PRD |
|---|---|---|---|---|
| Logg inn | P01 | Opening the app while signed out | Email and password; no «Glemt passordet?» (PRD §6) | FR-1, FR-20, FR-25 |
| Opprett konto | P02 | «Opprett konto» on P01 (hidden when sign-up is closed) | Email and password | FR-1, FR-25 |
| Hjem | P03 | Signing in; the app name; «Hjem» in the fag-rail; «Hjem · alle fag» in the fag-switcher | The next-step-band, then «Studievarsel for fagene dine»: the forecast-chart for all fag and one fag-forecast-row per fag | FR-2, FR-15, FR-16, FR-17, FR-28 |
| Fagoversikt (titled with the fag's name) | P04 | A fag-rail-row; a fag-forecast-row; the fag-switcher list; the breadcrumb | The fag's mastery under the title with the line that explains it, the band (by the priority rule in Next step), «Øv på svake temaer (N)», «Prøveeksamen», «Nytt tema», a mini forecast for the fag, and the tema-forecast-rows | FR-2, FR-16, FR-17, FR-18, FR-28 |
| Tema (titled with the tema's name) | P05 | A tema-forecast-row; the breadcrumb; a tema name in P11 | The band (quiz, or the first kilde), then four tema-tabs: «Sammendrag» (default), «Quiz», «Test deg selv» and «Kilder»; beside them the tema-forecast-panel «Varsel for temaet» | FR-3, FR-6 to FR-9, FR-14, FR-15, FR-19, FR-23, FR-24, FR-26, FR-27, NFR-7 |
| Quiz | P06 | D06 (the band on P05, or «Velg antall og start» in its «Quiz» tab); D10; «Øv på feilene» on P07 and P11 and on the newest row of the quiz-history | One Question at a time, in Practice mode; a Free-text Grade can be overridden | FR-10, FR-11, FR-12 |
| Resultat | P07 | The end of a Quiz; «Se resultatet» in the quiz-history | The score, every Grade (a Free-text Grade can be overridden), and the band for «Øv på feilene» | FR-12, FR-13, FR-27 |
| Bla i kort | P08 | «Bla i alle kort» in the «Test deg selv» tab on P05 | Flip through the tema's Flashcards in the order they were made; browsing changes no review dates | FR-14 |
| Repetisjon | P09 | The band on Hjem or Fagoversikt; «I dag · 14» in the fag-rail or top-bar; «Repeter dagens kort (N)» in the «Test deg selv» tab (this tema's Due cards only) | Rate the Due cards, see where each card returns, then the end summary | FR-15, FR-23 |
| Prøveeksamen (Should) | P10 | D11 | An Exam-mode Quiz with a running clock | FR-18 |
| Resultat for prøveeksamen (Should) | P11 | «Lever» (D12), or the time running out | The score, the score and new mastery per tema, and the band for «Øv på feilene»; a Free-text Grade can be overridden | FR-12, FR-13, FR-16, FR-18 |
| Fant ikke siden | P12 | An unknown address or another Student's data | «Fant ikke siden», «Til Hjem» | FR-1 |
| Kontomeny | D01 | The account at the foot of the fag-rail; the avatar in the top-bar | «Utseende» (System, Lys, Mørk) and «Logg ut» | FR-1 |
| Nytt fag | D02 | «Nytt fag» in the fag-rail, the fag-switcher list, or the Hjem empty-state | Name and an optional course code | FR-2 |
| Nytt tema | D03 | «Nytt tema» on P04 | Name | FR-2 |
| Før du laster opp | D04 | The first «Legg til kilde» in Real mode | The privacy notice | FR-22 |
| Legg til kilde | D05 | «Legg til kilde» on P05, or the band when the tema has no kilder | The upload-panel and the Detail level; the daily-limit message when the limit is reached | FR-3, FR-5, FR-20, NFR-7 |
| Start quiz | D06 | The band on P05 | The number of Questions | FR-10 |
| «⋯» menu | D07 | fag-forecast-row, tema-forecast-row, source-row, key-concept-item, flashcard | «Gi nytt navn», «Slett», «Forklar enklere» on a card | FR-2, FR-19, FR-24 |
| Gi nytt navn | D08 | D07 | Name, prefilled | FR-2 |
| Confirm delete | D09 | «Slett» in D07; «Slett spørsmålet» in the feedback-panel | Names what goes; cannot be undone | FR-2, FR-24 |
| Øv på svake temaer | D10 | «Øv på svake temaer (N)» on P04; the band on P04 or Hjem when no cards are due | The topic-picker with the Weak topics preselected | FR-17 |
| Prøveeksamen: oppsett (Should) | D11 | «Prøveeksamen» on P04 (several tema); «Sett opp prøveeksamen» in the «Test deg selv» tab on P05 (this tema preselected) | Tema, the number of Questions, the time limit | FR-18 |
| Levere nå? | D12 | «Lever» in P10 | Lists the unanswered Questions | FR-18 |

**Navigation rules:**

- **The fag-rail, from 1024 px:** a persistent left column on every signed-in page except sessions. It leads to Hjem, Repetisjon, each Fagoversikt, D02 and D01 (contents in Component Patterns, Shell and navigation). It marks the current item: Hjem, or the fag you are in (including while on that fag's Tema pages).
- **Below 1024 px:** two bars.
  - The top-bar holds the app name (to Hjem), «I dag · 14» (to Repetisjon) and the avatar (D01).
  - Under it, the fag-switcher: one button that shows the current fag and its due count («Databaser DAT102 · 9 i dag»), or «Alle fag · 3 fag · 14 i dag» on Hjem. It opens the same list as the fag-rail.
- **No bottom tab bar.** The top-bar reaches the only two phone destinations, Hjem and Repetisjon.
- **Hierarchy:** Hjem › fag › tema. From 600 px there is a breadcrumb; below 600 px, a back link to the parent («‹ Databaser»).
- **Sessions** (P06 to P11, including the result pages) replace the fag-rail, top-bar and fag-switcher with a session-bar that has an exit, so the Student can concentrate. The exit returns to the surface the session started from.
- **Dialogs:** one level deep, never stacked.

**Course overview requirement** («oversiktlig»): a Student must see every fag they have added, and for each fag:

- its name and code;
- the cards due today;
- its weakest tema or «Trenger øving» count;
- its mastery and trend;
- a way in.

The fag-rail gives the short form on every page from 1024 px: name, code, due count and mastery. Hjem gives the full form. Fagoversikt does the same for the tema of one fag. How the list behaves with eight or more fag is in State Patterns (mock P03, state d).

Fag appear in the order they were created, in the fag-rail and on Hjem alike. `[ASSUMPTION: the order is the mockup's note, not a source]`

**Visual reference:** the mockup [`mockups/14-fagskinnen.html`](mockups/14-fagskinnen.html). It holds all 24 surfaces in desktop, tablet and phone frames, in light and dark, each with its alternative states. **The spines win on any conflict with the mockup**, with the 2026-11-05 mocks and with any import.

**Surface closure:** every PRD capability has a surface in the table. The surfaces that no Key Flow reaches are listed in Key Flows, Coverage notes.

## Voice and Tone

Microcopy, in Norwegian bokmål. The brand voice lives in DESIGN.md, Brand & Style.

- Speak to the Student as «du». Treat them as an adult: plain, direct, respectful.
- Be calm and plain: say what happened, then what to do next.
- No exclamation marks, no emojis, no inflated praise, no cheering, no scolding.
- Write numbers as digits and dates as «12. november» (short form «12. nov.» in tables). Use sentence case; the app's own nouns (fag, tema, kort) stay lowercase in running text.
- **The next-step-band formula:** an imperative action («Repeter dagens kort»), then a why sentence with the numbers («14 kort forfaller i dag: Databaser 9 og Statistikk 5.»), then a size and «ca. 12 min».
- **Calm messages** say there is nothing to do and when there will be: «Ingen kort i dag. Neste kort kommer 18. november.»
- **Trend in words:** «Opp 4 poeng», «Ned 6 poeng», «Uendret», with when («etter økta 12. nov.»). On Hjem: «1 tema ned siden sist», «Uendret siden sist».

| Do | Don't |
|---|---|
| «7 av 10 riktige. Øv på de 3 du ikke fikk til.» | «Supert jobba! 🎉» |
| «Dette temaet trenger mer øving.» | «Svakt tema!» or «Du er dårlig på dette.» |
| «Repeter dagens kort» · «ca. 12 min» | «Klar for dagens utfordring?» |
| «Bra: kortet kommer tilbake torsdag 19. november. Torsdag går fra 3 til 4 kort.» | «Godt husket! +10 poeng» |
| «2 elementer ble fjernet fordi kildehenvisningen ikke stemte.» | «Referansefeil (kode 422)» |
| «Filen har 70 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.» | «Ugyldig fil.» |
| «Lager studiemateriell …» · «Vanligvis under 2 minutter. Hold siden åpen til det er klart.» | «Vennligst vent …» |
| «Kunne ikke rette svaret fordi KI-tjenesten ikke svarte. Prøv igjen.» | «Noe gikk galt.» |
| «KI-tjenesten har mange forespørsler akkurat nå. Vent noen minutter og prøv igjen.» | «Feil 429: For mange forespørsler.» |
| «Du har brukt alle 20 genereringene for i dag. Grensen nullstilles ved midnatt.» | «Grense nådd.» |
| «Sjekk adressen, eller velg et fag i listen. Fagene dine og dagens kort står der som før.» | «Oi, her var det tomt.» |

Interface labels. The Concept column uses PRD Glossary terms exactly as written.

| Concept | Label in the interface |
|---|---|
| Course / Topic / Source | fag / tema / kilde |
| Course overview | The Course's own name as the screen title |
| The fag-switcher | «Fag», «Alle fag», «Hjem · alle fag», «Bytt fag» (accessible name) |
| The theme heading in D01 | «Utseende» («tema» already means Topic) |
| Study material / Summary / Key concept | studiemateriell / sammendrag / nøkkelbegrep |
| Detail level | detaljnivå: «Kortfattet», «Middels», «Detaljert» («kort» is taken by Flashcards) |
| Simpler explanation | «Forklar enklere» (the action), «Enklere forklaring» (the heading) |
| Flashcard / Review / Due today | kort / repetisjon / «I dag» |
| Question, with Multiple-choice question and Free-text question | spørsmål, with the type labels «Flervalg» and «Fritekst» |
| Hint / Quiz / Answer / Explanation | hint / quiz / svar / forklaring |
| Practice mode / Exam mode | øving / prøveeksamen |
| Grade: correct, partially correct, incorrect, not graded | «Riktig», «Delvis riktig», «Feil», «Ikke rettet» |
| An overridden Grade | «Endre vurdering» (the action); «Endret av deg» beside the Grade; the original as «KI-vurdering: Delvis riktig» |
| Source status: generating, ready, failed | «Lager studiemateriell …», «Klar», «Feilet» |
| Generation call | generering (only in the daily-limit message) |
| Retry round | «Øv på feilene» |
| Quiz history | «Tidligere quizer» |
| Topic score / Weak topic | mestring («Mestring 45 %») / «Trenger øving» |
| Course score | «Mestring 61 %» (in the fag-rail «61 %»), explained on Hjem in the forecast footer and on Fagoversikt under the title: «Mestring for et fag er snittet av temaene som har nok svar.» |
| Next step | No label of its own: the next-step-band names the action |
| The weakest tema of a fag | «Svakest: Normalisering 45 %» |
| Answer history | «Siste 20 svar» |
| Reference | «Side 14» for PDF, the heading for Word, «Avsnitt 3» for plain text, followed by the quote |
| Generated item | element (only in counts) |
| Sample document / Mock mode | eksempeldokumentet / demomodus |
| AI provider / Key | KI-tjenesten / API-nøkkel |
| The ratings Again, Hard, Good, Easy | «Igjen», «Vanskelig», «Bra», «Lett» |
| Return times on the rating-buttons | «i dag», «i morgen», «om 3 dager», «om 1 uke» (always the real next date; see Component Patterns) |
| The forecast on Hjem / on P04 / on P05 / in Repetisjon | «Studievarsel for fagene dine» / «Kort i {fag} neste 7 dager» / «Varsel for temaet» and «Kort i temaet neste 7 dager» / «Studievarsel, neste 7 dager» |
| The forecast's unit and scope | «Kort som skal repeteres per dag. Bare kort som allerede har fått en dato.» · «47 kort de neste 7 dagene» |
| Day labels | «I dag», «I morgen», «Ons 18.» (phone: «Tir» over «17.») |

## Component Patterns

Behavioral rules only; the visual specs live in DESIGN.md, Components. The component names that replace those of the 2026-11-05 spine are listed in `.memlog.md`.

### Shell and navigation

| Component | Use | Behavioral rules |
|---|---|---|
| fag-rail | Every signed-in page from 1024 px, except sessions | Each fag-rail-row is one link to its Fagoversikt, and its accessible name includes the due count and mastery («Databaser, 9 kort i dag, DAT102, mestring 61 % i snitt»). The current item carries `aria-current="page"`. «I dag · N» opens Repetisjon; N is the Due-card count across all fag and updates as cards are rated. «Nytt fag» opens D02. The account opens D01 upward. With no fag, the list reads «Ingen fag ennå. Lag ett fag for hvert emne du tar.» |
| top-bar | Every signed-in page below 1024 px, except sessions | The app name goes to Hjem. «I dag · N» opens Repetisjon. The avatar opens D01. |
| fag-switcher | Under the top-bar, below 1024 px | Shows the current fag, its code and due count, or «Alle fag» on Hjem. It opens a list (`aria-haspopup="listbox"`) with «Hjem · alle fag», one row per fag with its due count, code and mastery, and «Nytt fag». Choosing a fag opens its Fagoversikt. It is hidden when there are no fag. |
| breadcrumb | Fagoversikt and Tema, from 600 px | Every level except the current one is a link. Below 600 px it is replaced by a back link to the parent. |
| mode-banner | Under the top-bar and on P01 and P02, whenever Mock mode is on | One line: «Demomodus: appen bruker innspilte svar for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.» It cannot be closed (FR-20). |

### Next step

| Component | Use | Behavioral rules |
|---|---|---|
| next-step-band | P03 and P04 (the PRD's Next step, FR-28); P05, P07 and P11 (a UX-level extension); directly after the title | **Exactly one per page.** It names one action, why, a size and a time, and it has one button. That button is the page's primary action; every other action on the page is secondary. When there is nothing to do, the band is replaced by a calm-message, or left out where an empty-state already carries the action. Which action each page shows is listed below this table. |
| next-step-row | Under the session-bar in P06, P08, P09 and P10 | The compact band. It names the next step and what remains: «Neste spørsmål · 6 spørsmål igjen · ca. 5 min · Enter går videre»; «Vurder kortet, så kort 2 · 13 kort igjen · ca. 11 min · 1–4 vurderer»; «Kort 5 av 22 · 18 kort igjen i temaet · → neste kort»; «Spørsmål 8 · 13 ubesvart · 18:42 igjen · Enter neste spørsmål». It is text, not a second button: the action happens through the main control or the key it names. |
| calm-message | In place of the band when nothing is due or needed | One line, no button: «Ingen kort i dag. Neste kort kommer 18. november.» |

**Priority when several actions apply (PRD FR-28).** On Hjem and Fagoversikt the band picks the first that applies, within the page's scope (all fag on Hjem, one fag on Fagoversikt):

1. Due cards today → «Repeter dagens kort» (Repetisjon). Short and due today, so it comes first.
2. Weak topics → «Øv på de svake temaene» (D10), weakest first.
3. A tema without kilder → «Legg til kilde» in that tema.
4. Otherwise the calm-message, with no button and the date of the next Due card.

If step 2 of the build plan misses 30 November, Weak topics move to Should (PRD §7.1), and rule 2 is dropped until they are built.

**The band's action per page.** Pages with no band (the No fag, No tema and All correct states) are in State Patterns.

| Page | Condition | Band | Button goes to |
|---|---|---|---|
| Hjem | Due cards today | «14 kort» · «Repeter dagens kort» · «14 kort forfaller i dag: Databaser 9 og Statistikk 5.» · «ca. 12 min» | «Start repetisjon» → P09 |
| Hjem | Nothing due, Weak topics exist | «Øv på de svake temaene», across all fag | «Øv på svake temaer» → D10 |
| Hjem | Nothing due, no Weak topics, a tema without kilder | «1 kilde» · «Legg til kilde i {tema}» · «{tema} i {fag} har ingen kilder ennå.» · «ca. 2 min» | «Legg til kilde» → D04 or D05 |
| Hjem | Nothing due or needed | calm-message «Ingen kort i dag. Neste kort kommer {dato}.» | — |
| Fagoversikt | Due cards in this fag | «9 kort» · «Repeter kortene i Databaser» · «9 kort forfaller i dag: Normalisering 5, Transaksjoner 3 og Grunnleggende SQL 1.» · «ca. 8 min» | «Start repetisjon» → P09 (this fag's cards) |
| Fagoversikt | Nothing due, Weak topics exist | «43 spørsmål» · «Øv på de svake temaene» · «2 temaer trenger øving: Normalisering 45 % og Transaksjoner 55 %.» · «ca. 25 min» | «Øv på svake temaer» → D10 |
| Fagoversikt | Nothing due, no Weak topics, a tema without kilder | «1 kilde» · «Legg til kilde i {tema}» · «{tema} har ingen kilder ennå.» · «ca. 2 min» | «Legg til kilde» → D04 or D05 |
| Fagoversikt | Nothing due or needed | calm-message «Ingen kort i {fag} i dag. Neste kort kommer {dato}.» | — |
| Tema | It has Questions | «10 spørsmål» · «Ta en quiz i Normalisering» · «Mestring 45 %, så temaet trenger øving. 28 spørsmål er klare fra forelesning 5.» · «ca. 8 min» | «Start quiz» → D06 |
| Tema | No kilder | «1 kilde» · «Legg til den første kilden» · «Quiz og kort lages fra kildene dine.» · «ca. 2 min» | «Legg til kilde» → D04 or D05 |
| Resultat | Some Answers missed | «3 spørsmål» · «Øv på feilene» · «Spørsmål 3, 4 og 5 var feil eller delvis riktige. Runden teller ikke i mestringen.» · «ca. 3 min» | «Øv på feilene (3)» → P06 |
| Resultat for prøveeksamen | Some Answers missed | «6 spørsmål» · «Øv på feilene» · «3 av de 6 er fra Normalisering, som fortsatt trenger øving.» · «ca. 6 min» | «Øv på feilene (6)» → P06 |

- `[ASSUMPTION: the time estimates]` How «ca. N min» is computed is not in any source.
- The mockup does not show the rows "Nothing due, Weak topics exist" on Hjem, "a tema without kilder" on either page, or the calm-message on Fagoversikt. They follow from the priority rule.

### Forecast and mastery

| Component | Use | Behavioral rules |
|---|---|---|
| forecast-chart | Hjem (all fag), Fagoversikt (one fag, mini), Tema panel (one tema, mini), Repetisjon (all fag), the end of Repetisjon | Seven days from today, each with its count printed. **Real data only:** it counts only Due cards that already have a date and never shows a prediction. The footer says the numbers change as you review. It updates when ratings are saved. In Repetisjon, today's column shows the cards left in the round. At the end, today is drawn as «Repetert» with the number of cards reviewed. `[ASSUMPTION: new Flashcards that have not entered Due today yet (FR-15: at most 20 a day) are not counted ahead of time]` |
| fag-forecast-row | Hjem, one per fag, under the chart | The whole row opens the Fagoversikt. It shows the name and code, the number of tema, the practice-tag with the Weak-topic count, «Svakest: {tema} {score}», the fag's mastery and trend, and the Due cards per day in the chart's columns. The «⋯» menu (D07) offers rename and delete; it is a separate control, not part of the row link. Below a container width of 560 px, the day columns are dropped and the row says «9 kort i dag». |
| tema-forecast-row | Fagoversikt | The whole row opens the Tema. It shows the tema name, the practice-tag if weak, mastery, the trend with the session that changed it, the answer-history, and the number of kilder. The «⋯» menu offers rename and delete. **Order:** Weak topics first, lowest first (FR-17), then the rest in order of creation `[ASSUMPTION: the order of the rest]`. |
| tema-forecast-panel | Tema («Varsel for temaet») | Shows the date, mastery with «Basert på de 20 siste svarene dine.», the practice-tag, the trend, «Siste 20 svar» with the session count, and the tema's mini forecast. It holds no actions: those live in the tema-tabs, so the panel never adds a second primary button. |
| mastery-meter | fag-rail-row, fag-forecast-row, tema-forecast-row, tema-forecast-panel, the D10 topic-picker, P11 | Always shows the labeled percent beside the bar. With fewer than 5 graded Answers it shows «Ikke nok data ennå» (or «–» in the fag-rail) and a dotted, empty track, and the tema is not a Weak topic (FR-16). It updates each time a Grade is saved, including an overridden Grade, so a Quiz left mid-way updates it too. Retry rounds, Answers that are not graded, and ratings do not count (FR-16). |
| Course score (mastery per fag) | fag-rail-row, fag-forecast-row, Fagoversikt under the title | The mean of the Topic scores of the tema that have enough data (PRD Course score, FR-16). «–» or «Ikke nok data ennå» when none has. Hjem explains it in the forecast footer; Fagoversikt shows «Mestring 61 % i snitt» with a mastery-meter under the title and the same explaining line (Voice and Tone). |
| trend-label | fag-forecast-row, tema-forecast-row, tema-forecast-panel, P11 | **Per tema:** the change in mastery caused by the most recent session that changed it, in points («Opp 4 poeng» / «etter økta 12. nov.»); the session is outlined in the answer-history. A tema with too little data shows «Første økt» and the date. **Per fag:** how many tema went up or down since the last session («1 tema ned siden sist», «Uendret siden sist»). `[ASSUMPTION: trend is not in the PRD; the definitions are read from the mockup]` |
| practice-tag | fag-forecast-row («2 temaer trenger øving»), tema-forecast-row, tema-forecast-panel, D10, P11 | Marks a Weak topic (Topic score under 60 %, FR-17). Always text with an icon. |
| answer-history | tema-forecast-row, tema-forecast-panel | The last 20 graded Answers, grouped by session with the date. An overridden Grade shows as the new Grade with a mark for «endret av deg» (FR-12). The accessible name reads the sessions out («5. november: 3 riktige, 1 delvis, 4 feil, 1 endret av deg. …»). With fewer than 20, it says «4 av 20 svar». |

### Content and actions

| Component | Use | Behavioral rules |
|---|---|---|
| button | Everywhere | At most one primary per region: the next step. Where a band is present, the band's button is the primary. `button-destructive` appears only inside a confirm dialog. A button is never disabled without a visible reason next to it. While an action runs, the button keeps its label, shows a spinner and ignores further presses. |
| text-input | P01, P02, D02, D03, D08, pasted text | The label is above the field and always visible. Errors appear below the field in words and are linked to it. Enter submits. |
| segmented-control | Detail level in D05 and the summary-block; theme in D01; presets in D06 and D11 | Exactly one option is selected. Changing the Detail level of an existing Summary regenerates only the Summary (FR-7), with no confirm. That is a Generation call: at the daily limit the control keeps the current Summary and shows the daily-limit message (NFR-7). |
| status-label | source-row | The Source status (FR-9): «Lager studiemateriell …» with a spinner as the progress indicator, «Klar» (with «· 2 elementer fjernet» when the Reference check removed items), «Feilet». Text with an icon. Status changes update without a reload and are announced politely. A kilde is never shown as generating after its run has stopped. |
| source-row | The «Kilder» tab in Tema | Shows the name, type, size, Detail level and status. Kilder are listed newest first. `[ASSUMPTION]` The «⋯» menu offers rename and delete. |
| upload-panel | D05 | Offers a drop zone from 600 px («Slipp filen her»), «Velg fil», and «Lim inn tekst». The limits are shown up front («PDF eller tekstfil · maks 50 sider eller 10 MB»). Size, type and length are checked before upload (FR-3). The Detail level defaults to «Middels» `[ASSUMPTION]`, with «Gjelder sammendraget. Du kan bytte detaljnivå senere.» In Mock mode it offers «Bruk eksempeldokumentet», which uploads the Sample document in one step. At the daily limit (NFR-7) the panel shows the daily-limit message and «Last opp» stays inactive with that message beside it; nothing is uploaded or sent. |
| summary-block | Each ready kilde in the «Sammendrag» tab | The full Summary at reading width, not truncated, with the Detail level control in its header. No Reference in v1. |
| key-concept-item | Each kilde in Tema | The term, the definition and the Location («Side 14», FR-23). «Vis kilde» opens the reference. «Forklar enklere» (Should, FR-19) opens «Enklere forklaring» below, with «Basert på side 14» and «Lag ny». Once saved, the Simpler explanation shows instantly next time. Making one, and «Lag ny», are Generation calls; showing a saved one is not (NFR-7). The «⋯» menu offers «Slett» (FR-24). `[ASSUMPTION: the quote opens on demand]` |
| reference | feedback-panel, the back of a flashcard, key-concept-item | The Location first, then the verbatim quote in the Source's language. Never a link that leaves the app. |
| dialog | D02 to D06, D08 to D12 | Opens over the current surface; a bottom sheet below 600 px. «Avbryt» and Esc close it. A confirm-delete dialog names what goes and everything under it («Slette faget Databaser? 4 temaer, 7 kilder og alle svar slettes. Dette kan ikke angres.»), and its destructive button repeats the verb («Slett faget»). D04 shows the FR-22 notice before the first upload in Real mode, once per Student. Its buttons are «Jeg forstår, fortsett» and «Avbryt»; Esc counts as «Avbryt», and then nothing is sent. |
| menu | D01, D07 | Opens at its trigger; Esc and a click outside close it. The account menu opens upward from the foot of the fag-rail. |
| topic-picker | D10, D11 | A checkbox list of the fag's tema with mastery, trend and the number of Questions. Weak topics are preselected in D10 («Temaene som trenger øving er valgt. Svakeste først.»). The footer counts the selection («2 temaer valgt · 43 spørsmål»), and the start button repeats it («Start quiz · 43 spørsmål»). |
| empty-state | Hjem, Fagoversikt, Tema, Repetisjon | A heading, one sentence and one primary action: «Ingen fag ennå» / «Lag ett fag for hvert emne du tar, og legg temaer inn under det.» / «Nytt fag». |
| inline-message | Where a problem happens: upload, generation, grading, network, the Key | Appears in place, never as a toast. It says what happened and what to do, and stays until solved or dismissed. It is announced politely, or assertively when it blocks the current action. |
| skeleton | First load of Hjem, Fagoversikt and Tema | Shown only if loading takes more than 300 ms. Its shapes match the final layout, and it is replaced in place. |

### Tema-tabs: Sammendrag, Quiz, Test deg selv, Kilder

Every tema gives direct access to its summary, quiz and self-test. A tema is the PRD's Topic, "a chapter or theme", so a chapter's summary, quiz and self-test live on the tema page. The four tabs are the four areas of PRD FR-23.

| Component | Use | Behavioral rules |
|---|---|---|
| tema-tabs | P05, directly under the band | Four tabs in this fixed order: «Sammendrag», «Quiz · 28», «Test deg selv · 22 kort», «Kilder · 2». «Sammendrag» is selected on arrival. The counts hide below 600 px so all four labels fit on a phone. ARIA tablist: ← and → move between tabs and select them, Home and End jump to the ends, and Tab moves into the panel. The selected tab is kept in the URL (for example `…/normalisering?fane=quiz`), so the browser's back button and a shared link return to it. `[ASSUMPTION: tab in the address]` The band stays above the tabs and keeps the page's one primary button whichever tab is open. |
| «Sammendrag» tab | P05 | One summary-block per ready kilde, newest first, each followed by its Key concepts with Location, «Vis kilde» and «Forklar enklere». A kilde still generating shows one dashed line: «{kilde}: sammendraget lages. Vanligvis under 2 minutter.» There is one Summary per kilde (FR-7), so a tema with several kilder shows several summaries. There is no combined summary for the whole tema (FR-23). |
| «Quiz» tab | P05 | A tool-card «Quiz i {tema}» naming how many Questions are ready and of which kinds, with «Velg antall og start» (secondary, opens D06). Under it, quiz-history. |
| quiz-history | The «Quiz» tab, under the heading «Tidligere quizer» | PRD FR-27. One row per earlier Quiz in this tema, newest first: date, «3 av 6 riktige · 1 delvis», the answer strip with the Grade of each Answer (an overridden Grade carries its mark), and one quiet action: «Øv på feilene (N)» on the newest row when it has misses, otherwise «Se resultatet» (P07). The note under it says «Runder med «Øv på feilene» teller ikke i mestringen.» With no Quiz yet, the list is replaced by «Du har ikke tatt en quiz i dette temaet ennå.» |
| «Test deg selv» tab | P05 | Two tool-cards. **Kort:** «22 kort i temaet. 5 forfaller i dag.» with «Repeter dagens kort (5)» (secondary, P09 with only this tema's Due cards, FR-15 and FR-23) and «Bla i alle kort» (quiet, P08). With nothing due, the first button is replaced by the text «Ingen kort i dag», and «Bla i alle kort» stays. **Prøveeksamen** (Should): «Spørsmål fra hele temaet, med klokke og uten hint.» with «Sett opp prøveeksamen» (D11 with this tema preselected) and the note «Vil du ha med flere temaer? Start prøveeksamen fra {fag}.» |
| «Kilder» tab | P05 | «Legg til kilde» (secondary) and the source-rows, newest first, with status-label and «⋯». A failed kilde has «Prøv igjen» on its row, without a new upload (FR-9). The Reference-check note («2 elementer ble fjernet …») shows on the kilde's summary in «Sammendrag». |
| tool-card | «Quiz» and «Test deg selv» tabs | A bordered card: icon, a name, one or two sentences of what it does, and its actions on the right from 600 px (below that, under the text). Never a primary button. |

### Sessions

| Component | Use | Behavioral rules |
|---|---|---|
| session-bar | P06 to P11 | **Left:** «Avslutt», which leaves at once, since Answers and ratings are already saved (FR-10). In an exam it is «Lever», which opens D12. **Middle:** the progress («4 av 10»), with a strip of one slot per Question (Quiz, exam) or a progress bar (Repetisjon). **Right:** the context («Normalisering · øving», «I dag · repetisjon») or, in an exam, the time left, always visible (FR-18). Result pages keep the session-bar with «Avslutt» and «Resultat». |
| question-card | P06, P10 | One Question per screen, with its type label and position. In Practice mode «Vis hint» shows the Hint inline. An exam has no Hint (FR-18). |
| option-row | P06, P10 | Four options, A to D; a click, a tap or 1 to 4 selects. In Practice mode «Svar» or Enter submits; the options then lock and show «Ditt svar» and «Riktig svar» in words and icons, with the feedback-panel below. In an exam, selecting is all that happens («Valgt»). |
| free-text-answer | P06, P10 | «Svar» submits. While grading, «Retter svaret …» shows where the feedback will appear. After grading, «Vis fasit» shows the model answer with its Location. |
| feedback-panel | P06; the question rows in P07 and P11 | The Grade in words with an icon, the Explanation and the reference. For an incorrect Multiple-choice Answer it names the correct option and why the chosen one is wrong (FR-11). Actions: «Neste spørsmål» and «Slett spørsmålet» (FR-24, via D09). A mock Grade carries «Demo» (FR-12). **Grade override (FR-12):** on a graded Answer to a Free-text question, a quiet «Endre vurdering» opens a menu with «Riktig», «Delvis riktig» and «Feil». The choice saves at once. The heading then shows the new Grade with «Endret av deg», and the line «KI-vurdering: Delvis riktig» keeps the original Grade and its Explanation in view. Once a Grade is overridden, the menu adds «Bruk KI-vurderingen» to undo the override. The overridden Grade is the one used in mastery (FR-16) and in «Øv på feilene» (FR-13). It is not offered on Multiple-choice questions, on «Ikke rettet», or in an exam before «Lever». |
| result-summary | P07, P11 | The score («7 av 10»), a lead sentence, and a strip of every Question by Grade. Each question row expands to its feedback-panel. Overriding a Grade there updates the score, the strip and the «Øv på feilene (N)» count in place. In P07 a link reads «Mestringen for Normalisering er oppdatert med disse svarene. Se varselet for temaet» (→ P05). P11 adds a per-tema table: «Prøveeksamen» (score), «Mestring nå», «Endring» («Opp 3 poeng fra 45 %»), and groups the questions by tema. `[ASSUMPTION: showing both exam score and new mastery per tema in P11 is the mockup's choice on an open point]` «Tilbake» returns to where the session started. |
| flashcard | P08, P09 | The front shows first. A click, a tap, Space or Enter flips it to the back, with the answer and the reference. The meta line shows «{fag} › {tema}» and «Forside»/«Bakside». `[ASSUMPTION: showing fag and tema on the Repetisjon card was an open point]` P08 also shows «Neste repetisjon: 18. november». In P08, «Forrige», «Neste» and ← → move between cards in the order they were made, and browsing never changes a card's next review date (FR-14). The «⋯» menu offers «Forklar enklere» (Should) and «Slett kortet» (D09). |
| rating-buttons | P09, after the card is flipped | «Igjen», «Vanskelig», «Bra», «Lett» (keys 1 to 4). Each button names when the card returns, under its name. A rating saves at once and shows the next card; a card rated «Igjen» returns later in the same Review (FR-15). There is no undo in v1. `[ASSUMPTION]` **The return time is the real next date** computed for this card by the FR-15 scheduler, phrased relative to today («i dag», «i morgen», «om 3 dager», «om 1 uke», «om 2 mnd.»). The interval after «Bra» grows with each «Bra» in a row and is never longer than 180 days (FR-15). `[ASSUMPTION: the intervals in the mockup are illustrative]` The mockup's intervals are Leitner-like; the actual intervals depend on which scheduler the architecture picks (addendum: Leitner, SM-2 or FSRS) and vary per card. |
| return-forecast | P09, under the rating-buttons | Previews where the card lands. Hovering or focusing a rating marks the target day with «+1» and rewrites the sentence («Bra: kortet kommer tilbake torsdag 19. november. Torsdag går fra 3 til 4 kort.»). The sentence is a polite live region. With no hover or focus, «Bra» is previewed. A return beyond the seven days says so («… etter varselet under»). There is no flying-card animation. `[ASSUMPTION: on touch screens there is no hover, so the preview stays on «Bra» until a rating is tapped, and the tap rates at once]` |
| exam clock | session-bar in P10 | Counts down, tabular. When 5 minutes remain, the clock turns copper and «5 minutter igjen» shows until the Student moves to the next Question; the clock is announced at that point and again when 1 minute remains. At 0 the Answers are submitted. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Signed out | Any | P01. After signing in, the Student returns to the surface they asked for. `[ASSUMPTION]` |
| Wrong credentials | P01 | An inline-message above the fields: «Feil e-post eller passord.» |
| Email in use | P02 | Under the field: «Det finnes allerede en konto med denne e-postadressen.» and a «Logg inn» link. |
| Sign-up closed | P01, P02, on the Hosted instance (FR-25) | «Opprett konto» is hidden. A direct visit shows «Registrering er stengt på denne installasjonen.» |
| First load | Hjem, Fagoversikt, Tema | A skeleton, replaced in place. |
| No fag | Hjem | The empty-state «Ingen fag ennå» with «Nytt fag». No band, no forecast. The fag-rail reads «Ingen fag ennå» and keeps «Nytt fag»; the fag-switcher is hidden. |
| One to seven fag | Hjem, fag-rail | Normal rows. |
| Eight fag or more | Hjem, fag-rail | Compact fag-forecast-rows; the fag-rail fits 8 above the account at 800 px height. `[ASSUMPTION: the threshold for compact rows]` |
| More than 10 fag | fag-rail, Hjem | The fag list in the fag-rail scrolls on its own; «Hjem», «I dag» and the account stay fixed. On Hjem the rows continue down the page. |
| A fag with no mastery data | fag-rail, Hjem | «–» with a dotted meter in the fag-rail; «Ikke nok data ennå» on Hjem. «Svakest:» still names the weakest tema, without a score. |
| No tema | Fagoversikt | The empty-state «Ingen temaer ennå» / «Et tema samler kildene, kortene og spørsmålene for én del av faget.» / «Nytt tema». No band. |
| No kilder | Tema | The band «Legg til den første kilden». The empty-state «Ingen kilder ennå» / «Legg til en PDF, en tekstfil eller tekst du limer inn. Quiz og kort kommer når studiemateriellet er klart.» Quiz and Flashcard actions are hidden. |
| No Flashcards yet | Hjem | No Review band, and the forecast shows zeros. |
| Generating (v1) | Tema | In v1 generation runs while the Student waits (FR-9). The source-row reads «Lager studiemateriell …» with a spinner and «Vanligvis under 2 minutter. Hold siden åpen til det er klart.» (NFR-3). The tabs and other kilder work as normal meanwhile; that kilde's Questions and Flashcards are not used until ready. |
| Generation interrupted | Tema | If the Student closed or left the page while generating, the kilde shows «Feilet» on return, with «Genereringen stoppet fordi siden ble lukket. Prøv igjen.» and «Prøv igjen». It never shows as generating forever (FR-9). |
| Generating in the background (Should) | Tema | With FR-26 built, the hint becomes «Vanligvis under 2 minutter. Du kan gå fra siden imens.» On return, the source-row shows the current status, and Study material that finished meanwhile is shown. |
| Items removed by the Reference check | Tema | «Klar · 2 elementer fjernet», and under the material: «2 elementer ble fjernet fordi kildehenvisningen ikke stemte.» (FR-8) |
| Generation failed | Tema | «Feilet», with «Kunne ikke lage studiemateriell fordi svaret fra KI-tjenesten ble avbrutt. Prøv igjen.» and «Prøv igjen», without a new upload. Nothing from the failed attempt is shown (FR-9). |
| Rate limit from the AI provider | Tema | «Feilet», with «KI-tjenesten har mange forespørsler akkurat nå. Vent noen minutter og prøv igjen.» and «Prøv igjen». No partial Study material is saved (FR-9). |
| Daily limit reached | D05, Tema («Prøv igjen», the Detail level, «Forklar enklere», «Lag ny») | An inline-message where the action was: «Du har brukt alle 20 genereringene for i dag. Grensen nullstilles ved midnatt.» No call is sent, and the control that would send one stays inactive with the message beside it. Quizzes, grading, Repetisjon and the Study material already made keep working. The limit applies in Mock mode too (NFR-7). |
| Upload rejected | D05 | In the upload-panel: the reason and the limit («Filen har 70 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.») and «Velg en annen fil». Nothing is uploaded. |
| Privacy notice declined | D04 | The dialog closes and nothing is uploaded. The notice shows again at the next upload (FR-22). |
| Mock mode | All | The mode-banner (FR-20). |
| Mock mode, another file | D05, Tema | «I demomodus lages studiemateriell bare for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.» with «Bruk eksempeldokumentet». The file is stored (FR-20). |
| Key rejected | Tema, Quiz | «KI-tjenesten godtok ikke API-nøkkelen. Sjekk nøkkelen i .env og start appen på nytt.» Existing Study material keeps working (FR-21). |
| Few Questions | D06 | Presets are capped at what is available («5», «10», «20», «Alle 28»), with «28 spørsmål tilgjengelig. Flervalg og fritekst blandes.» (FR-10). With none ready, the quiz band is not shown. |
| Grading | P06, Free-text | «Retter svaret …»; the field locks. At most 15 seconds (NFR-3). |
| Not graded | P06, P07 | «Ikke rettet» with «Prøv igjen» or «Prøv å rette igjen». «Spørsmålet er ikke med i «Øv på feilene» før det er rettet.» (FR-12, FR-13) |
| Mock Grade | P06 | «Demo» beside the Grade (FR-12). It can be overridden like any Free-text Grade. |
| Grade overridden | P06, P07, P11, the quiz-history, the answer-history | The new Grade with «Endret av deg», and «KI-vurdering: {Grade}» in the feedback-panel. Mastery updates at once (FR-16); «Øv på feilene» uses the new Grade (FR-13). |
| Retry round | P06 | The session-bar reads «Øv på feilene» and «1 av 3». A note says «Denne runden teller ikke i mestringen.» (FR-16) |
| Quiz left mid-way | P06 | «Avslutt» leaves at once. Answers so far are saved, count, and have already updated mastery (FR-10, FR-16). |
| All correct | P07 | No band. «Alle svarene var riktige.» and «Tilbake». |
| Nothing due | Hjem, Repetisjon | The calm-message «Ingen kort i dag. Neste kort kommer {dato}.» with the forecast. In Repetisjon, the same message and «Til Hjem». |
| End of Review | Repetisjon | «Repetisjonen er ferdig» · «Du repeterte 14 kort. Neste kort kommer i morgen.», a stat («9 kort i morgen»), «Kortene du vurderte nå, har fått nye datoer. Tallene under viser dem.», the updated forecast, and «Til Hjem» (FR-15). |
| Daily limit on new cards | End of Review | «I dag fikk du 20 nye kort. Flere kommer i morgen.» (FR-15) |
| Time running out | P10 | See exam clock. At 0, the Answers are submitted and P11 opens with «Tiden var ute, så svarene dine ble levert.» Unanswered Questions count as incorrect and join «Øv på feilene». `[ASSUMPTION: unanswered counts as incorrect is the mockup's rule]` |
| Exam left mid-way | P10 | The clock keeps running. If the Student reopens it in time: «Prøveeksamenen fortsetter der du slapp. Klokka gikk mens fanen var lukket, så du har 11 minutter igjen.» After the time is up, the Answers so far are submitted. |
| Moving around in an exam | P10 | «Forrige» and «Neste spørsmål» move freely; Answers can change until «Lever». The strip shows answered and unanswered. «Ingen hint og ingen tilbakemelding før du leverer. Du kan endre svarene til du leverer. Klokka går videre selv om du lukker fanen.» `[ASSUMPTION: going back was an open point]` |
| Submitting with gaps | D12 | «Levere nå?» · «3 av 20 spørsmål er ubesvart.» · «Ubesvart: spørsmål 4, 12 og 19 · 14:10 igjen» · «Fortsett prøveeksamen» / «Lever». |
| Grading after submission | P11 | «12 av 18 rettet» · «Retter 2 fritekstsvar …» · «Mestringen oppdateres når alle svarene er rettet. Du kan vente her eller gå tilbake.» |
| Too few Answers | Fagoversikt, Tema, P11 | «Ikke nok data ennå» with «4 av 20 svar»; not a Weak topic (FR-16). |
| Network lost | Where an action failed | An inline-message with «Prøv igjen». An Answer or rating does not count until saved. There is no offline mode (PRD §6). |
| Not found, or another Student's data | P12 | «Feil 404» · «Fant ikke siden» · «Sjekk adressen, eller velg et fag i listen. Fagene dine og dagens kort står der som før.» · «Til Hjem». The fag-rail stays, so the overview is still there. Nothing about the data is shown (FR-1). |
| Item deleted | Tema, P08, P06 | After D09, the item disappears and the counts and forecast update. No success message. `[ASSUMPTION]` D09 names the consequence: «Svarene dine på det teller ikke lenger i mestringen.» for a Question; «… forsvinner fra Bla i kort og fra varselet.» for a card. |

## Interaction Primitives

- **Pointer:** click or tap to act. The fag-rail-row, fag-forecast-row and tema-forecast-row are clickable as a whole; their «⋯» menus are separate targets.
- **Keyboard:**
  - Tab follows the reading order (fag-rail first, then the page), Enter submits, and Esc closes the top dialog or menu.
  - In a Quiz, 1 to 4 pick an option, Enter answers, and Enter again moves on. The next-step-row names the key.
  - In Repetisjon and Bla i kort, Space flips the card. In Repetisjon, 1 to 4 rate it; in Bla i kort, ← and → move between cards.
  - From 1024 px, keys are hinted next to the controls. `[ASSUMPTION]`
- **Preview before commit:** in Repetisjon, hovering or focusing a rating previews the return in the forecast. Focus alone is enough, so the preview never depends on hover.
- **Gestures:** none is ever the only way to do something. No swipe in v1. `[ASSUMPTION]`
- **Pace:** the Student sets it. Nothing moves on by itself, except when the time runs out in an exam.
- **Saving:** Answers, ratings and Grade overrides save the moment they are given (FR-10, FR-12). Only forms have save buttons.
- **Generation:** in v1 it runs while the Student waits on the Tema page, with a progress indicator. The rest of the page stays usable, but leaving the page stops the run (FR-9). Background generation is FR-26 (Should).
- **Daily limit:** at most 20 Generation calls per day (NFR-7). The message comes before anything is sent, never after a wait.
- **Destructive actions:** a confirm dialog comes first (FR-2, FR-24). No undo in v1.
- **Motion:**
  - Panels and dialogs take 150 to 250 ms ease-out; color changes take 160 ms. The flashcard flip takes 300 ms.
  - Nothing animates on page load; forecast bars and the return preview change in place.
  - With reduced motion on, flips, slides and spinners become instant changes.
- **Banned:**
  - confetti, streaks, points, badges, levels, sounds, mascots;
  - moving on by itself in Practice mode;
  - toasts for routine events;
  - stacked dialogs;
  - actions that only appear on hover;
  - infinite scrolling;
  - more than one next-step-band on a page.

## Accessibility Floor

Behavioral rules; visual contrast lives in DESIGN.md, Colors.

- **Standard:** WCAG 2.2 AA.
- **Not by color alone:** Grades, statuses, Weak topics and trends are always written in words, with an icon. Today in the forecast is labeled «I dag» as well as colored. Every bar, meter and day cell has its number printed.
- **Landmarks:**
  - the fag-rail is `nav` «Hovedmeny»;
  - the fag-switcher is `nav` «Bytt fag»;
  - the breadcrumb is `nav` «Brødsmuler»;
  - the band is a `section` labeled by its heading.
- **Charts as lists:** each forecast-chart is an ordered list with an accessible name («Kort per dag de neste 7 dagene»); each day reads «14 kort i dag», «6 kort i morgen». Each fag's day cells are a list named «Kort per dag i Databaser». The answer-history has a summary name per session.
- **Keyboard:** everything works by keyboard, and the focus ring is always visible. It is white on the petrol shell, band and session-bar (DESIGN.md `{colors.focus-on-shell}`) and `{colors.focus}` on the workspace.
- **Page titles:** each surface has its own, for example «Normalisering – Databaser – AI Study Buddy».
- **Announcements:**
  - Polite: the feedback-panel, source-row status changes, card progress, and the return-forecast sentence in Repetisjon.
  - Assertive: errors that block the current action.
  - The exam clock is announced only at 5 minutes and at 1 minute; its visible value has an accessible name in words («18 minutter og 42 sekunder igjen»).
- **Focus:**
  - A dialog keeps focus inside, starts on its title, and returns focus to its trigger.
  - After an Answer, focus moves to the feedback-panel heading; after «Neste spørsmål», to the next Question.
  - The fag-switcher list returns focus to its button on close.
- **Language:** `lang="nb"`; each kilde's Study material carries its own language (FR-6).
- **Touch targets:** at least 44 px. The rating-buttons are at least 64 px high, 10 px apart.
- **Zoom and reflow:** text can be enlarged to 200 %, and the layout reflows to 320 px without horizontal scrolling (WCAG 1.4.10). Below a container width of 560 px, the forecast rows drop their day columns, so nothing scrolls sideways.
- **Time limit:** the Student sets the exam's time limit (FR-18), which meets WCAG 2.2.1.
- **Forms:** labels are visible; errors are in words and linked to their field.

## Responsive & Platform

Breakpoints `[ASSUMPTION, carried and extended]`:

- `sm` below 600 px (phone);
- `md` 600 to 1023 px (tablet);
- `lg` from 1024 px (laptop and desktop, where the fag-rail appears);
- `xl` from 1200 px (the two-column Tema page).

Forecasts and tables also respond to their container width (DESIGN.md, Layout & Spacing).

| Surface | `sm` | `md` | `lg` / `xl` |
|---|---|---|---|
| Shell | top-bar + fag-switcher | Same, with a width cap on the switcher button | fag-rail + workspace; no top-bar |
| Hjem | Band (button on its own row); chart with short day labels; fag rows stacked with «N kort i dag», no day columns | Day columns appear once the forecast is wide enough | Day columns, axis, and a stat column inside each fag row on a wide forecast |
| Fagoversikt | Band, actions under it, mini forecast, tema rows stacked | Tema rows in two lines | Mini forecast in a panel beside the actions; a six-column tema table on a wide table |
| Tema | Forecast panel above the tema-tabs; tab counts hidden | Same, with tab counts | `xl`: reading column + «Varsel for temaet» on the right. At `lg` below 1200 px it stays stacked, because the fag-rail narrows the workspace |
| Sessions | Full width; rating-buttons 2 × 2 | Centered at reading width; rating-buttons in one row | Same, with key hints |
| Dialogs | Bottom sheet, buttons stacked full width | Centered dialog | Same; the account menu opens above the account in the fag-rail |
| upload-panel | «Velg fil» and «Lim inn tekst» | Adds the drop zone | Same |

- The tema-forecast-panel is not sticky.
- `[ASSUMPTION: thumb reach]` Whether the main session action (the rating-buttons, «Neste spørsmål») is pinned to the bottom edge on phones is not decided. The mockup keeps it in the flow under the card.
- Using the phone away from home needs the Hosted instance (FR-25, Should). The interface is the same.

## Inspiration & Anti-patterns

- **The posture:** a good bank app, Yr, Finn, or a university's student web or library system.
- **Lifted from Yr (via 06 Studievarselet):** study load as a seven-day forecast with values, today marked, and real data only.
- **Lifted from 08 Kortboksen, made adult:** the persistent left rail, as a flat petrol column with no drawer fronts, brass holders or tab colors. Also lifted: seeing when a card comes back, as words on the rating-buttons plus a forecast preview, with no box metaphor and no flying card.
- **Lifted from 04 Gule skilt, made adult:** the next-step band, as deep petrol with a large tabular number and one copper button. No airport yellow and no pictograms.
- **Rejected:**
  - Gamification in any form: Duolingo-style streaks, points, levels, badges and celebration.
  - Course colors (`course-1` to `course-6`): fag are told apart by name and code.
  - Mascots, illustrations of people, rounded display faces and pastel palettes.
  - A chat interface (PRD §6), endless feeds, and pages the inventory rules out: settings, statistics, onboarding, planner.
  - Dashboards of many charts. Hjem has one chart and one fag table.

## Key Flows

The protagonists are the PRD's: **Ida**, the Student, who stands in for the Author, and **Jonas**, the Examiner. The fag are Databaser (DAT102), Statistikk (STA100) and Programmering (ING101). The dates are in the week of Monday 16 November.

### UJ-1. Ida turns Monday's lecture into a quiz the same evening

1. Signed in on her laptop, Ida sees Hjem with the fag-rail on the left. She clicks «Databaser» in the fag-rail, and the row is marked as current.
2. In Fagoversikt she clicks «Nytt tema» (D03) and names it «Normalisering». The new Tema opens. The band reads «Legg til den første kilden» · «Quiz og kort lages fra kildene dine.», over the empty-state.
3. She clicks «Legg til kilde». Because this is her first upload in Real mode, D04 «Før du laster opp» explains where the text goes. She clicks «Jeg forstår, fortsett».
4. In D05 she drops the 32-page PDF, keeps «Middels» and clicks «Last opp».
5. The source-row reads «Lager studiemateriell …» with a spinner and «Hold siden åpen til det er klart.». Ida reads the slides' first pages while she waits.
6. The status turns «Klar». The «Sammendrag» tab shows the Summary and Key concepts, the «Test deg selv» tab now counts 22 kort, and the band reads «Ta en quiz i Normalisering».
7. She clicks «Start quiz» in the band. D06 has 10 Questions selected, and she starts. On the third Question she clicks «Vis hint».
8. She answers a Multiple-choice question incorrectly. The feedback-panel shows «Feil», the correct option, why hers is wrong, and «Side 14» with the quoted sentence. The next-step-row under the session-bar reads «Neste spørsmål · 6 spørsmål igjen · ca. 5 min».
9. **Climax:** the result reads «7 av 10». The band under it says «Øv på feilene: Spørsmål 3, 4 og 5 var feil eller delvis riktige.» She clicks «Øv på feilene (3)», and the three Questions she missed are back in front of her. The evening's lecture has become practice, not reading.

**Failure:**
- The 70-page compendium is rejected in D05 before anything is uploaded: «Filen har 70 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.»
- If generation fails, the source-row says what failed and offers «Prøv igjen» without a new upload. If the AI provider answers with a rate limit, the message asks her to wait a few minutes first.
- If the AI provider grades a Free-text Answer «Feil» where Ida thinks it is right, she clicks «Endre vurdering» and picks «Riktig». The Answer shows «Endret av deg», and it leaves «Øv på feilene».

### UJ-2. Ida clears Due today on the bus

1. On her phone, Ida opens the app on the Hosted instance (FR-25). The top-bar reads «I dag · 14», and the fag-switcher reads «Alle fag · 14 i dag».
2. The band on Hjem reads «14 kort» · «Repeter dagens kort» · «14 kort forfaller i dag: Databaser 9 og Statistikk 5.» · «ca. 12 min». She taps «Start repetisjon».
3. Repetisjon opens with the session-bar «1 av 14» and the next-step-row «Vurder kortet, så kort 2 · 13 kort igjen · ca. 11 min».
4. She reads the front, which is marked «Databaser › Normalisering», and taps to flip it. The back shows the answer and the reference.
5. The rating-buttons appear, each with its return time: «Igjen → i dag», «Vanskelig → i morgen», «Bra → om 3 dager», «Lett → om 1 uke». Under them the forecast already shows «Bra: kortet kommer tilbake torsdag 19. november. Torsdag går fra 3 til 4 kort.»
6. She taps «Bra», and the next card shows. A card she rates «Igjen» comes back before the end.
7. **Climax:** the screen reads «Repetisjonen er ferdig» and «Du repeterte 14 kort. Neste kort kommer i morgen.» The forecast below shows today as «Repetert» and the cards she just rated on the days they will return. Due today is empty, and she can see exactly when the cards come back.

**Failure:** if the connection drops mid-Review, an inline-message says the rating was not saved and offers «Prøv igjen». The card stays until the rating is saved.

### UJ-3. Two weeks before the exam, Ida drills Weak topics and sits a mock exam

1. Ida has already reviewed today's cards on the bus. She clicks «Databaser» in the fag-rail, and with nothing due the band in Fagoversikt reads «43 spørsmål» · «Øv på de svake temaene» · «2 temaer trenger øving: Normalisering 45 % og Transaksjoner 55 %.»
2. The tema table lists Normalisering and Transaksjoner first, each marked «Trenger øving», with its trend and its last 20 answers.
3. She clicks «Øv på svake temaer». In D10 both tema are preselected («2 temaer valgt · 43 spørsmål»), and she starts the Practice-mode Quiz.
4. Later she clicks «Prøveeksamen» (Should). In D11 she keeps all four tema, 20 Questions and 30 minutes.
5. The exam runs without Hints or feedback. The session-bar always shows the time left, and the strip shows what is still unanswered. She goes back to one Question to change her Answer.
6. She clicks «Lever». D12 says «3 av 20 spørsmål er ubesvart» and names them; she clicks «Lever». If the time runs out first, her Answers are submitted for her.
7. **Climax:** P11 shows «14 av 20» and a table per tema. It lists the exam score, the mastery now and the change, for example «Normalisering · 3 av 6 · 48 % · Opp 3 poeng fra 45 %». The band offers «Øv på feilene (6)». Back on any page, the fag-rail's meter for Databaser has moved too. She can see where she stands in every tema and in the whole fag.

**Failure:** she closes the tab mid-exam. If she reopens it before the time is up, the exam resumes and tells her how much time is left. If the time runs out first, her Answers so far are submitted.

### UJ-4. Ida gets a Simpler explanation of a Key concept that does not click (Should)

1. In the Tema «Normalisering», Ida reads the key-concept-item «Tredje normalform (3NF)», in the language of the slides.
2. She clicks «Forklar enklere».
3. The panel opens under the definition, first with a loading line, then with «Enklere forklaring»: at most three sentences in the language of the slides, and «Basert på side 14».
4. **Climax:** the concept clicks. The explanation is saved, so «Forklar enklere» shows it at once next time, with «Lag ny» if she wants another.

**Failure:** if the AI provider fails, an inline-message inside the panel offers «Prøv igjen».

### UJ-5. Jonas runs the app from the README without a Key

1. Jonas starts the app as the README describes. Logg inn shows the mode-banner for Mock mode.
2. He creates an account. Hjem shows «Ingen fag ennå», with no band and no forecast. The fag-rail reads «Ingen fag ennå» above «Nytt fag».
3. He creates the fag «Sensortest» (D02). It appears in the fag-rail with «0 temaer» and a dotted meter. Its Fagoversikt shows «Ingen temaer ennå», and he creates a tema (D03).
4. The band reads «Legg til den første kilden». In D05 he clicks «Bruk eksempeldokumentet». There is no privacy notice in Mock mode.
5. The Study material appears. The source-row reads «Klar · 1 element fjernet»: the Reference check caught the one wrong page in the recorded responses (FR-8).
6. He takes a Quiz from the band. His Free-text Answer gets «Delvis riktig» marked «Demo».
7. He takes «Øv på feilene» and then a Repetisjon from «I dag».
8. **Climax:** every core function has worked without a Key. The removed item even shows him the Reference check at work.

**Failure:** when he uploads another PDF, it is stored, and an inline-message explains that Mock mode only generates Study material for the Sample document.

### Flow 6. Ida keeps every fag in view across the semester

This flow comes from the course overview requirement («oversiktlig»). It is not a PRD UJ.

1. Monday morning, Ida opens the app on her laptop. Without scrolling, the fag-rail shows Databaser 9 (61 %), Statistikk 5 (71 %) and Programmering 0 (76 %).
2. Hjem's band says what to do first: «Repeter dagens kort», 14 cards, about 12 minutes.
3. Under it, «Studievarsel for fagene dine» shows 47 cards over the next seven days. Each fag's row shows its share per day, so she sees that Wednesday is heavy because of Databaser (6).
4. The Databaser row says «2 temaer trenger øving», «Svakest: Normalisering 45 %» and «1 tema ned siden sist». She clicks the row and lands in Fagoversikt, where Normalisering is first.
5. Later in the semester she has eight fag. The fag-rail still fits on her screen, and Hjem lists all eight in compact rows, in the order she created them. On her phone, the fag-switcher under the top-bar opens the same list.
6. **Climax:** whatever page she is on, the full list of fag, with today's cards and mastery for each, is one glance to the left. She never has to hunt for where she stands.

**Failure:** none specific. A fag without enough answers shows «–» and «Ikke nok data ennå» instead of a misleading number.

### Coverage notes

- **Surfaces not in a flow** (carried from 2026-11-05, plus rename and delete):
  - P08 Bla i kort, reached from the «Test deg selv» tab on the Tema (FR-14).
  - P12 Fant ikke siden.
  - D01 Kontomeny, for the theme and «Logg ut».
  - D07, D08 and D09, for rename and delete (FR-2, FR-24).

  Their behavior is fully specified above. Covering them in a Key Flow would need a new journey from the author.
- **Needs with a surface:** every PRD capability (FR-1 to FR-28, and NFR-7) and the three UX priorities have a surface:
  - the overview of all fag: the fag-rail and Hjem;
  - the next step: the next-step-band and next-step-row;
  - the adult look: DESIGN.md.
- **Not yet in the mockup** (added from the PRD on 2026-11-13; the spines win):
  - the Course score under the title on Fagoversikt;
  - «Endre vurdering» and the «Endret av deg» mark;
  - the rate-limit, daily-limit and interrupted-generation messages;
  - the v1 hint «Hold siden åpen til det er klart.».
