# Story 6: generering av studiemateriell og referansesjekken

## 2026-11-16 kl. 18:10 — Mathias Bråten

### Oppgave
«start story 6»: bygg story 6 fra `stories.yaml`, «Study-material generation and the Reference check» (CAP-4, CAP-5, FR-6). Det betyr å generere Summary, Key concepts, Flashcards og Questions gjennom en alt-eller-ingenting-livssyklus med retry, og å fjerne og telle elementer som feiler referansesjekken.

### Plan
- Kjørte `bmad-build` med spec-mappen `spec-ai-study-buddy` og story-id 6. Kontekst: SPEC.md, story 5 for kontinuitet, og AD-2–AD-6, AD-13, AD-18 og AD-19 i arkitekturspinen.
- Spec: [6-study-material-generation-and-the-reference-check.md](../../_bmad-output/specs/spec-ai-study-buddy/stories/6-study-material-generation-and-the-reference-check.md).
- Mathias valgte 1A: en `pending` kilderad starter genereringen selv med én `hx-post` ved lasting. Det er et andre navngitt unntak fra AD-13. Specen ble beholdt i full lengde (ca. 2000 tokens).
- En subagent implementerte. Deretter gikk tre reviewere over koden (Blind Hunter, Edge Case Hunter og Verification Gap), og ni små rettinger ble gjort.

### Resultat
- Commit `ebe5898` «feat: study-material generation and the Reference check (story 6)».
- `courses`:
  - `claimable()`, `effective_status` og `effective_failure_reason` (5-minuttersregelen).
  - `claim`, `mark_ready` og `mark_failed`. De to siste matcher bare når kjøringens token fortsatt eier kilden.
- `studymat`:
  - Modellene Summary, KeyConcept, Flashcard og Question, med migrasjon `0001_initial`.
  - `checks.py`: FR-7-reglene og referansesjekken etter AD-6.
  - `services.generate()`, som lagrer alt eller ingenting.
  - `POST /sources/<id>/generate/`.
- `ai/markers.py` med markørformatet `[[L{index}]]`.
- Kilderaden viser «Klar · 1 element fjernet», «Feilet» med årsak og «Prøv igjen», eller «Bruk eksempeldokumentet» for `needs_key`. Ved den daglige grensen er knappen inaktiv.
- Eksempeldokumentet gir 7 Key concepts, 10 Flashcards og 11 Questions. Referansesjekken fjerner 1 (det plantede BCNF-kortet), og FR-7-reglene dropper 0.
- Review fant 28 punkter. 9 ble rettet: setningstelling med ordenstall som «1. normalform» og forkortelser, sjekken av riktig svar i hintet, free-text med alternativer, at Location-teksten bare normaliseres én gang, dobbel grensemelding, og tre manglende tester (CSRF, foreldet rad ved grensen, grensen på nøyaktig halvparten). 19 ble avvist med begrunnelse i specens triage-logg.
- `uv run pytest`: 442 bestått offline. `manage.py check` og `makemigrations --check` er rene.

### Åpne punkter
- Sjekk i nettleser at en ny kilde starter genereringen av seg selv og at raden byttes ut. Til nå er dette bare testet med Djangos testklient.
- Skriv unntaket fra AD-13 (POST ved lasting for `pending` kilderad, valg 1A) inn i arkitekturspinen.
- Story 17 (Word): `studymat.services.locations()` bruker bare `index` som nøkkel. Dette må avklares når kilder kan ha både overskrifter og avsnitt.
