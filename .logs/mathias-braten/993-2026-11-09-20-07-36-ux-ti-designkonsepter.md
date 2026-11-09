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
