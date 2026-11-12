# UX: ti designkonsepter

## 2026-11-09 kl. 20:07 — Mathias Bråten

### Oppgave
Mathias kjørte `/bmad-ux` og ba om at alle sidene i appen skisseres i ti ulike designkonsepter, med bred kreativ variasjon. Det viktigste er at det er oversiktlig. Impeccable-skillen skulle brukes, med ti subagenter i parallell, og alt skulle settes sammen. Han ville ikke ha spørsmål før han har sett konseptene.

### Plan
- **UX-kjøring:** ny bmad-ux-kjøring (Create) i `_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/`, med memlog. Kjøringen fra 5. november er kilde.
- **Kartlegging:** én agent laget `PRODUCT.md` (Impeccable) og `.working/concept-brief.md` med 12 sider, 12 dialoger og felles norsk eksempelinnhold.
- **Retninger:** Impeccables retningsrunde (`concept-seed`, seed:be346f5cdddd14ea) tildelte DNT-merkingen blant sju forankrede retninger. Av seks katalogutfordrere bygges tre, og tre er avvist med disiplinen overført. Alt står i `.working/concepts/directions.md`.
- **Felles verktøy:**
  - visningen i `.working/concepts/_viewer/`;
  - agentinstruksene i `.working/concept-agent-instructions.md`;
  - oversiktssiden `.working/concepts/index.html`;
  - et WebKit-skjermbildeverktøy med batch-skript, kopiert til `.working/tools/`.
- **Bygging:** ti konseptagenter i parallell, én per retning.

### Resultat
- **Ferdig:**
  - `PRODUCT.md` i prosjektroten, som utkast der utledede fakta er merket «inferred»;
  - concept-brief og directions;
  - visningen og agentinstruksene;
  - oversiktssiden, som fylles med data når konseptene er ferdige.
  Visningen og skjermbildeverktøyet er testet.
- **Ikke ferdig: selve konseptene.**
  - Agentene ble stoppet to ganger av bruksgrensen før de rakk å skrive sider. Bare Impeccables referansebilder ligger i `ref/` for 03–05.
  - Øktgrensen nullstilles kl. 18:50, og da kan agentene fortsette der de stoppet.
  - Skjermbildeverktøyet ligger i økta sin scratchpad. I en ny økt bygges det fra `.working/tools/render.swift` med `swiftc -O render.swift -o render`, og stien i agentinstruksene oppdateres.
- Memlog er oppdatert med bestillingen, retningsrunden og stoppet.
- `PRODUCT.md` og UX-mappa for 2026-11-09 er ikke committet.

### Åpne punkter
- Fullfør de ti konseptene etter kl. 18:50, ta sammenligningsbilder og fyll oversiktssiden. Deretter velger Mathias ett til tre konsepter.
- Bekreft eller rett «(inferred)»-faktaene i `PRODUCT.md`, som ble skrevet uten intervju.
- Avklar om ønsket om lyse farger fra 5. november fortsatt gjelder.

## 2026-11-11 kl. 07:36 — Mathias Bråten

### Oppgave
Fortsette UX-kjøringen, men med fem designkonsepter i stedet for ti. Alle sidene skal skisseres, med bred kreativ variasjon og oversiktlighet som viktigste kriterium. Impeccable brukes, subagentene jobber parallelt, og alt settes sammen uten spørsmål underveis.

### Plan
- Beholde de fem retningene som er lengst fra hverandre og som hadde mest påbegynt arbeid:
  - 04 Gule skilt (skilting);
  - 06 Studievarselet (Yr);
  - 07 Kompendiet (trykksak);
  - 08 Kortboksen (fysiske kort);
  - 10 Mønsteret (strikkediagram).
