# Nettlesertester for app.js

## 2026-11-25 kl. 10:08 — Mathias Bråten

### Oppgave
Gjennomfør retrotiltak E1-1 etter spec-en `_bmad-output/implementation-artifacts/spec-retro-e1-1-browser-test-harness.md`: Playwright-tester uten nøkkel for `static/js/app.js`, som var utsatt seks ganger.

### Plan
- Spec-en over er planen. Den sier at testene er valgfrie (markøren `browser`) og at én test skal dekke hver rad i matrisen.
- Pytest-playwright mot `live_server` på 127.0.0.1 i demomodus, med eksisterende hjelpere for testdata.

### Resultat
- `pyproject.toml`/`uv.lock`: `playwright==1.65.2` og `pytest-playwright==0.10.0` i dev-gruppa. `addopts` har `-m 'not browser'`, og markøren `browser` er registrert.
- `tests/browser/` (conftest og seks moduler, 19 tester): dialoger (åpne, Esc, Avbryt, gyldig innsending, nettverksfeil, 500), tastene i P05-fanene, tastene i P06-quizen, P07-stripa og hash, D10-foten, piltastene i P08 og vern mot dem, snu kort og vurdere med 1–4 i P09. Pytest-socket slipper bare 127.0.0.1 gjennom. Forespørsler fra nettleseren til andre adresser blir stoppet og får testen til å feile. Mangler Chromium, feiler testen med beskjeden om `uv run playwright install chromium`.
- Reell feil i `app.js` (P07): trykk på samme slot en gang til flyttet fokus til `<body>`. Lenkens hopp blir nå avbrutt med `preventDefault`.
- Mutasjonssjekk: uten `showModal()`, P05-`End`, D10-lytteren, P07-fiksen eller vernet mot tastetrykk i tekstfelt feiler testene. Alt ble satt tilbake etterpå.
- `uv run pytest -m browser`: 19 består. `uv run pytest`: 902 består og 19 er valgt bort.
- README har fått seksjonen «Nettlesertester». `deferred-work.md` har seks punkter markert løst, og `sprint-status.yaml` har E1-1 satt til `done`. Implementation Notes i spec-en er fylt ut.
- Endringene er ikke committet.

### Åpne punkter
- Gjennomgang (review) av endringene gjenstår. Spec-en står fortsatt som `in-progress`.
