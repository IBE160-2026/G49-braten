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