- Parkere 01 Merket løype, 02 Linjekartet, 03 Fliser, 05 Avgangstavla og 09 Sjøkartet. Mappene deres står urørt.
- Kompilere skjermbildeverktøyet inn i `.working/tools/render` og la agentinstruksene peke dit.
- Fem konseptagenter i parallell som fortsetter fra `parts/` i hver sin mappe.
- Ta sammenligningsbilder og fylle oversiktssiden fra hvert konsepts `notes.md`.

### Resultat
- **De fem konseptene er ferdige.** Hvert har alle 24 skjermene (P01–P12 og D01–D12) i lyst og mørkt tema og på desktop, nettbrett og mobil, med `notes.md` og skjermbilder i `shots/`. Agentene renderet i to runder og kjørte `impeccable detect`. Gjenstående funn er vurdert som villet eller falske positiver og står i hvert konsepts notes.md.
- **Avvik og risiko fra notatene:**
  - Kortboksen har en venstre skinn på desktop i stedet for toppfeltet, med de samme tre målene.
  - Mønsteret har syntetiske stand-in-tekster for spørsmål 6–10 i P07, for 19 av de 20 eksamensspørsmålene i P11 og for fire av «Vis kilde»-sitatene.
  - Kompendiet mangler et overflyt-valg når det er mange fag.
- **Sammenligningsbilder:** 240 stykker (24 skjermer × desktop og mobil × 5 konsepter) i `<konsept>/shots/compare/`. `tools/shoot-all.sh` tar nå valgfrie konseptmapper som argumenter.
- **Oversiktssiden** `.working/concepts/index.html` er skalert til fem konsepter og fylt med idé, signaturgrep, navigasjon, skrift, tetthet, risiko og farger. Seksjonen «Fra ti til fem» forklarer utvalget. Siden er renderet og kontrollert.
- Memlog er oppdatert med byttet til fem, verktøyflyttingen og ferdigstillingen.
- Lukket åpent punkt: konseptene er ferdige og satt sammen.
- Konseptfilene, `PRODUCT.md` og UX-mappa er ikke committet.

### Åpne punkter
- Mathias velger ett til tre av de fem konseptene, gjerne med elementer fra andre. Deretter detaljeres valget i bmad-ux til DESIGN.md og EXPERIENCE.md.

### Fortsettelse kl. 21:26: runde 3

**Oppgave:** Mathias skrev beslutningene sine i `decisions.md` og ba om fem nye design basert på dem:
- 06 Studievarselet er hoveddesignet og skal utvikles videre, med god oversikt over fagene;
- lån fra de andre konseptene, særlig neste steg-feltet fra 04 Gule skilt;
- uttrykket skal være voksent, for studenter fra 20 år og oppover.

**Plan:**
- Gjorde om `decisions.md`, som var opprettet som en tom mappe, til en fil med mal.
- Førte beslutningene inn i memloggen.
- Skrev bestillingen `.working/runde-3/brief.md`. Den har felles regler for oversikt over fagene, ett neste steg-felt per side og et voksent uttrykk, og den beskriver fem varianter.
- Fem agenter i parallell. De ble stoppet to ganger av bruksgrensen og fortsatte der de slapp.

**Resultat:**
- **Fem ferdige varianter** i `.working/runde-3/`. Alle har 24 skjermer, `notes.md` og skjermbilder:
  - 11 Klarvær: ryddet og luftig;
  - 12 Veiviseren: + Gule skilt, i dempet oker;
  - 13 Registeret: + Kompendiet, med dempede fagfarger;
  - 14 Fagskinnen: + Kortboksen, med venstre fagskinne;
  - 15 Fagtavla: oversiktstabell, nøktern.
- 240 sammenligningsbilder.
- Oversiktssiden `.working/runde-3/index.html` er fylt inn.
- **Publisert privat:**
  - runde 3: https://claude.ai/artifact/18UHcWBnhAyLKGEyZVg2CX;
  - runde 2: https://claude.ai/artifact/R5hH5UYJS9evx14MCSZLzH.
  Lenkene står også i `decisions.md`.
