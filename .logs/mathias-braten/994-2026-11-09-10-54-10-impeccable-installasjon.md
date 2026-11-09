# Impeccable-installasjon

## 2026-11-09 kl. 10:54 — Mathias Bråten

### Oppgave
Installere design-skillen Impeccable i Claude Code før det nye UX-arbeidet. Mathias ba meg finne installasjonskommandoen på nettet og kjøre den.

### Plan
- **Kilde:** Jeg fant det offisielle GitHub-repoet `pbakaus/impeccable` og npm-pakken `impeccable` v4.8.1, som Paul Bakaus vedlikeholder. Flere søketreff var uoffisielle kopier, og dem brukte jeg ikke.
- **Kontroll før kjøring:** Jeg leste oppstartsskriptet `cli/bin/cli.js`. Det starter et ferdigbygd program for maskinen og sjekker det mot SHA-256-summene som følger med pakken.
- **Omfang:** Jeg installerte globalt i `~/.claude/`, der BMAD-skillene også ligger. Da blir gruppe-repoet ikke endret.
- Jeg tok en sikkerhetskopi av `~/.claude/settings.json` før installasjonen.
- **Kommando:** `npx -y impeccable@4.8.1 install -y --providers=claude --scope=global`

### Resultat
- **Skillen:** `impeccable` v4.8.1 ligger i `~/.claude/skills/impeccable/` og kan kjøres som `/impeccable`. Den kom inn i skill-lista allerede i samme økt.
- **Motoren:** Designsjekkeren v0.1.19 (darwin-arm64) ligger i skill-mappa. SHA-256-summen stemmer med pakkens sjekksumfil.
- **Agenter:** Fire nye i `~/.claude/agents/`: `impeccable-asset-producer`, `impeccable-documenter`, `impeccable-finish-reviewer` og `impeccable-manual-edit-applier`.
- **Hooks:** Tre nye i `~/.claude/settings.json`, og de gjelder i alle prosjekter:
  - etter Edit og Write sjekker de UI-filene som er endret
  - ved øktstart
  - ved Stop kjører de en grundig designsjekk
- **Resten av settings:** Modell, statuslinje og tema er uendret. Installasjonen la også til en `description`-nøkkel øverst i fila.
- **Hvor Impeccable skriver:** `/impeccable init` lager `PRODUCT.md` i prosjektroten, og `/impeccable document` lager `DESIGN.md` samme sted. BMAD-dokumentene ligger fortsatt i `_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-05/`.
- **Telemetri:** Når et nytt design startes, henter skillen visuelle retninger fra impeccable.style. Den sender også anonymt hvilke retninger som ble vist og hvilken som ble valgt. Det kan slås av med `npx impeccable telemetry off`.
- **Repoet:** Installasjonen endret ingenting i repoet, og git status var ren etterpå.

### Åpne punkter
- Start en ny Claude Code-økt, siden hookene lastes ved oppstart. Kjør deretter `/impeccable init` i prosjektet, og vis den til de eksisterende `DESIGN.md` og `EXPERIENCE.md`, så den bygger videre på valgene derfra.
