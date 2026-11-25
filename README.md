# G49 — Local Minimum

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

Repoet inneholder gruppens applikasjon og dokumentasjon av utvikling, testing og kvalitetssikring med KI.

## Medlemmer

- Mathias Bråten

## Hva appen er

**AI Study Buddy** gjør ditt eget kursmateriell om til aktiv selvtesting. Du laster opp en PDF eller tekst til et tema, og appen lager et sammendrag, nøkkelbegreper, spørsmål og kort, hvert med en kildehenvisning som blir sjekket mot teksten. Deretter øver du med quiz, «Øv på feilene» og repetisjon av kort, og appen viser hva du bør gjøre neste gang.

Uten API-nøkkel kjører appen i **demomodus** (Mock mode) med innspilte svar for et eksempeldokument, så du kan prøve alt uten konto, nøkkel eller nettverk.

## Dette trenger du

| Verktøy | Hvorfor | Installering |
| --- | --- | --- |
| git | For å klone repoet | Vanligvis installert. Sjekk med `git --version` |
| uv | Installerer Python 3.13 og alle avhengigheter, og kjører appen | macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh` · Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

Du trenger ikke Python fra før, og heller ikke Node, Docker, en databaseserver, en betalt konto eller en API-nøkkel.

## API-nøkler

Appen bruker **én** API-nøkkel, og den er valgfri:

| Nøkkel | Fra | Trengs til | Uten den |
| --- | --- | --- | --- |
| `ANTHROPIC_API_KEY` | Anthropic Console (<https://console.anthropic.com>) | Å lage studiemateriell fra dine egne filer (ekte modus) | Appen kjører i demomodus. Alt kan prøves med eksempeldokumentet, og testene trenger aldri nøkkel. |

Ingen andre nøkler eller kontoer trengs. Nøkkelen legges bare i `.env`, som git ignorerer. Se [Ekte modus](#ekte-modus-med-api-nøkkel) for hvordan du lager den og setter en utgiftsgrense.

## Start appen

```bash
git clone https://github.com/IBE160-2026/G49-braten.git
cd G49-braten
cp .env.example .env          # Windows: copy .env.example .env
uv sync                       # installerer Python 3.13 og avhengighetene
uv run manage.py migrate      # lager data/db.sqlite3
uv run manage.py runserver
```

Åpne <http://127.0.0.1:8000>. Et banner øverst viser at appen kjører i demomodus:

> **Demomodus:** appen bruker innspilte svar for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.

## Prøv alle kjernefunksjonene

1. **Lag en konto** under «Opprett konto» med en hvilken som helst e-postadresse og et passord.
2. **Lag et fag og et tema.** Velg «Nytt fag» (for eksempel «Databaser»), og deretter «Nytt tema» inne i faget (for eksempel «Normalisering»).
3. **Bruk eksempeldokumentet.** I temaet velger du «Legg til kilde», et detaljnivå og så **«Bruk eksempeldokumentet»**. Eksempeldokumentet behandles med innspilte svar, og ingenting sendes over nettverket. Kilden vises under fanen «Kilder» og blir «Klar» etter noen sekunder.
4. **Se studiemateriellet.** Fanen «Sammendrag» viser sammendraget og nøkkelbegrepene, og fanen «Test deg selv» viser kortene. Under sammendraget står **«1 element ble fjernet fordi kildehenvisningen ikke stemte.»** Det er med vilje: eksempelet har ett element med feil kildehenvisning, og fjerningen viser at kontrollen virker (FR-8).
5. **Ta en quiz.** Under fanen «Quiz» velger du «Velg antall og start», et antall og «Start quiz». Svar på alle spørsmålene, gjerne med minst ett feil svar. På «Resultat» velger du **«Øv på feilene»** for å ta en runde med bare spørsmålene du bommet på.
6. **Repeter kortene.** Velg «I dag · N» i menyen (eller «Repeter dagens kort» under «Test deg selv»), snu hvert kort med «Vis svaret» og vurder det med «Igjen», «Vanskelig», «Bra» eller «Lett» til du ser «Repetisjonen er ferdig».
7. **Valgfritt: last opp en annen PDF.** Appen lagrer den, men sier at studiemateriell for egne filer krever en API-nøkkel (FR-20).
8. **Se at for store filer blir avvist.** Velg «Legg til kilde», velg filen `sample/for_mange_sider.pdf` fra repoet (51 sider), et detaljnivå og «Last opp». Appen lagrer ingenting og viser: «Filen har 51 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.» (FR-3)

Logg gjerne ut («Logg ut» i kontomenyen) og inn igjen: fag, temaer, studiemateriell, svar og repetisjonsdatoer er der fortsatt.

I demomodus får fritekstsvar en plassholder-vurdering merket «Demo-vurdering». Den tester flyten, ikke kvaliteten på rettingen.

## Kjør testene

```bash
uv run pytest
```

Hele testkjøringen tar noen minutter (rundt 4 minutter på en ny MacBook). Testene trenger verken API-nøkkel eller nettverk. Socketer er blokkert under testkjøringen (`--disable-socket`), og testene kjører alltid i demomodus, også om `.env` har en nøkkel. Testnavnene begynner med kravet de dekker, for eksempel `test_fr15_…` eller `test_nfr7_…`.

Testene dekker blant annet (NFR-5):

| Område | Eksempel på testfil |
| --- | --- |
| Grenser for opplasting (FR-3) | `tests/test_ingestion.py`, `tests/test_upload.py` |
| Sjekk av kildehenvisninger (FR-8) | `tests/test_reference_check.py` |
| Retting av flervalg (FR-11) | `tests/test_grading.py`, `tests/test_quiz.py` |
| «Øv på feilene» (FR-13) | `tests/test_result.py` |
| Repetisjonsdatoer (FR-15) | `tests/test_review_rules.py`, `tests/test_review.py` |
| Mestring per tema (FR-16, FR-17) | `tests/test_progress.py` |
| Daglig grense for genereringer (NFR-7) | `tests/test_ai_gateway.py`, `tests/test_generation.py` |
| Hele sensorstien over, ende til ende | `tests/test_examiner_path.py` |

### Nettlesertester

`static/js/app.js` (dialoger, tastene i fanene, quizen og kortene, resultatstripen og temavelgeren) testes i en ekte nettleser med Playwright og Chromium, uten nøkkel og i demomodus. Testene ligger i `tests/browser/` og er valgfrie: `uv run pytest` hopper over dem. Første gang laster du ned Chromium (rundt 100 MB):

```bash
uv run playwright install chromium   # én gang
uv run pytest -m browser             # kjører bare nettlesertestene
```

Også når du peker på en enkelt fil eller test i `tests/browser/`, trengs `-m browser`. Uten det blir alt valgt bort i stillhet. `-m ""` kjører alle testene. Kjør `uv run pytest -m browser` før du committer en endring i `static/js/app.js`, siden den vanlige kjøringen ikke dekker den.

Nettleseren snakker bare med en testserver på 127.0.0.1. En forespørsel til en annen adresse blir stoppet og får testen til å feile.

## Akseptansesjekkliste (SM-2)

Hver sjekk består enten ved å følge denne README-en (R) eller ved en automatisk test (T). `tests/test_sm2_checklist.py` feiler hvis en test som er nevnt her, får nytt navn eller forsvinner.

| Sjekk | Hva | R/T | Bevis |
| --- | --- | --- | --- |
| 1 | Eksempeldokumentet gir studiemateriellet i FR-7 | R | Steg 3–4 · `test_uj5_examiner_path_end_to_end_in_mock_mode` |
| 2 | Elementet med feil kildehenvisning blir fjernet (FR-8) | R | Steg 4 · `test_uj5_examiner_path_end_to_end_in_mock_mode` |
| 3 | Appen kjører i demomodus uten nøkkel (FR-20, NFR-2) | R | «Start appen», steg 1 og 7 · `test_uj5_examiner_path_end_to_end_in_mock_mode`, `test_uj5_other_pdf_in_mock_mode_is_stored_with_the_needs_key_message` |
| 4 | Opplastinger over grensene blir avvist (FR-3) | R | Steg 8 · `test_uj5_committed_51_page_pdf_is_refused_naming_the_page_limit`, `test_fr3_51_page_pdf_is_refused_naming_the_limit` |
| 5 | Quizer blir rettet; feil og delvis riktige spørsmål går til «Øv på feilene» (FR-11 til FR-13) | R | Steg 5 · `test_uj5_examiner_path_end_to_end_in_mock_mode` |
| 6 | Data lagres per student, fag og tema og er der etter ny innlogging (FR-1, FR-2) | R | Steg 1–2 og utloggingen etter stegene · `test_uj5_examiner_path_end_to_end_in_mock_mode` |
| 7 | Repetisjonsdatoer følger FR-15 | T | `test_fr15_next_due_moves_boxes_and_caps_at_eight`, `test_fr15_acceptance_three_good_ratings_end_and_today_drops` |
| 8 | Svake temaer vises som i FR-17 | T | `test_fr17_seeded_weak_topics_lowest_first`, `test_fr17_p04_lists_weak_topics_first_with_tags_and_the_weak_quiz_button` |
| 9 | Genereringer stopper ved grensen i NFR-7 | T | `test_nfr7_twenty_calls_succeed_and_the_21st_raises_daily_limit`, `test_nfr7_a_pending_source_at_the_limit_fails_with_daily_limit` |
| 10 | Neste steg følger rekkefølgen i FR-28 | T | `test_fr28_hjem_due_cards_come_first_per_fag`, `test_fr28_rules_1_and_2_come_before_an_empty_topic` |

Du kjører én av dem med for eksempel `uv run pytest -k test_fr15_next_due_moves_boxes_and_caps_at_eight`.

## Hvis noe går galt

| Symptom | Løsning |
| --- | --- |
| `uv: command not found` | Åpne en ny terminal etter at du har installert uv, eller følg PATH-hintet installasjonen skrev ut |
| `no such table` | Du hoppet over `uv run manage.py migrate` |
| Du vil stoppe serveren | Trykk Ctrl+C i terminalen der `runserver` kjører |
| Port 8000 er opptatt | `uv run manage.py runserver 8001`, og åpne <http://127.0.0.1:8001> |
| Du vil starte helt på nytt | Stopp serveren, slett `data/db.sqlite3` og kjør `uv run manage.py migrate` igjen |

## Ekte modus (med API-nøkkel)

Dette trenger ikke sensor. Det er for deg som vil lage studiemateriell fra egne filer.

1. **Lag en konto** i Anthropic Console (<https://console.anthropic.com>).
2. **Kjøp en liten forhåndsbetalt kreditt.** Modellen har ikke gratisnivå. Å generere én PDF på 20 sider koster godt under 1 cent, og appen stopper deg ved 20 genereringer per dag (NFR-7).
3. **Sett en månedlig utgiftsgrense** i Console, så en feil aldri kan koste mer enn du har valgt.
4. **Lag en API-nøkkel og legg den i `.env`**, og ingen andre steder. `.env` er ignorert av git, og appen logger eller viser aldri nøkkelen.
   ```dotenv
   ANTHROPIC_API_KEY=sk-ant-...
   ```
5. **Start `runserver` på nytt.** Banneret forsvinner, og appen er i ekte modus.
6. **Godta personvernvarselet** ved første opplasting. Før du gjør det, sender appen ingen tekst fra kildene dine noe sted (FR-22).

Vil du kjøre demomodus selv om nøkkelen er satt, for eksempel for å vise sensorstien, setter du `AI_PROVIDER=mock` i `.env`.

`ANTHROPIC_API_KEY` eller `AI_PROVIDER` som er satt i skallet (miljøvariabler i terminalen), går foran verdiene i `.env`. Ser du ikke banneret når du venter det, eller omvendt, sjekk `echo $ANTHROPIC_API_KEY $AI_PROVIDER`.

Hvis nøkkelen lekker, for eksempel i en commit eller et skjermbilde, trekker du den tilbake i Console med en gang og lager en ny.

Alle innstillingene i `.env` er forklart i `.env.example`.

## Prosjektdokumenter

- Spesifikasjon: [`_bmad-output/specs/spec-ai-study-buddy/SPEC.md`](_bmad-output/specs/spec-ai-study-buddy/SPEC.md)
- Arkitektur: [`ARCHITECTURE-SPINE.md`](<_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md>) og [`SETUP-GUIDE.md`](<_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/SETUP-GUIDE.md>)
- Kvalitet og målinger: [`docs/quality/`](docs/quality/)
