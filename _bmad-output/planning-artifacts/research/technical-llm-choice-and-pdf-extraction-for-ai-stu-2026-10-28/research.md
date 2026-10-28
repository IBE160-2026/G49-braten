---
title: 'technical research: LLM-valg og PDF-uttrekk for AI Study Buddy'
type: 'technical'
topic: 'LLM-valg og PDF-uttrekk for AI Study Buddy'
decision: 'Hvilken språkmodell-løsning og PDF-uttrekksløsning v1 av AI Study Buddy skal bygges på (solo, frist 2026-12-07, sensor må kunne kjøre appen uten forfatterens nøkkel)'
source: 'native run'
status: complete
claims_verified: 2
claims_unverified: 3
claims_disputed: 1
preset: 'standard'
validation: 'normal'
created: '2026-10-28'
updated: '2026-10-28'
---

# Technical research: LLM-valg og PDF-uttrekk for AI Study Buddy

**Beslutningen denne research-en støtter:** Hvilken språkmodell-løsning og hvilken PDF-uttrekksløsning v1 av AI Study Buddy skal bygges på. Prosjektet er solo, har frist 7. desember 2026, og sensor må kunne kjøre appen uten forfatterens nøkkel.

## Sammendrag

**Anbefaling:** Bygg et eget lag mellom appen og språkmodellen, med to leverandører bak: en **deterministisk mock-leverandør som er standard**, og en ekte leverandør du velger med en miljøvariabel og en nøkkel i `.env`. Hent ut PDF-tekst **side for side i egen kode** og merk hver side i teksten som sendes til modellen. Be modellen svare i strukturert JSON med sidetall og et ordrett sitat, og kontroller begge deler i koden før de vises.

De tre funnene som bærer anbefalingen:

1. **Kostnad avgjør ikke valget, nøkkeltilgang gjør.** Behandling av én 20-siders PDF koster under ca. 2 cent (under 0,02 USD) på alle de billige betalte modellene, regnet med 18k tokens inn og 5k ut [9][10][13][14]. Det vanskelige er å la sensor kjøre appen uten betalt nøkkel. Blant de store leverandørene har bare Gemini et bekreftet gratisnivå med eget API [10]; det mangler offisielle tall for grensene [11], og innhold som sendes inn der kan brukes til å forbedre Googles produkter [10][12].
2. **Egen sideuttrekking er nødvendig, ikke bare mulig.** Claudes innebygde sidesitater (`page_location`) [2] kan ikke kombineres med strukturert JSON-utdata [2]. Sidehenvisninger må derfor komme fra sidemarkører i teksten du selv sender, og kontrolleres i koden.
3. **Kapasitet er ikke flaskehalsen.** Dagens Claude-modeller har 1M tokens kontekst [8]. Det som begrenser en sidegrense er tokens per minutt på gratisnivåer (Groq [15]; Gemini mangler offisielle tall [11]), og at Ollama som standard bruker bare 4k kontekst på en laptop med under 24 GiB [17].

**Største forbehold:** Flere tall som anbefalingen hviler på er ikke bekreftet av offisielle sider: gratisgrensene hos Gemini [11], Groq-gratisplanen [15] og kvaliteten på små lokale modeller på norsk (ingen treff). Kvaliteten på uttrekk fra forelesningslysbilder er heller ikke dokumentert med noen datert sammenligning. Se «Åpne spørsmål».

## A. Språkmodell

### A1. Sky eller lokal modell

- **Sky er det realistiske hovedvalget.** Billige skymodeller koster under 2 cent per PDF (se A2), mens lokale modeller krever oppsett hos både deg og sensor.
- **Lokal modell (Ollama) fungerer som valgfri tredje leverandør, ikke som standard.** Ollama støtter skjemastyrt utdata via `format`-parameteren [19]. Standard kontekstlengde er 4k tokens når VRAM er under 24 GiB (32k ved 24–48 GiB) [17]. En prompt på ca. 18k tokens blir derfor kuttet på en vanlig laptop med mindre kontekstlengden heves, noe som koster mer minne [17]. Gemma 4 finnes i størrelser fra 4,6 GB til 20 GB å laste ned, med 128k–256k kontekst [18].
- **Norsk kvalitet på små lokale modeller er ikke dokumentert.** Jeg fant ingen datert 2026-sammenligning av 7–14B-modeller på norsk sammendrag eller quizgenerering. Nærmeste kilde er NorEval fra 2025 (24 norske datasett, 19 åpne modeller), og jeg så ikke tall for Gemma eller Qwen3 [20]. Konfidens: lav.

