# Tilbakemelding på product brief

| | |
|---|---|
| **Gruppe** | G49 – G49-braten |
| **Product brief** | `brief.md` med `addendum.md` (commit 04c2c3f) |
| **Tilbakemelding fra** | Faglærer i IBE160 (utarbeidet med KI-støtte) |
| **Dato** | 2026-10-06 |

## Samlet vurdering

- **Godt utgangspunkt med justeringer.** Gruppen kan gå videre og innarbeide punktene under.

**Det som er bra:**

1. Briefen er ærlig og gjennomtenkt. Dere sier tydelig at AI Study Buddy ikke skal konkurrere med Quizlet, StudyFetch og Quizgecko, og addendumet viser bevisste avgrensninger: nettverifiserte fasitsvar er droppet, fire plattformer er redusert til én responsiv webapp, og OCR er utsatt.
2. Problemet er konkret og personlig forankret: samtaler med ChatGPT og Claude «forsvinner inn i en chat-logg» og blir aldri til repetisjonsmateriale. Organisering per kurs og kapittel/tema gjør appen nyttig gjennom hele semesteret.

**De viktigste endringene:**

1. Suksesskriteriene kan ikke testes. «Appen brukes løpende gjennom semesteret» er et godt personlig mål, men sensor kan ikke etterprøve det. Legg til funksjonelle kriterier, for eksempel «en opplastet PDF på 20 sider gir et sammendrag, minst 10 flashcards og en quiz der hvert spørsmål viser sidetall i kilden».
2. Lag en plan for språkmodellen: hvilken modell, hvor nøkkelen ligger, og en testmodus med mock-svar slik at sensor kan kjøre appen uten deres nøkkel. Addendumet lister dette som et åpent beslutningspunkt, men det påvirker kjørbarheten så mye at retningen bør bestemmes nå.
3. Juster løftet om å generere innhold «uavhengig av hvor stor teksten er». Store dokumenter går ut over modellens kontekstvindu og krever oppdeling. Sett en øvre grense i v1, for eksempel antall sider per opplasting.

## Vanskelighetsgrad og gjennomførbarhet

### Vurdert vanskelighetsgrad

- **Enkel**

**Sammenlignbart med:** 1) AI Study Buddy (enkel). Briefen følger forslaget nesten punkt for punkt, med innlogging og organisering per kurs og kapittel i tillegg.

**Begrunnelse:**

| Faktor | Nivå (lav / middels / høy) | Kommentar |
|---|---|---|
| Domenelogikk – hvor mange og hvor kompliserte regler og beregninger må stemme? | Lav | Lite egen forretningslogikk utover organisering og eventuell quizretting. Det meste styres av språkmodellen. |
| Datamodell – antall entiteter og relasjoner mellom dem | Middels | Bruker, kurs, kapittel/tema, opplasting, og generert innhold av fem typer (sammendrag, flashcards, quiz, begreper, referanser). |
| Brukere, roller og innlogging | Middels | Innlogging med lagring per bruker. Én rolle, men innlogging må gjøres trygt. |
| KI-funksjonalitet i appen, f.eks. kall til språkmodell, prompts i koden og håndtering av usikre svar | Middels | Fem typer generert innhold med hver sin prompt og strukturert utdata. Referansepekere til side krever at sidetall følger teksten gjennom hele kjeden. |
| Integrasjoner og eksterne tjenester, f.eks. API-er, betaling og e-post | Middels | Avhengig av LLM-API med nøkkel og kostnad, eller lokal modell. |
| Sanntid, samtidighet eller flere brukere som påvirker hverandre | Lav | Ingen sanntid eller deling. |
| Filhåndtering, f.eks. opplasting, PDF-lesing og eksport | Middels | PDF-tekstuttrekk med sidetall. Lysbilder og tabeller gir ofte rotete tekst, som addendumet riktig påpeker. |
| Sikkerhet og personvern | Lav–middels | Pensummateriale sendes til en ekstern tjeneste. Bruk testmateriale uten opphavsrettslige problemer i repoet. |

**Hva vanskelighetsgraden betyr for dere:**

- _Enkel:_ Et enkelt prosjekt gir stor sjanse for å bli ferdig. Vanskelighetsgraden inngår likevel i vurderingen, så for å nå helt opp må dere vise mer i gjennomføringen. Det betyr særlig et gjennomarbeidet design, grundig testing, en tydelig dokumentert prosess og en README som virker. Når du arbeider alene, er et enkelt prosjekt et fornuftig valg. Bruk tiden på kvalitet heller enn flere funksjoner.

### Gjennomførbarhet med BMAD og Claude Code

Dere skal planlegge med BMAD (product brief → PRD → arkitektur → epics og stories) og implementere med Claude Code. Vurderingen under tar hensyn til at det må være tid til hele denne flyten, og til testing, retting og README til slutt.

| Spørsmål | Vurdering (OK / risiko / stor risiko) | Kommentar |
|---|---|---|
| **Tid og omfang** – kan v1 realistisk bli ferdig og stabil i løpet av semesteret, med tid til flere iterasjoner? | OK | Omfanget passer for én person, så lenge filstørrelsen begrenses og de fem utdatatypene bygges trinnvis. Kom raskt i gang med PRD. |
| **BMAD-flyten** – er briefen konkret nok til at PRD, arkitektur og stories kan lages uten store hull, og blir det overkommelig mange stories? | OK | Data inn og ut er tydelig listet, og addendumet gir arkitekturfasen et godt utgangspunkt. |
| **Egnet for Claude Code** – bruker løsningen en vanlig, godt dokumentert teknologistakk som Claude Code håndterer godt, eller krever den nisjeteknologi, spesialmaskinvare eller mye manuell konfigurasjon? | OK | En webapp med filopplasting, innlogging og LLM-API er godt dokumentert. |
| **Kontroll på KI-ens arbeid** – kan gruppen selv avgjøre om koden gjør det riktige? Krever domenet kunnskap gruppen ikke har, f.eks. avanserte beregninger eller fagregler, så er det vanskelig å kvalitetssikre. | Risiko | Koden kan du kontrollere, men kvaliteten på sammendrag og quiz er vanskeligere. Bruk egne forelesningsnotater du kjenner godt som fast testmateriale, og sjekk særlig at referansepekerne viser til riktig side. |
| **Testbarhet** – finnes det tydelige regler og forventede resultater som tester kan skrives mot? | Risiko | Organisering, innlogging og lagring kan testes godt. KI-delen må testes med mock-svar og kontroll av format. Suksesskriteriene i dag gir ingen testtilfeller. |
| **Kjørbar for sensor** – kan appen kjøres lokalt etter README, uten gruppens nøkler, betalte kontoer eller egen infrastruktur? | Stor risiko | Uten testmodus eller mock-svar kan ikke sensor prøve noen av kjernefunksjonene. |
| **Avhengigheter og kostnader** – krever løsningen betalte API-er, f.eks. språkmodeller, og finnes det en plan for kostnad, testmodus eller mock-data? | Risiko | Lokal modell vs. sky er åpent. Lokal modell fjerner kostnaden, men gjør oppsettet for sensor tyngre. Velg og begrunn. |

**Konklusjon om gjennomførbarhet:**

- **Gjennomførbart med justert omfang.** Se forslagene under.

**Forslag til justering av omfang eller vanskelighetsgrad:**

1. Bygg utdatatypene trinnvis: sammendrag og quiz først, deretter flashcards og nøkkelbegreper, og referansepekere til side til slutt. Sett en øvre grense for dokumentstørrelse i v1.
2. For å løfte prosjektet over «enkel» kan du vurdere én utvidelse som gir egen logikk, for eksempel at quizen rettes og at feil besvarte spørsmål samles for ny øving. Det gir også gode testtilfeller.

## Hvorfor product brief er viktig for mappen

Product brief er utgangspunktet for PRD, arkitektur, stories og til slutt koden. Del 1 av mappen vurderes blant annet på om sensor kan følge en sporbar vei fra plan til ferdig app. Den vurderes også på om appen gjør det dere har beskrevet, om den er testet, om den er godt designet, og om den kan kjøres etter README. Et uklart, for stort eller for lite brief gjør alt dette vanskeligere senere. Det er mye enklere å rette nå enn sent i semesteret.

## 1. Gjennomgang av briefens deler

| Del av brief | Status | Kommentar |
|---|---|---|
| Executive Summary – er det klart hva appen er, og hvilket problem den løser? | OK | Klart hva appen er, hvem som lager den og hvorfor. |
| The Problem – er problemet konkret, med reelle situasjoner og brukere? | OK | Konkret og personlig, med passiv gjenlesing og ad hoc KI-bruk som ikke blir til repetisjonsmateriale. |
| The Solution – beskriver løsningen brukeropplevelsen, ikke bare teknologi? | Juster | Godt beskrevet hva som genereres. Beskriv også hva brukeren gjør etterpå: tar quizen i appen, blar i flashcards, eller eksporterer? Fjern «uavhengig av hvor stor teksten er». |
| What Makes This Different – er vurderingen ærlig og realistisk? | OK | Svært ærlig og realistisk. |
| Who This Serves – er primærbrukerne tydelige, og vet vi hva de trenger? | OK | Primærbrukeren (deg selv som student) er konkret og gir et godt referansepunkt for design og testing. |
| Success Criteria – kan kriteriene faktisk sjekkes eller testes? | Endre | Personlig bruk kan ikke etterprøves av sensor, og leveransekriteriet gjentar bare oppgaveteksten. Legg til funksjonelle, testbare kriterier. |
| Scope – er det klart hva som er med i første versjon, og hva som ikke er det? | OK | Tydelig liste over hva som er med og ute. Legg til en grense for dokumentstørrelse. |
| Vision – henger visjonen sammen med resten uten å blåse opp omfanget? | Juster | Briefen mangler en egen visjonsdel. Addendumet nevner mobil og OCR som mulige utvidelser. Legg inn et kort avsnitt i briefen. |

## 2. Utgangspunkt for del 1 av mappen

Punktene følger kriteriene i sensorveiledningen for del 1. Vektene i parentes viser hvor mye hvert kriterium teller i del 1.

| Kriterium i del 1 | Hva briefen bør legge til rette for | Status | Kommentar |
|---|---|---|---|
| **1. Prosess og KI-styring** (30 %) | Brief som er presis nok til at PRD og stories kan bygges direkte på den, slik at krav kan spores fra brief til kode. | OK | Brief og addendum gir god sporbarhet. Legg gjerne planleggingsdokumentene i en egen mappe (for eksempel `_bmad-output/planning-artifacts/`) når PRD og arkitektur kommer. |
| **2. Funksjonalitet og omfang** (20 %) | Realistisk omfang for gruppen og semesteret: en tydelig kjerneflyt som kan bli ferdig og stabil, og nok innhold til å vise reell funksjonalitet. | OK | Realistisk for én person. Vurder én utvidelse med egen logikk, som foreslått over. |
| **3. Kvalitetssikring og testing** (15 %) | Suksesskriterier og funksjoner som er konkrete nok til å bli testtilfeller. | Endre | Suksesskriteriene må omformuleres før de kan bli testtilfeller. Planlegg mock-svar for KI-delen. |
| **4. Design og brukeropplevelse** (10 %) | Tydelige brukere og brukssituasjoner som designet kan bygges rundt, gjerne med de viktigste skjermbildene eller flytene skissert. | OK | Responsiv app for mobil, nettbrett og desktop er et tydelig designkrav. Skisser kurs-/kapitteloversikten og visningen av generert innhold. |
| **5. Kodekvalitet og arkitektur** (10 %) | Teknologivalg som er begrunnet og ikke mer komplekse enn appen trenger. | OK | Teknologivalg er riktig utsatt til arkitekturen. Samle LLM-kall i én modul, slik at mock-modus blir enkel. |
| **6. README og kjørbarhet** (10 %) | Løsning som andre kan kjøre lokalt uten betalte kontoer, og uten tilgang til gruppens egne tjenester og nøkler. | Endre | Avhengig av LLM-nøkkel eller lokal modell. Planlegg `.env.example`, testmodus og et eksempeldokument. |
| **7. Ryddighet i repoet** (5 %) | En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge. | Juster | Brief og addendum ligger i roten. Flytt dem til en dokumentasjonsmappe når flere planleggingsdokumenter kommer til, og hold API-nøkler utenfor repoet. |

## 3. Neste steg for gruppen

1. Legg til 4–6 funksjonelle, testbare suksesskriterier ved siden av målet om personlig bruk.
2. Velg retning for språkmodell (sky eller lokal), og beskriv testmodus med mock-svar og hvordan sensor setter inn egen nøkkel.
3. Sett en grense for dokumentstørrelse, prioriter utdatatypene i trinn og gå videre til PRD.

Oppdater product brief i repoet når dere har gjort endringene, slik at historikken viser hvordan planen utviklet seg. Det er en del av prosessen sensor ser etter.
