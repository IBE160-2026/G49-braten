# Tilbakemelding på PRD

| | |
|---|---|
| **Gruppe** | G49 – G49-braten |
| **PRD vurdert** | `_bmad-output/planning-artifacts/prds/prd-Prosjekt A-2026-10-29/prd.md` (status: final, sist endret 2026-11-05, commit f05353f) |
| **Dato** | 2026-11-12 |
| **Type** | Formativ tilbakemelding, ikke karakter |

## 1. Samlet inntrykk

Dette er en sterk PRD med en tydelig tese, testbare FR-er, et konsekvent glossar og ærlig avgrensning. Den er et godt grunnlag for UX, arkitektur og stories. Risikoen ligger ikke i kvaliteten på teksten, men i at Must-listen er stor for ett semester og én person, og at kvaliteten på det KI-en lager (innhold og retting av fritekst) har få konkrete kontroller i Real mode.

## 2. Dette fungerer godt

- **Tesen bærer funksjonene.** §1 sier at produktet satser på å «close the loop between testing and repetition: every Answer decides what the Student practices next». Retry round, Review og Topic score følger av dette, og SM-4 («at least 60% are answered correctly the next time») måler tesen, ikke bare aktivitet. SM-C2 advarer mot å jukse Topic score.
- **Kjørbarhet og KI-kontroll er tenkt inn fra start.** FR-20 (Mock mode uten Key), FR-8 (Reference-sjekk som fjerner elementer som ikke finnes i kilden) og eksemplet «exactly one Generated item with a wrong page index» i Sample document gjør kjernen testbar uten nøkkel. FR-11 flytter retting av flervalg til kode i stedet for KI.
- **Ærlig scope.** Must/Should er merket per FR, byggerekkefølgen er gitt (§7.1), og kuttlinjen 30. november er fastsatt på forhånd. §7.3 og §6 sier hva som er utelatt og hvorfor.

## 3. Oversikt per dimensjon

| Dimensjon | Vurdering | Kort begrunnelse |
|---|---|---|
| Beslutningsklarhet | sterk | Valg er datert og begrunnet (flervalg-retting i kode, Exam-svar teller, kuttlinje). Kun to åpne spørsmål, begge reelt åpne. |
| Substans | sterk | Konkrete terskler i NFR-ene (15 minutter, 360 px, 2 minutter). Persona-ene Ida og Jonas styrer faktiske valg (FR-20, UJ-5). |
| Strategisk sammenheng | sterk | Tese, SM-er og motmål henger sammen. Se 4.1 om at kuttlinjen berører selve tesen. |
| Testbarhet | god | De fleste FR-er har målbare konsekvenser. Svakest er kvalitet på KI-innhold og KI-retting, samt noen tall som mangler (4.2, 4.5). |
| Scope og avgrensning | god | Utelatelser er eksplisitte, men Must er stort i forhold til tiden som er igjen (4.1). |
| Brukbarhet for neste fase | sterk | Kontinuerlige FR-IDer 1–25, UJ-1 til UJ-5 med navngitt hovedperson, glossar brukt konsekvent, indeks stemmer med inline-tagger. |
| Formtilpasning | sterk | Én rolle, webapp, UJ-er og FR-er i passe detaljnivå. Litt tett (ca. 5000 ord), men oversiktlig. |

## 4. Viktigste forbedringer

### 4.1 Must-listen er stor, og kuttlinjen dekker bare siste trinn
- **Alvorlighet:** høy
- **Hvor:** §7.1 «Cut line: if step 2 is not done by 30 November 2026, FR-16 and FR-17 move to Should»
- **Problem og hvorfor det betyr noe:** Must er 18 FR-er pluss seks NFR-er (innlogging, opplasting, uttrekk med Location, fem typer generert innhold, Reference-sjekk, bakgrunnsjobb, to rettemåter, Retry, Review, Topic score, Mock mode), med levering 7. desember. Trinn 1 (kjerneløkken) har ingen dato, så forsinkelse oppdages først 30. november. Kuttlinjen fjerner også FR-16/17, som er en del av tesen i §1 og av SM-4 og UJ-3. Det står ikke hva som endres i resten av PRD-en når linjen utløses.
- **Forslag:** Legg inn en dato for trinn 1, og velg en reserve-kutt som ikke rammer tesen, for eksempel: «Hvis trinn 1 ikke er ferdig og testet innen 20. november, flyttes FR-24 og baksiden av FR-9 (generering som fortsetter etter at brukeren forlater siden) til Should; generering kjøres da i selve forespørselen.» Skriv også: «Hvis FR-16/17 kuttes, utgår SM-4 og UJ-3 settes til Should.»