### A2. Leverandører, priser og gratisnivåer

Priser per million tokens (inn/ut), hentet 2026-10-28. Alle er fra offisielle sider, lest via en oppsummerende nettleser; konfidens medium til høy.

| Leverandør og modell | Inn | Ut | Kommentar |
|---|---|---|---|
| Anthropic Haiku 5.5 | 0,10 USD | 0,50 USD | 1M kontekst; høyere pris over 100k tokens; batch 50 % rabatt [8][9] |
| Anthropic Sonnet 5.5 | 2 USD | 10 USD | [8][9] |
| Gemini 2.5 Flash-Lite | 0,10 USD | 0,40 USD | Har gratisnivå [10] |
| Gemini 2.5 Flash | 0,30 USD | 2,50 USD | Har gratisnivå [10] |
| OpenAI gpt-5-nano | 0,05 USD | 0,40 USD | Ingen gratisnivå oppgitt [13] |
| OpenAI gpt-5-mini | 0,25 USD | 2,00 USD | [13] |
| Groq gpt-oss-20b | 0,075 USD | 0,30 USD | 131k kontekst [14] |

**Kostnad per PDF** (antakelse: 18k tokens inn og 5k ut, ett kall; regnestykket er mitt, fra prislistene over):

| Modell | Regnestykke | Sum |
|---|---|---|
| Haiku 5.5 | 0,0018 + 0,0025 | ca. 0,004 USD |
| Gemini 2.5 Flash-Lite | 0,0018 + 0,0020 | ca. 0,004 USD |
| gpt-5-nano | 0,0009 + 0,0020 | ca. 0,003 USD |
| Groq gpt-oss-20b | 0,00135 + 0,0015 | ca. 0,003 USD |
| Sonnet 5.5 | 0,036 + 0,05 | ca. 0,09 USD |

Claudes nyere tokenizer gir omtrent 30 % flere tokens for samme tekst [9], så Haiku ender nær 0,005 USD. Tenkende modeller fakturerer tenketokens som utdata, og ingen kilde tallfestet hvor mye det øker kostnaden. Antakelsen om 18k tokens for 20 sider er ikke sourcet (se B3).

**Gratisnivåer (nøkkelen til sensor-spørsmålet):**

- **Anthropic og OpenAI:** Ingen gratis API-nivå ble funnet på prissidene og grensesidene som ble lest [9][13][36]. Fravær på en side beviser ikke at det ikke finnes kampanjekreditter. Konfidens: lav.
- **Gemini:** Gratisnivå finnes for Flash- og Flash-Lite-modellene [10]. Tallgrensene (forespørsler og tokens per minutt og dag) står ikke på de offisielle sidene lenger; de vises i AI Studio per prosjekt [11]. Tredjepartsblogger oppgir motstridende tall (for eksempel 15 mot 5 forespørsler per minutt) og er ikke brukt [11]. **På gratisnivået brukes innsendt innhold til å forbedre Googles produkter, og menneskelige vurderere kan lese det** [10][12]. Det betyr at pensumtekst bør ikke sendes dit uten at brukeren vet det.
- **Groq:** Siden som ble lest viser grenser for Developer-planen (gpt-oss-modellene: 30 forespørsler per minutt og 8K tokens per minutt) [15]. En prompt på ca. 18k tokens overstiger 8K per minutt og blir trolig avvist. Gratisplanens egne tall og kortkrav ble ikke hentet ut [15]. Konfidens: lav til medium.
- **OpenRouter `:free`-modeller:** 20 forespørsler per minutt og 50 per dag (1000 per dag hvis du har kjøpt kreditter for minst 10 USD) [16]. Den synlige listen over gratismodeller inneholdt ingen kjente chatmodeller, men visningen kan være ufullstendig [16].
- **Mistral:** Gratisgrensene ble ikke funnet; begge dokumentsidene ga 404.

### A3. Strukturert JSON-utdata og usikre svar