- Lukket åpent punkt: Mathias valgte Studievarselet som hoveddesign.
- UX-mappa og `PRODUCT.md` er ikke committet.

**Åpne punkter:**
- Mathias velger én av de fem variantene i runde 3, gjerne med detaljer fra de andre, og skriver valget i `decisions.md`. Deretter kommer DESIGN.md og EXPERIENCE.md.
- Mestring per fag (snitt over temaene), som flere varianter viser, er et nytt begrep som må avklares mot PRD-en.

## 2026-11-12 kl. 08:16 — Mathias Bråten

### Oppgave
Fullføre bmad-ux med 14 Fagskinnen som valgt retning: skrive DESIGN.md og EXPERIENCE.md, avklare de åpne punktene og sette dokumentene til endelige. Underveis la Mathias til et nytt krav i `decisions.md`: appen skal også ha quiz, «test deg selv» og sammendrag av kapitler, ordnet pent og oversiktlig.

### Plan
- Destillere de to dokumentene fra 14 Fagskinnen, memloggen og PRD-en.
- Avklare punktene som blokkerte fasen, ett om gangen, med Mathias.
- Bygge inn det nye kravet i skissen (P05 Tema og P04 Fagoversikt) og i dokumentene.
- Hoppe over Reviewer Gate (Mathias valgte det), sjekke at alle skjermene er dekket og kopiere skissen til `mockups/`.
- Gå gjennom språk og struktur med bmad-review (linsene structure og prose), rette uten å endre beslutninger, og sette status til final.

### Resultat
- **Beslutninger (alle i `.memlog.md`):**
  - Fagskinnen erstatter beslutningene fra 5. november: fagskinne i stedet for toppstolpe på desktop, hvit arbeidsflate og kobber som eneste aksent.
  - Kantene på skjemafelt og knapper får en mørkere farge, `line-control` (#728A90 lys, #5E7A81 mørk). Den oppfyller 3:1 etter WCAG 1.4.11.
  - Mestring per fag er snittet av temaene som har nok svar.
  - «Test deg selv» betyr både kort og prøveeksamen.
  - Tema-siden får fire faner: Sammendrag (standard), Quiz (med quizhistorikk), Test deg selv og Kilder.
  - Prioriteten i neste steg-feltet på Hjem og Fagoversikt er: dagens kort, så svake temaer, så et tema uten kilder, så en rolig melding.
- **Skisse:** P05 er bygd om med faner. På P04 viser feltet nå «Repeter kortene i Databaser», og knappen «Øv på svake temaer (2)» er lagt til. Begge sidene har nye alternative tilstander. Skissen ligger i `ux-Prosjekt A-2026-11-09/mockups/14-fagskinnen.html`, og runde 3 er publisert på nytt (https://claude.ai/artifact/18UHcWBnhAyLKGEyZVg2CX).
- **Dokumentene** `DESIGN.md` og `EXPERIENCE.md` har `status: final` og er datert 2026-11-12.
  - Strukturgjennomgangen fjernet historikken («changed from 2026-11-05») og slo sammen dubletter. Navnebyttene er ført i memloggen.
  - Språkgjennomgangen gjorde om lag 40 setningsrettelser og ryddet begrepene, for eksempel review i stedet for repeat.
  - Ingen beslutning er endret, og alle de 29 `[ASSUMPTION]`-merkene står igjen.
- Lukker tre åpne punkter: valget av variant i runde 3, mestring per fag og de lyse fargene.
- UX-mappa og `PRODUCT.md` er ikke committet.

### Åpne punkter
- PRD-en bør ta inn det nye fra UX: mestring per fag (snitt av temaene), fanene på Tema-siden, quizhistorikken og prioriteten i neste steg-feltet.
- Gå gjennom de 29 utsatte UX-antakelsene (3 i DESIGN.md, 26 i EXPERIENCE.md) når skjermene bygges.
- Neste steg: bmad-architecture, deretter bmad-create-epics-and-stories.
