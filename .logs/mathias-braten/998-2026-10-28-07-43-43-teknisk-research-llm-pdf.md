# Teknisk research: LLM og PDF-uttrekk

## 2026-10-28 kl. 07:43 — Mathias Bråten

### Oppgave
Før PRD: finne ut hvilken språkmodell-løsning og PDF-uttrekk AI Study Buddy bør bruke, slik at sensor kan kjøre appen uten forfatterens nøkkel (punkt fra faglærerens tilbakemelding). I tillegg ba brukeren om en statuslinje med modell, kontekstbruk, tokens og effort-nivå.

### Plan
- Kjøre `bmad-deep-recon` (type technical, preset standard, to runder) på sju dimensjoner: A1–A4 (språkmodell) og B1–B3 (PDF).
- Kontrollere to nøkkelfunn mot primærkilder og kjøre sitatsjekk (mekanisk og semantisk).
- Sette opp statuslinje i `~/.claude/settings.json` (utenfor repoet).

### Resultat
- Rapport: `_bmad-output/planning-artifacts/research/technical-llm-choice-and-pdf-extraction-for-ai-stu-2026-10-28/research.md` (status complete, 37 kilder, 2 verified / 3 unverified / 1 disputed). Digests, memlog og `citation-audit.md` ligger i samme mappe. Ikke committet.
- Hovedfunn: kostnad per PDF er under 2 cent; nøkkeltilgang for sensor er det som avgjør. Anbefalt: leverandørlag med mock som standard, egen sideuttrekking med sidemarkører, sitat- og sidekontroll i kode. Claudes sidesitater kan ikke kombineres med strukturert JSON.
- Sitatsjekken fant 2 feil (enhet øre/cent) og 4 overdrivelser; alle rettet.
- Statuslinje: modell, effort, kontekst-% og tokens. Sikkerhetskopi av gamle innstillinger i scratchpad.

### Åpne punkter
- Les Gemini-gratisgrensene i AI Studio og sjekk om kort trengs (står ikke på offisielle sider).
- Test PDF-uttrekk på egne forelesningslysbilder før stakken låses.
- Avklar PyMuPDF-lisens (AGPL) hvis Python velges.
- Ikke gjort: HTML-oversikt og språkvask av research.md. Rapporten er ikke committet eller pushet.
- Neste steg: oppdater brief med funnene, deretter PRD.