- **Alle tre store leverandørene har skjemastyrt utdata.** Anthropic har det generelt tilgjengelig via `output_config.format` og bruker begrenset dekoding, så formatfeil trenger ikke gjentakelser [3]. OpenAI har `json_schema` med `strict: true` [4]. Gemini godtar JSON-skjema [5]. Zod (JS) og Pydantic (Python) støttes av alle tre [3][4][5].
- **Begrensninger du må planlegge for:** Anthropic støtter ikke rekursive skjemaer, tallgrenser eller lengdegrenser på strenger [3]. Gemini ignorerer `minLength`, `maxLength` og `uniqueItems` uten feilmelding [5]. Anthropic kan svare med `refusal` eller `max_tokens`, og da kan utdata mangle eller være avkuttet [3]. Sjekk `stop_reason` før parsing.
- **Skjemaet garanterer form, ikke sannhet.** Googles dokumentasjon sier at utdata er syntaktisk gyldig, men at verdiene kan være feil [5].
- **Anthropics sidesitater kan ikke kombineres med strukturert utdata.** Slår du på begge, avvises forespørselen (400) fordi sitater må flettes inn i teksten [2]. Dette er kontrollert mot den offisielle dokumentasjonen (verified).
- **Forslag til sjekk av sidehenvisninger (min syntese, ikke en dokumentert praksis):** Be modellen oppgi sidetall og et ordrett sitat per spørsmål eller kort. Kontroller i koden at sidetallet var blant sidene som ble sendt, og at sitatet finnes i den siden. Fjern eller merk det som feiler. Forskning på siteringsverifikasjon bruker samme idé om ordrette sitater, men gjelder vitenskapelige referanser, ikke studiekort [37]. Konfidens: lav til medium.
- **Ikke funnet:** Noen primærkilde eller god ingeniørartikkel om hvordan flashcard- og quizgeneratorer håndterer hallusinasjoner eller viser sikkerhetsnivå i brukergrensesnittet.

### A4. Mock-modus og nøkkelhåndtering

- **Konfigurasjon og hemmeligheter hører i miljøvariabler, atskilt fra koden** (twelve-factor) [33]. Det støtter `.env` for nøkkel og et flagg for leverandør.
- **Innspilling og avspilling** er det vanlige mønsteret i testverktøy for LLM-apper: spill inn svar én gang med ekte nøkkel, lagre dem som JSON, og spill dem av uten nett og nøkkel. Nøkler fjernes fra filene [35]. Ulempen er at du må spille inn på nytt når prompten endres. Kildene er små og unge verktøy, sett bare via søkeutdrag. Konfidens: lav til medium.
- **Ingen standard `MOCK_LLM`-konvensjon ble funnet.** Å bruke en leverandørgrensesnitt-adapter med en mock-leverandør er min slutning fra mønstrene over, ikke en kanonisk kilde.
- **Nøkler ut av git:** GitHub skanner offentlige repoer for hemmeligheter gratis. Lekker en nøkkel, skal den kalles tilbake (rotert) umiddelbart [34].
- **Ikke funnet:** Offisiell veiledning for `.env.example` og README i LLM-apper som sensor skal kjøre, og dokumenterte mønstre for at en bruker limer inn egen nøkkel i appen.

## B. PDF-uttrekk

### B1. Biblioteker (versjon og lisens, sjekket 2026-10-28)

| Bibliotek | Nyeste versjon | Lisens | Sidevis tekst | Merknad |
|---|---|---|---|---|
| unpdf (JS) | 1.9.1 (19. okt.) | MIT | Ja, en streng per side som standard | Serverless-bygg av PDF.js; ikke sidebilder i serverless [22] |
| pdf.js (JS) | 6.4.299 (3. okt.) | Apache-2.0 | Ja (`getTextContent` per side, ikke verifisert) | Mozillas bibliotek [21] |
| pdf-parse (JS) | 2.4.5 | Apache-2.0 (2.x) | Ikke undersøkt | [23] |
| PyMuPDF (Python) | 2.0 (19. okt.) | AGPL-3.0 eller kommersiell (Artifex) | Ja (`page_chunks=True`) | Pymupdf4llm-koden er nå slått inn i pymupdf 2.x [24][25][26][27] |
| pypdf (Python) | 6.21.3 (27. okt.) | BSD-3-Clause | Ikke verifisert | Ingen tabelluttrekking [28][30] |
| pdfplumber (Python) | 0.11.10 (15. juni) | MIT | Ikke verifisert | Fikk 0 poeng på leserekkefølge i en liten syntetisk test [29][30] |

**PyMuPDF-lisensen** krever vurdering: AGPL kan kreve at kildekoden til en nettjeneste som bruker den deles. Dette ble bare bekreftet via repoet og søkeresultater, ikke Artifex' egen lisensside [26]. PyMuPDF 2.0 kom for ni dager siden, og saksbehandlingen etter utgivelsen ble ikke sjekket for feil [25]. Det kan finnes eldre veiledninger for 1.x som ikke passer.

### B2. Kvalitet på lysbilder, tabeller og figurer

Dette er svakt dokumentert. Jeg fant **ingen datert sammenligning av uttrekk fra forelesningslysbilder** de siste 12 månedene.

- Vanlige feil, bare fra forum- og hjelpesider (lav konfidens): rekkefølgen i filen avviker fra rekkefølgen på siden, så kolonner og sidefelt flettes sammen; gjentatte topp- og bunntekster havner i brødteksten; ligaturer og formler blir ødelagt; PowerPoint-eksporterte PDF-er kan ha manglende eller endret leserekkefølge [31].
- En liten, udatert og syntetisk test fra én forfatter (10 PDF-er laget med reportlab) rangerte PyMuPDF best på tabeller og leserekkefølge, og pypdf likt med PyMuPDF på ren tekst [30]. Lav vekt.
- Pymupdf4llm kan gjenkjenne topp- og bunntekst som bokstyper, men har ikke en dokumentert innstilling for å fjerne dem [27].
- **Konsekvens:** Test uttrekket på dine egne forelesningslysbilder før du velger bibliotek. Dette er et mål på appens kvalitet, ikke noe en kilde kan svare på.

### B3. Oppdeling, sidehenvisninger og sidegrense

- **Kapasitet:** Alle aktive Claude-modeller har 1M tokens kontekst og 128K maks utdata [8]. Ifølge Anthropic tilsvarer 1M tokens omtrent 555 000 ord på dagens tokenizer [8]. Et dokument på 100–300 sider kan derfor ligge i ett kall (min slutning). Map-reduce er ikke nødvendig for kapasitet i v1.
- **Innebygd PDF-støtte er et alternativ, men dyrere og med strengere grenser.** Claude: maks 32 MB; 600 sider per forespørsel, men 100 sider når kontekstvinduet er under 1M [1]. Hver side leses både som tekst (typisk 1 500–3 000 tokens) og som bilde, og bildet faktureres i tillegg [1]. En PDF på 20 sider blir dermed ca. 30 000–60 000 tokens bare i tekst, mot ca. 18 000 antatt med egen uttrekking. Gemini: opptil 50 MB eller 1000 sider, 258 tokens per side [6]. OpenAI: under 50 MB, ingen sidegrense oppgitt [7].
- **Sidehenvisninger:** Claude anbefaler logiske sidetall (fra PDF-leseren) i prompten [1]. For sidetall i JSON må du selv legge sidemarkører i teksten (for eksempel `[Side 12]`), siden sidesitatene ikke kan brukes sammen med JSON-skjema [2]. Jeg fant ingen offisiell kilde som beskriver sidemarkører, overlapp eller delområder.
- **Sidegrense i sammenlignbare produkter:** NotebookLM har ingen sidegrense, men maks 500 000 ord eller 200 MB per kilde [32]. Grensene til Quizlet, StudyFetch og ChatPDF ble ikke hentet.
- **Ingen kilde støtter et bestemt tall for v1.** Det som faktisk begrenser, er tokens per minutt på gratisnivåer (Groq 8K [15]; Gemini har ikke offisielle tall [11]) og Ollamas 4k-standard [17]. Se anbefalingene.

## Innsikter på tvers av dimensjonene

- **PDF-valget og JSON-valget henger sammen.** Fordi Claudes sidesitater utelukker strukturert utdata [2], må uttrekkingen skje i egen kode med sidemarkører. Det er trolig også billigere enn å sende PDF-en direkte [1] (min regning, se B3).
- **Sensor-kravet styrer arkitekturen mer enn pris eller kvalitet.** Når alle billige modeller koster øre [9][10][13][14], er det mock-modus og valgfri egen nøkkel som svarer på faglærerens «stor risiko».
- **Gratisnivåer og sidegrense kolliderer.** Tokens per minutt på gratisnivåer [15] og innholdsbruk hos Gemini [10] taler for en lav sidegrense og for at eksempeldokumentet i repoet er materiale uten opphavsrett, slik tilbakemeldingen også ber om.

## Motstridende bevis

Red team var ikke slått på i denne kjøringen (standard). Én uenighet er notert: tall for gratisnivået hos Gemini varierer sterkt mellom tredjepartskilder [11], og påstanden om at innebygd PDF-tekst ikke faktureres for Gemini 3 [6] er usikker (se «Åpne spørsmål»).

## Anbefalinger

| # | Anbefaling | Knyttes til | Konfidens |
|---|---|---|---|
| 1 | Lag et leverandørgrensesnitt for alle modellkall, i én modul. Ha en **mock-leverandør som standard** som returnerer innspilte, gyldige svar på et eksempeldokument. Velg ekte leverandør med en miljøvariabel og nøkkel i `.env`, og lever en `.env.example`. | Brief: suksesskriterier og README; PRD: krav om testmodus; arkitektur: LLM-modul | Medium. Mønsteret er en slutning fra kilder om testing [33][35] |
| 2 | Bruk en billig skymodell til din egen utvikling (for eksempel Haiku 5.5 eller Gemini Flash-Lite, under 1 cent per PDF [9][10]). Behandle lokal Ollama og Gemini gratisnøkkel som valgfrie leverandører, ikke som krav. | Arkitektur: leverandørvalg | Medium |
| 3 | Bruk skjemastyrt utdata (Zod eller Pydantic) og kontroller `stop_reason` og refusjon før parsing [3][4][5]. | Arkitektur og stories | Høy |
| 4 | Hent tekst side for side i egen kode, legg inn sidemarkører, og be modellen om sidetall og et ordrett sitat. Kontroller i koden at begge stemmer. | PRD: referansepekere; arkitektur | Medium (verifiseringen er min syntese) |
| 5 | Biblioteker etter stakk: JS/TS bruker unpdf (MIT, en streng per side) [22]; Python bruker pypdf (BSD) eller pdfplumber (MIT) [28][29]. Velg PyMuPDF bare etter at du har vurdert AGPL [24][26]. | Arkitektur: stakkvalg | Medium |
| 6 | Sett en øvre grense for dokumentstørrelse i v1 (min vurdering: i størrelsesorden 50 sider og noen få MB). Det finnes ingen kilde for et bestemt tall. Begrunn grensen med tokens per minutt på gratisnivåer [15] og med testing mot dine egne notater. | Brief: avgrensning; PRD | Lav |
| 7 | Test uttrekket på egne forelesningslysbilder og tabeller før stakken låses. | PRD: testkrav | Høy (som prosess) |

## Åpne spørsmål

| Spørsmål | Hva som trengs |
|---|---|
| Hva er Gemini-gratisgrensene (forespørsler og tokens per minutt og dag), og trengs betalingskort for nøkkel? | Du må logge inn i AI Studio og lese «rate limit»-visningen; offisielle sider viser dem ikke [11] |
| Gratisplanene hos Groq og Mistral, og eventuelle gratis kreditter hos OpenAI og Anthropic | Les kontoinnstillinger og hjelpesider; dokumentsidene ga ikke tall |
| Hvor god er norsk fra Gemma, Qwen3, Llama og Mistral i 7–14B-klassen, og hvor mye RAM og hvor mange tokens per sekund på en 16 GB-laptop? | Datert 2026-benchmark, eller en egen test med Ollama |
| Kvalitet på uttrekk fra lysbilder, tabeller og figurer | Egen test på dine notater (B2) |
| Lisensvilkår for PyMuPDF 2.0 (AGPL eller kommersiell) og tidlige feil etter 19. oktober | Artifex' lisensside og GitHub-saker etter 2026-10-19 |
| Dokumentert praksis for sidemarkører, overlapp og delområder i prompter | Anthropics, LlamaIndex' og LangChains veiledning |
| Er det riktig at Gemini 3 ikke fakturerer innebygd PDF-tekst? | Les prissiden direkte [6] |
| Hva er støttet delmengde av JSON-skjema hos OpenAI («alle felt påkrevd»)? | Les resten av dokumentasjonen [4] |
| Grenser for opplasting hos Quizlet, StudyFetch og ChatPDF | Offisielle hjelpesider |
| Hvordan håndterer studieverktøy hallusinasjoner og viser sikkerhetsnivå i brukergrensesnittet? | Ikke funnet; kan tas som egen brainstorming |
| Mønstre for at brukere legger inn egen nøkkel i appen (BYOK) | Ikke søkt |

