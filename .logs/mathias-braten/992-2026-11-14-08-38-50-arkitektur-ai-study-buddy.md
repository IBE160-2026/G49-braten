# Arkitektur for AI Study Buddy

## 2026-11-14 kl. 08:38 — Mathias Bråten

### Oppgave
Kjøre `bmad-architecture` for AI Study Buddy v1: lage en arkitekturspine (et byggegrunnlag for stories og bmad-build) og en oppsettsguide, både for sensors vei og for Mathias' egen. Økten startet 2026-11-13 og ble avsluttet 2026-11-14, fordi bruksgrensen stoppet review-agentene to ganger.

### Plan
- Coaching path, med samtale på norsk og dokumenter på engelsk. Leverer spine og oppsettsguide.
- Ta lastbærende beslutninger sammen med Mathias:
  - stack;
  - modulinndeling;
  - score regnet ut ved visning;
  - generering (to steg, én claim, alt eller ingenting, 5 min tidsavbrudd);
  - dagsgrense per handling;
  - eierskap og 404;
  - hard sletting;
  - Leitner;
  - Oslo-tid;
  - frontend-konvensjoner;
  - gratis hosting med Haiku 5.5 beholdt.
- Destillere spinen fra memloggen, deretter tre avstemminger (PRD, UX og research) og review-port (rubrikk, teknologisjekk og adversarial) med underagenter. Så triage og oppsettsguide.
- Memlogg: `_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/.memlog.md`

### Resultat
- `ARCHITECTURE-SPINE.md` (status `final`) har 19 AD-er, alle vedtatt:
  - modulær monolitt med Django 6.1.3 og HTMX 2.0.11, i ti apper med `core` nederst og `web` øverst;
  - én KI-gateway (Mock eller Claude Haiku 5.5) med et lukket sett operasjoner;
  - dagsgrense i databasen;
  - transaksjonsgrenser rundt KI-kallet (AD-19);
  - SQLite overalt.
- Spinen har også konvensjoner, stack verifisert mot PyPI og npm 2026-11-13/14, ER-, deployment- og tilstandsdiagram, en kravtabell, tre åpne spørsmål og en liste over utsatte valg.
- `SETUP-GUIDE.md`: Del A er sensors vei (git og uv, deretter `uv sync`, `migrate` og `runserver` i Mock mode). Del B er Mathias' vei (nøkkel og forbruksgrense, OQ-1/OQ-2-sjekkliste, krav og deploy-rekkefølge for Hosted instance, tabell over miljøvariabler).
- Avstemmingene ga 21 funn mot PRD, 30 mot UX og 22 mot research. Review-porten ga 23 funn i rubrikken, 8 feil og 4 uverifiserte i teknologisjekken, og 25 hull fra angriperen. Alle klare rettelser er lagt inn. Rapportene ligger i `reviews/`.
- `EXPERIENCE.md` er oppdatert på fire punkter, slik at den stemmer med spinen:
  - teksten for avbrutt generering;
  - ingen skjeletter;
  - størrelse og type sjekkes i nettleseren, sidetall på serveren;
  - URL-eksempelet bruker `?tab=`.
- Beslutninger fra Mathias: Django + HTMX; ingen betaling for hosting; Haiku 5.5 beholdes; FR-25 droppes hvis ingen gratis vert oppfyller AD-16.
- Ikke committet: arkitekturmappen og endringen i `EXPERIENCE.md`.

### Åpne punkter
- OQ-1: uttrekkstest på tre egne lysbildesett (pypdf plain/layout mot pdfplumber) før 20.11. Avgjør bibliotek og `MIN_TEXT_CHARS`, skrives til `docs/quality/`. Dette er det eksisterende punktet fra 2026-10-28 i `issues.md`.
- OQ-2: mål genereringstid i Real mode for 20 og 50 sider, og sjekk rate-limit-nivået hos Anthropic, før 20.11.
- OQ-3: vertssjekk for FR-25 (PythonAnywhere free: allowlist for `api.anthropic.com`, tidsgrense, samtidighet, SQLite-versjon, planlagt backup) når FR-25 starter.
- Oppdater `PRODUCT.md` («Stack: Undecided») med valget fra arkitekturen.
- Valgfritt: polering av `SETUP-GUIDE.md` med bmad-review (structure, prose).
- Neste steg: bmad-spec for å ta spinen inn som følgedokument, deretter bmad-create-epics-and-stories.
