---
title: 'Topics and Sources'
type: 'feature'
created: '2026-11-15'
status: 'done'
baseline_commit: '0627ebe967dda99a7c49446cb528a3144fc4cac1'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/_bmad-output/specs/spec-ai-study-buddy/stories/3-shell-courses-and-a-basic-home.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A fag can exist but holds nothing: there are no Topics or Sources, P04 shows a dead empty-state, and deleting a fag cannot say what goes (CAP-2, FR-2; second half of story 3, split from 3a).

**Approach:** Add `Topic` and `Source` to `courses` with an owned cascade chain, «Nytt tema» (D03), Topic rows on P04, a basic Topic page (P05) listing Sources, rename (D08) and delete (D09) for Topics and Sources, and D09 texts that count what goes. Source creation arrives with upload in story 4.

## Boundaries & Constraints

**Always:**
- `Topic(student, course, name, created_at)` and `Source(student, topic, name, kind, size_bytes, detail_level, status, failure_reason, content_sha256, language, started_at, removed_count, dropped_count, created_at)`, each with a non-null `student` FK set explicitly from the parent in `courses.services`, `on_delete=CASCADE` on every link (Course → Topic → Source), `OwnedQuerySet`. Enums as `TextChoices` with the spine's lowercase values (`pending/generating/ready/failed`, `short/medium/detailed`, `FailureReason`; `kind` = `pdf/text/pasted`). Name rules as Course (required, stripped, ≤ 80). Topics in creation order; Sources newest first.
- Reuse 3a's mechanics unchanged: dialogs as GET URLs with the `dialog` partial, `render_page`, `redirect_after_submit`, `safe_next`, `FocusFirstErrorMixin`, `get_owned_or_404`, P12 for anything not owned. Dialogs, forms and services in `courses`; P04 and P05 in `web` (AD-1).
- URLs: `/courses/<id>/topics/new/`, `/topics/<id>/`, `/topics/<id>/rename/`, `/topics/<id>/delete/`, `/sources/<id>/rename/`, `/sources/<id>/delete/`.
- Create Topic → its P05. Rename → safe `next`, else the item's page (Source: its Topic's P05). Delete Topic → its fag's P04. Delete Source → its Topic's P05.
- D09 names what goes and says «Dette kan ikke angres.», with correct singular/plural and zero counts left out:
  - fag: «Slette faget Databaser? 4 temaer, 7 kilder og alle svar slettes.» / «Slett faget»
  - tema: «Slette temaet Normalisering? 2 kilder og alle svar slettes.» / «Slett temaet»
  - kilde: «Slette kilden forelesning-3.pdf? Studiemateriellet fra kilden og svarene på det slettes.» / «Slett kilden»
- P04: «Nytt tema» button and the empty-state «Ingen temaer ennå» / «Et tema samler kildene, kortene og spørsmålene for én del av faget.» / «Nytt tema»; otherwise one row per Topic (name linking to P05, «Ikke nok data ennå», «⋯» with «Gi nytt navn», «Slett»).
- P05: breadcrumb Hjem › fag › tema (back link below 600 px), title, «⋯» actions, a «Kilder» list of source-rows (name, type, size, Detail level, status-label text: pending/generating «Lager studiemateriell …», ready «Klar», failed «Feilet»; «⋯» with rename and delete), and with no Sources the empty-state «Ingen kilder ennå» / «Legg til en PDF, en tekstfil eller tekst du limer inn. Quiz og kort kommer når studiemateriellet er klart.» without an action.
- fag-rail current item stays the fag while on its P05. One test per model checks `student` equals the parent's.

**Never:**
- Upload, «Legg til kilde», band, tabs, Study material, status polling, `effective_status`/`claimable` (stories 4–7); mastery or due counts.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Create tema | D03 «Normalisering» on fag A | Topic with `student` and `course` from A; lands on its P05 | N/A |
| Blank tema | D03 «  » | D03 re-rendered with field error; nothing saved | 200 |
| Tema on other's fag | D03 URL of Student B's fag | P12 | 404 |
| Rename tema | D08 «Normalformer» from P04 | renamed; back on P04 | N/A |
| Delete tema | D09 on tema with 2 Sources | text counts «2 kilder»; Topic and Sources gone; lands on P04 | N/A |
| Delete fag | fag with 1 tema, 1 kilde | «1 tema, 1 kilde og alle svar slettes.»; all three gone | N/A |
| Delete empty fag | no Topics | «Slette faget Databaser? Dette kan ikke angres.» | N/A |
| Rename/delete kilde | own Source | renamed / deleted; lands on its P05 | N/A |
| Other's tema/kilde | P05, D08, D09 of Student B's items | P12, nothing changed | 404 |
| Source order | two Sources | newest first on P05 | N/A |

