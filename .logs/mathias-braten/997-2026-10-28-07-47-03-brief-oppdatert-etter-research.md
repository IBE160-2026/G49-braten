# Brief oppdatert etter research

## 2026-10-28 kl. 07:47 — Mathias Bråten

### Oppgave
Legge funnene fra den tekniske research-en og faglærerens tilbakemelding inn i product brief og addendum.

### Plan
- `bmad-product-brief` i Update-modus, fast path. Fire valg avklart med brukeren: kort visjonsavsnitt, quizretting med ny øvingsrunde i v1, grense på 50 sider / 10 MB, fast path.
- Plan for research: [998-teknisk-research-llm-pdf](998-2026-10-28-07-43-43-teknisk-research-llm-pdf.md).

### Resultat
- `brief.md`: seks testbare funksjonelle kriterier, størrelsesgrense i stedet for «uavhengig av tekststørrelse», trinnvis bygging, leverandørlag med mock-modus, «Etter genereringen»-avsnitt, kort visjon. Fra ca. 970 til 1290 ord.
- `addendum.md`: beslutningspunktene fikk «Direction»-tillegg, to nye avviste alternativer og en seksjon «Research findings».
- Memlog fikk seks linjer, blant dem at visjonsavgjørelsen fra 15.09 er reversert. Filene i `_bmad-output/planning-artifacts/briefs/` er ikke committet.

### Åpne punkter
- Brief-en er lengre enn målet på 1–2 sider; vurder å flytte detaljer til addendumet.
- Språkvask/strukturgjennomgang (`bmad-review`) er ikke kjørt på brief og addendum.
- Rettingen av åpne quiz-spørsmål (modell mot kildetekst) er en antakelse merket [ASSUMPTION] i brief-en.
- Neste steg: PRD (`bmad-prd`).

## 2026-10-29 kl. 13:01 — Mathias Bråten

### Oppgave
Vurdere om briefen er klar for PRD, sjekke at research-funnene faktisk er tatt høyde for, og rette de punktene som manglet.

### Plan
- `bmad-help` for å plassere prosjektet i BMad-flyten (planleggingsfasen, neste obligatoriske steg `bmad-prd`).
- Sammenligne `research.md` (anbefaling 1–7) mot `brief.md`. Rapporten ble lest bare til og med linje 150, og addendumet ble ikke lest.
- Tre rettelser avtalt med brukeren: markere sidegrensen som antakelse, legge inn personvern, la `[ASSUMPTION]` om retting av åpne quiz-spørsmål stå.

### Resultat
- `brief.md`: sidegrensen 50 sider / 10 MB er nå merket `[ASSUMPTION]` (ingen kilde støtter tallet, bekreftes mot tester på egne notater og gratisnivåenes tokengrenser).
- `brief.md`: ny omfangslinje om personvern (pensumtekst sendes til leverandøren; Geminis gratisnivå kan bruke innhold til produktforbedring og la mennesker lese det; mock-modus sender ingenting ut).
- `brief.md`: `updated` satt til 2026-10-29. Status er fortsatt `draft`, siden `[ASSUMPTION]`-merkene står.
- Research-hull som ikke er i briefen, men bør i PRD/arkitektur: testkrav for uttrekk fra egne lysbilder, strukturert JSON-utdata, valg av PDF-bibliotek, PyMuPDF-lisens.
- Endringen i `brief.md` er ikke committet; bare loggfila og `issues.md` committes her.

### Åpne punkter
- Sidegrensen 50 sider / 10 MB er en antakelse som må bekreftes.
- PRD må ha krav om varsel til brukeren om at tekst sendes til ekstern leverandør.
- Neste steg: `bmad-prd` (anbefalt i ny kontekst etter `/clear`).