### 4.2 Ingen kontroll av innholdskvalitet eller feil KI-retting i Real mode
- **Alvorlighet:** medium
- **Hvor:** FR-8 «It does not judge whether the content is correct», FR-12, NFR-5 «a fixed set of the Author's own lecture notes … is the test material for judging Summaries and Questions»
- **Problem og hvorfor det betyr noe:** Reference-sjekken viser at sitatet finnes, ikke at spørsmålet er godt eller at fritekstsvaret er rettet riktig. Feil retting gir feil Topic score og feil Weak topics, og SM-4 bygger på dem. «Not graded» dekker bare at rettingen feiler, ikke at den er feil.
- **Forslag:** Legg til en konsekvens i FR-12: «Studenten kan overstyre Grade for sitt eget svar; overstyringen merkes og brukes i Topic score.» Gjør NFR-5 etterprøvbart: «For ett fast notat på 10–20 sider vurderer Author 15 Questions mot kilden. Minst 12 skal være riktige og besvarbare; resultatet skrives ned.» Husk at Mock mode bare tester flyten (addendumet sier det selv).

### 4.3 Kostnad og bruksgrenser i Real mode mangler
- **Alvorlighet:** medium
- **Hvor:** FR-21 (Key), FR-9 (retry), FR-7 (regenerer Summary), FR-19 (ny forklaring), FR-25
- **Problem og hvorfor det betyr noe:** Gjenforsøk, regenerering og «make a new one» kan gjentas uten grense mot en gratis-tier, og Hosted instance bruker Authors egen Key. Rate-limit (429) fra leverandøren nevnes ikke som egen feiltype.
- **Forslag:** Ny konsekvens i FR-9: «Når AI provider svarer med rate limit, vises en melding om å vente, og Source får status failed uten delvis Study material.» Legg til en NFR: «Maks N genereringskall per Student per dag; ved overskridelse vises melding og ingen kall sendes.» Test i Mock mode.

### 4.4 Mange `[ASSUMPTION]` i et dokument med status final
- **Alvorlighet:** medium
- **Hvor:** §10 og inline-tagger (omtrent 40)
- **Problem og hvorfor det betyr noe:** Tagene blander ting Author allerede har bestemt («email and password», «three Detail levels») med startverdier som skal testes («20 Answers», «60%»). Da vet ikke arkitektur og stories hva som er låst. Siden Author er eneste beslutningstaker, kan mange av dem bekreftes nå.
- **Forslag:** Fjern taggen på beslutninger og skriv «Decided» i teksten. Behold taggen kun for verdier som skal kalibreres, og knytt dem til en test, for eksempel: «Terskelen 60 % justeres etter første uke med egne data (SM-1).»

### 4.5 Små hull i testbarhet og konsistens
- **Alvorlighet:** lav
- **Hvor:** FR-15 «up to a maximum interval»; FR-16 «updates when a Quiz ends» mot FR-10 «abandoned Quiz … still count»; FR-14
- **Problem og hvorfor det betyr noe:** Maksimalt intervall har ingen verdi, så testen kan ikke skrives. Det er uklart når Topic score oppdateres hvis Quizen aldri avsluttes. FR-14 har bare ett testpunkt, og FR-3, 4, 6, 9, 14 og 21 sier ikke hvilken UJ de realiserer.
- **Forslag:** «Intervallet etter Good vokser for hver Good på rad (for eksempel 1, 3, 7 dager) og er aldri over 180 dager.» «Topic score oppdateres når et Answer lagres.» Legg til «Realizes UJ-x» der det finnes en kobling.

## 5. Mekaniske funn

- FR-IDer 1–25, UJ-1–5, SM-1–4 og SM-C1/C2 er unike og sammenhengende. Krysshenvisninger løser seg. FR-23 til FR-25 står utenfor tallrekkefølgen i dokumentet, men det er greit fordi IDene er stabile.
- Assumptions-indeksen stemmer med de inline taggene (noen er slått sammen i indeksen).
- Glossaret brukes konsekvent. Statusene «generating, ready, failed» (FR-9) og «Detail level» er brukt som begreper, men «Source status» er ikke definert i glossaret. Mindre sak.

## 6. Før dere går videre

**Må avklares før UX, arkitektur og epics:**
- Dato for trinn 1 og eventuell reserve-kutt (4.1).
- Om bakgrunnsjobb i FR-9 er et krav eller en forbedring. Det styrer arkitekturen.
- Valg av AI provider i Real mode (åpent spørsmål 2). Det styrer kostnadsgrenser (4.3).

**Kan vente:** valg av Leitner eller SuperMemo-2 (addendumet sier at begge oppfyller FR-15), bilder/OCR og gamle eksamensoppgaver.

**Oppfølging av product brief-tilbakemeldingen: ja.** Testbare suksesskriterier (SM-2), Mock mode og `.env.example` (FR-20/21), sidegrense (FR-3), trinnvis bygging (§7.1) og en utvidelse med egen logikk (Retry, Topic score, Review) er alle fulgt opp. Valg av leverandør er fortsatt åpent.

## 7. Refleksjonsspørsmål

1. Mange av parameterne i PRD-en (60 %, 20 svar, 15 minutter, 90 %) kom trolig fra KI-forslag. Hvilke har dere bevisst valgt selv, og hvordan vil dere finne ut om de er riktige?
2. Hvordan vil dere avgjøre om en Question eller et fritekstsvar som KI-en har laget eller rettet er riktig, når Reference-sjekken bare bekrefter at sitatet finnes?

_Vurdert mot kvalitetsrubrikken i bmad-prd. Dette er veiledning, ikke sensur._