</frozen-after-approval>

## Code Map

- `courses/models.py` -- Course, `NAME_MAX_LENGTH`, `created_now`; add Topic, Source and the enums here.
- `courses/services.py`, `forms.py` (`name_field`, `FocusFirstErrorMixin`), `views.py`, `urls.py` -- extend with the same shapes as Course.
- `templates/courses/{create,rename,delete,course_menu_items}.html` -- patterns for D03 and the new D08/D09 variants.
- `templates/web/course.html` -- marked «Story 3b adds «Nytt tema»»; `web/views.py` `course` -- add Topic rows.
- `web/context_processors.py` -- `current_course` drives the rail mark; set it on P05.
- `core/messages.py` -- add texts by code.
- `tests/test_courses.py` -- fixtures and helpers to reuse; put new tests in `tests/test_topics_sources.py`.

## Tasks & Acceptance

**Execution:**
- [x] `courses/models.py`, `courses/migrations/0002_*.py` -- Topic, Source, enums
- [x] `courses/services.py` -- create/rename/delete Topic, rename/delete Source, delete counts; Source factory used only by tests until story 4
- [x] `courses/forms.py`, `courses/views.py`, `courses/urls.py`, `templates/courses/*` -- D03, D08/D09 for Topic and Source, counted fag D09
- [x] `web/views.py`, `web/urls.py`, `templates/web/{course,topic}.html`, `templates/components/` (source-row, topic row) -- P04 rows, P05
- [x] `static/css/components.css` -- rows and status-label at 360 px and 1280 px, light and dark
- [x] `tests/test_topics_sources.py` -- every matrix row, plural forms (1/2, zero left out), `student` equals parent per model, cascade from Course and Topic, HTMX partials for the new dialogs, signed-out redirects

**Acceptance Criteria:**
- Given JavaScript off, when the Student creates, renames and deletes a tema, then every step works as full pages.
- Given `uv run pytest` offline, then everything passes, including the import-graph test.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap, plus an orchestrator check against AD-13). No intent_gap or bad_spec; patches sent to the implementation agent; one defer.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| D09 texts in `courses/rules.py` (orchestrator) | low | patch | AD-13: bokmål text only in templates and core/messages.py; a second home for UI text will drift |
| Norwegian TextChoices labels disagree with the status-label template (BH) | low | patch | «Lager studiemateriell» vs «Lager studiemateriell …»; same AD-13 rule |
| Pasted Source shows «0 byte» (BH, ECH) | low | patch | `filesizeformat` on default 0 |
| `create_topic_href` not URL-encoded (BH) | low | patch | Menu items encode; one-filter fix |
| D08/D09 action and hx-post per view, untested (VG) | medium | patch | Six hand-written `action=` args; a slip would rename/delete the wrong item |
| «Avbryt» href untested (VG) | low | patch | Folded into the same parametrized test |
| Too-long Source name, P05 POST 405, size 0 untested (BH) | low | patch | Cheap tests |
| Source names capped at 80 while file names can be longer | medium | defer | Spec sets ≤ 80; story 4 must shorten or reject on upload — deferred-work.md |
| Pending shown as generating with a spinner (BH, ECH) | false | reject | AD-5: «under it, `pending` shows as generating» |
| `started_at` set at creation (BH) | false | reject | AD-5 step 1 creates the Source as pending with `started_at` |
| Validation by `assert` (BH, ECH) | false | reject | Spine Conventions: «Services assert values before saving»; story 4 validates input in forms |
| FailureReason has no labels; failed row shows no reason (BH) | false | reject | Failure display and retry are story 6 |
| No DB constraints for owner chain / status (BH) | low | reject | AD-7 enforces through services plus one test per model |
| D09 «og alle svar slettes» with no Sources (BH) | false | reject | Wording fixed by the spec |
| No guard deleting a generating Source (BH, ECH) | false | reject | AD-5's run-token save matches nothing after a delete; story 6 |
| Reused `course_name_too_long` key (BH) | low | reject | The text is neutral («Navnet kan ha høyst 80 tegn.») |
| Parameter names shadow view names in `_rename`/`_delete` (BH) | low | reject | Readability only |

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes
