---
title: "Product Brief: AI Study Buddy"
status: draft
created: 2026-09-15
updated: 2026-09-15
---

# Product Brief: AI Study Buddy

## Sammendrag

AI Study Buddy er en enkel, responsiv web-app som lar en student laste opp egne pensumkilder — forelesningsnotater, lysbilder og pensumtekster som PDF eller ren maskinskrevet tekst — og få dem omsatt til sammendrag, flashcards, quiz-spørsmål/svar, nøkkelbegreper og referansepekere, organisert per kurs og kapittel/tema. Den bygges av en enkeltstudent som en skoleoppgave med levering 7. desember 2026, og er samtidig ment å faktisk brukes gjennom hele semesteret — ikke bare fungere som en demo for innlevering.

Problemet den løser er velkjent for de fleste studenter: pensum bearbeides i dag manuelt og usystematisk — lest på nytt, skrevet av for hånd, med ad hoc-spørsmål til ChatGPT eller Claude når noe er uklart — uten at noe av dette blir til gjenbrukbart repetisjonsmateriale. Løsningen henter det studiematerialet som trengs for aktiv gjenkalling direkte ut av det studenten allerede laster opp, fortløpende gjennom semesteret, ikke bare rett før eksamen.

Prosjektet konkurrerer bevisst ikke med etablerte verktøy som Quizlet, StudyFetch eller Quizgecko — funksjonelt overlapper det med det de allerede tilbyr. Verdien ligger i at det er et eget, gratis verktøy skreddersydd til egen studiehverdag, og i at selve byggingen er læringsmålet i oppgaven. Suksess måles først og fremst i om studenten faktisk bruker appen løpende fram til innlevering, ikke bare i om prototypen fungerer teknisk.

## Problemet

Å bearbeide pensum til noe man faktisk husker på eksamen tar tid — og de fleste studenter, inkludert brukeren selv, gjør det manuelt og usystematisk i dag. Notater leses på nytt og skrives av for hånd, og når noe er uklart, spørres ChatGPT eller Claude ad hoc for å forstå et konsept. Men disse samtalene forsvinner inn i en chat-logg; de blir aldri til noe man kan repetere, terpe på eller teste seg selv på senere.

Dette gjelder gjennom hele semesteret, ikke bare rett før eksamen. Etter hver ny pensumbolk (et kapittel, en forelesning) trengs en måte å omsette rå notater til noe brukbart for repetisjon på. Når eksamen nærmer seg og pensum har vokst til hundrevis av sider, blir jobben med å strukturere alt overveldende nok til at mange ikke gjør det systematisk — de leser i stedet passivt på nytt, en kjent ineffektiv strategi sammenlignet med aktiv gjenkalling (flashcards, quiz).

Det finnes også et sekundært problem: studenter bruker allerede generelle AI-verktøy i studiehverdagen, men tilfeldig og ustrukturert — de lærer ikke noe overførbart om *hvordan* AI faktisk bearbeider tekst, bare at "det funket for dette ene spørsmålet."

## Løsningen

En web-app der studenten laster opp sine egne pensumkilder — forelesningsnotater, lysbilder, pensumtekster som PDF eller ren maskinskrevet tekst — sammen med enkel kontekst (kurskode/emne, kapittel/tema, ønsket detaljnivå på sammendrag, språk/preferanser). Fra dette genererer appen, uavhengig av hvor stor teksten er:

- **Sammendrag** av opplastet materiale, med justerbar detaljgrad
- **Flashcards** for aktiv gjenkalling
- **Quiz-spørsmål og -svar** — både korte og åpne oppgaveformater — for egentesting og eksamensforberedelse
- **Nøkkelbegreper** trukket ut fra materialet
- **Referansepekere** tilbake til kilde/side

Alt organiseres per kurs og kapittel/tema, slik at studenten enkelt kan skille hva som hører til hvor og bruke verktøyet fortløpende gjennom semesteret — ikke bare som en engangs eksamens-crammer. Innlogging lar studenten lagre opplastet materiale og generert innhold organisert på denne måten, og komme tilbake til det senere for repetisjon.

## Hva som gjør dette annerledes

Dette prosjektet konkurrerer ikke med etablerte verktøy som Quizlet, StudyFetch eller Quizgecko, og har ingen ambisjon om å utkonkurrere dem i markedet. Funksjonelt overlapper det med det disse allerede tilbyr (opplastede notater → sammendrag/flashcards/quiz).

Det som gjør dette prosjektet verdt å bygge er:

- **Eget verktøy uten abonnement eller begrensninger** — skreddersydd til egen studiehverdag, uten betalingsmurer eller fremmed produktutforming.
- **Strukturert rundt egne kurs og kapitler/temaer**, slik brukeren faktisk organiserer pensumet sitt, fremfor en generisk mal.
- **Selve byggingen er formålet.** Dette er en skoleoppgave der læringsmålet er å faktisk bygge og forstå en AI-drevet applikasjon end-to-end — ikke å etablere et konkurransedyktig produkt i et allerede trangt marked.

## Hvem dette er for

*Primærbruker:* brukeren selv — en aktiv student som i dag prosesserer pensum manuelt (lesing + håndskrevne sammendrag) og bruker ChatGPT/Claude ad hoc for forståelse, men uten noe system for repetisjon eller egentesting. Appen skal faktisk brukes gjennom semesteret, kapittel for kapittel — ikke bare fungere som en skoleprosjekt-demo.

*Sekundær/tiltenkt bruker:* studenter generelt, uavhengig av fag. Appen designes fag-agnostisk, men brukerens egen studiehverdag er referansepunktet for hva som faktisk er nyttig.

## Suksesskriterier

**Personlig bruk (det viktigste kriteriet):** Appen regnes som vellykket hvis den faktisk brukes løpende gjennom semesteret — for flere fag, over tid — til å bearbeide pensum, og ikke bare fungerer som en engangs-demo bygget for innlevering. Reell bruk før 7. desember er selve beviset på at løsningen er nyttig, ikke bare funksjonell.

**Leveransekriterier (skoleoppgaven):** En fungerende prototype som dekker det oppgaveteksten spesifiserer — data inn (opplastede forelesningsnotater/lysbilder/pensum, kurskode, detaljnivå, språk) og data ut (sammendrag, flashcards, quiz-spørsmål/svar, nøkkelbegreper, referansepekere) — samt en skriftlig rapport som blant annet reflekterer over hvordan AI kan brukes til tekstbehandling.

## Omfang

**Med i første versjon (MVP, til 7. desember):**
- Opplasting av pensumkilder som PDF eller ren maskinskrevet tekst (ikke bilder/håndskrift)
- Enkel kontekst per opplasting: kurskode/emne, kapittel/tema, ønsket detaljnivå, språk
- Generering av: sammendrag, flashcards, quiz-spørsmål/svar (korte og åpne formater), nøkkelbegreper, referansepekere til kilde/side
- Organisering av innhold per kurs og kapittel/tema
- Innlogging og lagring, slik at studenten kan komme tilbake til tidligere opplastinger og generert innhold
- Responsiv web-app som fungerer på mobil, nettbrett og desktop i nettleser (ingen native apper)

**Bevisst utenfor omfang:**
- Native mobil-, iPad- eller desktop-apper
- Opplasting av bilder/håndskrevne notater (OCR) — mulig senere utvidelse
- AI-generert fasit på øvingsoppgaver, verifisert mot nettet
- Betaling/kjøp
- Deling eller samarbeid mellom studenter (flerbrukerfunksjoner utover egen innlogging)