## Kildeappendiks

| [n] | Funn kilden støtter | Utgiver | Utgitt | Hentet | Konfidens |
|---|---|---|---|---|---|
| 1 | Claude PDF-grenser, tokens per side, logiske sidetall | [Anthropic](https://platform.claude.com/docs/en/build-with-claude/pdf-support) | uten dato | 2026-10-28 | høy |
| 2 | Sidesitater (`page_location`), uforenlige med strukturert utdata | [Anthropic](https://platform.claude.com/docs/en/build-with-claude/citations) | uten dato | 2026-10-28 | høy (verified) |
| 3 | Strukturert utdata hos Anthropic, begrensninger, feiltilstander | [Anthropic](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | uten dato | 2026-10-28 | høy |
| 4 | OpenAI strukturert utdata | [OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs) | uten dato | 2026-10-28 | medium-høy |
| 5 | Gemini strukturert utdata | [Google](https://ai.google.dev/gemini-api/docs/structured-output) | uten dato | 2026-10-28 | høy |
| 6 | Gemini PDF-grenser og tokens per side | [Google](https://ai.google.dev/gemini-api/docs/document-processing) | uten dato | 2026-10-28 | medium |
| 7 | OpenAI PDF-inndata | [OpenAI](https://developers.openai.com/api/docs/guides/pdf-files) | uten dato | 2026-10-28 | medium-høy |
| 8 | Claude-modeller, kontekst og priser | [Anthropic](https://platform.claude.com/docs/en/about-claude/models/overview) | uten dato | 2026-10-28 | høy |
| 9 | Claude-priser, batch, tokenizer | [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing) | uten dato | 2026-10-28 | høy |
| 10 | Gemini-priser, gratisnivå, dataforbruk | [Google](https://ai.google.dev/gemini-api/docs/pricing) | 2026-10-27 | 2026-10-28 | høy (verified) |
| 11 | Gemini-grenser vises i AI Studio; tall mangler | [Google](https://ai.google.dev/gemini-api/docs/rate-limits) | uten dato | 2026-10-28 | medium |
| 12 | Gemini-vilkår: innhold på ubetalte tjenester | [Google](https://ai.google.dev/gemini-api/terms) | uten dato | 2026-10-28 | medium-høy |
| 13 | OpenAI-priser | [OpenAI](https://developers.openai.com/api/docs/pricing) | uten dato | 2026-10-28 | medium-høy |
| 14 | Groq-modeller og priser | [Groq](https://console.groq.com/docs/models) | uten dato | 2026-10-28 | medium |
| 15 | Groq-grenser (Developer-plan) | [Groq](https://console.groq.com/docs/rate-limits) | uten dato | 2026-10-28 | lav-medium |
| 16 | OpenRouter `:free`-grenser og modellliste | [OpenRouter](https://openrouter.ai/docs/api-reference/limits) | uten dato | 2026-10-28 | medium-høy (grenser), lav-medium (modellliste) |
| 17 | Ollama standard kontekstlengde | [Ollama](https://docs.ollama.com/context-length) | uten dato | 2026-10-28 | høy |
| 18 | Gemma 4 på Ollama: størrelser og kontekst | [Ollama](https://ollama.com/library/gemma4) | uten dato | 2026-10-28 | medium |
| 19 | Ollama skjemastyrt utdata | [Ollama](https://registry.ollama.ai/blog/structured-outputs) | 2024-12 | 2026-10-28 | medium |
| 20 | NorEval: norske benchmark for åpne modeller | [arXiv/ACL](https://arxiv.org/abs/2504.07749) | 2025 | 2026-10-28 | medium |
| 21 | pdf.js: Apache-2.0 | [Mozilla](https://raw.githubusercontent.com/mozilla/pdf.js/master/LICENSE) | live | 2026-10-28 | høy |
| 22 | unpdf: MIT, en streng per side, serverless | [unjs](https://github.com/unjs/unpdf) | live | 2026-10-28 | høy |
| 23 | pdf-parse: versjon og lisens | [npm](https://registry.npmjs.org/pdf-parse) | n/a | 2026-10-28 | medium |
| 24 | PyMuPDF 2.0: dobbeltlisens | [PyPI](https://pypi.org/project/PyMuPDF/) | 2026-10-19 | 2026-10-28 | høy |
| 25 | PyMuPDF 2.0 utgivelsesnotater | [PyMuPDF/GitHub](https://github.com/pymupdf/PyMuPDF/releases) | 2026-10-19 | 2026-10-28 | høy |
| 26 | pymupdf4llm slått inn i pymupdf 2.x; AGPL-3.0 i repoet | [Artifex/GitHub](https://github.com/pymupdf/pymupdf4llm) | live | 2026-10-28 | høy |
| 27 | pymupdf4llm: `page_chunks`, topp- og bunntekst | [PyMuPDF docs](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html) | uten dato | 2026-10-28 | medium |
| 28 | pypdf 6.21.3, BSD-3-Clause | [PyPI](https://pypi.org/project/pypdf/) | 2026-10-27 | 2026-10-28 | høy |
| 29 | pdfplumber 0.11.10, MIT | [PyPI](https://pypi.org/project/pdfplumber/) | 2026-06-15 | 2026-10-28 | høy |
| 30 | Liten syntetisk uttrekksbenchmark | [justin-aj/GitHub](https://github.com/justin-aj/pdf-extraction-benchmark) | uten dato | 2026-10-28 | lav |
| 31 | Vanlige uttrekksfeil (forum og hjelpesider) | [twig.so](https://help.twig.so/chunking-and-processing/pdf-extraction) | uten dato | 2026-10-28 | lav |
| 32 | NotebookLM: grenser per kilde | [Google](https://support.google.com/notebooklm/answer/16269187) | live | 2026-10-28 | høy (per kilde) |
| 33 | Konfigurasjon i miljøvariabler | [12factor.net](https://12factor.net/config) | uten dato | 2026-10-28 | høy |
| 34 | Hemmelighetsskanning på offentlige repoer | [GitHub](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning) | uten dato | 2026-10-28 | høy |
| 35 | Innspilling og avspilling av LLM-svar i tester | [Sycophant/llm-mock m.fl.](https://hexdocs.pm/sycophant/0.4.2/recording-tests.html) | uten dato | 2026-10-28 | lav-medium |
| 36 | Anthropics grenser: ingen gratisnivå nevnt | [Anthropic](https://platform.claude.com/docs/en/api/rate-limits) | uten dato | 2026-10-28 | medium |
| 37 | Siteringsverifikasjon med ordrette sitater (vitenskapelige referanser); kun søkeutdrag lest | [AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/42361/46322) | 2026 | 2026-10-28 | lav |

## Foreldelseskart

Beregnet med `recon_kit.py staleness` fra kravene i ledgeren. Vinduene er pakkens ferskhetskrav: pris, grenser og API-funksjoner 3 måneder (AI-nær), versjoner 1 måned. Utgivelsesdato er satt til hentedato der siden ikke har dato.

| Påstand | Klasse | Sjekk på nytt |
|---|---|---|
| PyMuPDF 2.0: lisens og innslått pymupdf4llm | versjon | 2026-11-19 |
| Sidesitater kan ikke kombineres med strukturert utdata (Anthropic) | API-funksjon | 2027-01-28 |
| Modellpriser (Claude, Gemini, OpenAI, Groq) | pris | 2027-01-28 |
| Gemini gratisnivå: innhold brukes til produktforbedring | pris | 2027-01-27 |
| Groq gratis- og basegrenser (8K tokens per minutt) | grense | 2027-01-28 |
| Claudes PDF-grenser (100/600 sider, 32 MB) | grense | 2027-01-28 |
| Ollama standard kontekstlengde | grense | 2027-01-28 |

**Tidligste sjekk:** 2026-11-19 (PyMuPDF). Siden planleggingen avsluttes i november, er det ikke relevant før arkitekturen skal låse stakken. Prisene bør sjekkes på nytt før innlevering 7. desember.
