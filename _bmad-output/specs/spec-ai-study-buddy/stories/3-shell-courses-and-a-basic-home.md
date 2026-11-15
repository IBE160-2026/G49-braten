---
title: 'Shell, Courses and a basic Home'
type: 'feature'
created: '2026-11-15'
status: 'done'
baseline_commit: '24c29408a46a93ac3041db7b2be899edb9c192a0'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After sign-in the Student lands on a placeholder: there is no shell, no way to add a fag, and no 404 page (CAP-2, FR-2; story 3 split into 3a here and 3b in deferred-work.md).

**Approach:** Build the signed-in shell (fag-rail from 1024 px; top-bar and fag-switcher below), D01 account menu with theme and sign-out, P12, vendored htmx and Public Sans, the AD-13/AD-18 dialog mechanics, and the Course model with create (D02), rename (D08) and delete (D09) from a basic Hjem (P03) and a basic Fagoversikt (P04).

## Boundaries & Constraints

**Always:**
- `courses.Course(student, name, code, created_at)`: non-null `student` FK (CASCADE), `objects = OwnedQuerySet.as_manager()`, name required (≤ 80 chars, stripped), code optional (≤ 20). Fag listed in creation order everywhere. Views load Courses only via `for_student` / `get_owned_or_404` (AD-7).
- AD-1 holds: Course dialogs, forms and services live in `courses`; P03, P04, P12, the shell context and composite regions live in `web`.
- AD-13/AD-18: every URL is a full page; dialogs are GET URLs — standalone page normally, `<dialog>` partial in the one `#dialog` slot under HTMX, chosen by `request.htmx.target` with the `core.http` Vary decorator; valid submit → `HX-Location`, invalid → dialog re-rendered. Mutating controls use `hx-disabled-elt` and `hx-sync`. Menus use native `popover`. One `static/js/app.js` with delegated listeners only, htmx 2.0.11 vendored, both `defer` in `<head>`, `historyRestoreAsHxRequest: false`. No `hx-confirm`, no native confirm, no success toast.
- Create → the new fag's P04. Rename → back to the page it came from (safe relative `next`, else P04). Delete → Hjem. D09 names the fag and says it cannot be undone («Slette faget Databaser? Alt i faget slettes. Dette kan ikke angres.»), destructive button «Slett faget».
- fag-rail and fag-switcher behave as EXPERIENCE.md «Shell and navigation», with due count shown as 0 and mastery «–» with a dotted meter until stories 11–12; «I dag · 0» is plain text until Repetisjon exists. Current item has `aria-current="page"`. Empty: «Ingen fag ennå. Lag ett fag for hvert emne du tar.»; fag-switcher hidden with no fag.
- Hjem: empty-state «Ingen fag ennå» / «Lag ett fag for hvert emne du tar, og legg temaer inn under det.» / «Nytt fag»; otherwise one row per fag (name, code, «Ikke nok data ennå», «⋯» menu with «Gi nytt navn» and «Slett»). No band, no forecast.
- P04: breadcrumb from 600 px (back link below), title = fag name, code, «⋯» actions, and the empty-state «Ingen temaer ennå» text without its action (3b adds «Nytt tema»).
- D01: «Utseende» segmented-control System/Lys/Mørk stored only in a `theme` cookie and rendered server-side as `<html data-theme>`; «Logg ut» posts to sign-out.
- P12 via `handler404`, rendered in the shell for a signed-in Student: «Feil 404» · «Fant ikke siden» · EXPERIENCE text · «Til Hjem». Another Student's fag gives exactly the same page.
- Public Sans vendored as woff2 with its OFL licence; text in bokmål via templates and `core/messages.py`. 360 px with no horizontal scroll, light and dark, dialogs as bottom sheets below 600 px, Esc and «Avbryt» close.

**Never:**
- Topics, Sources, «Nytt tema», delete counts (3b); band, forecast, mastery, due counts (stories 11–13); mode-banner (story 5); session layout.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| New Student | no fag | Hjem empty-state; rail «Ingen fag ennå»; no fag-switcher | N/A |
| Create | D02 name «Databaser», code «DAT102» | Course saved for this Student; lands on its P04; appears last in rail and Hjem | N/A |
| Blank name | D02 name «   » | D02 re-rendered with a field error; nothing saved | 200 |
| Rename | D08 «Databaser 2» from Hjem | name changed; back on Hjem | N/A |
| Delete | D09 confirm | Course removed; lands on Hjem | N/A |
| GET delete | open D09 | shows the confirmation, deletes nothing | N/A |
| Other's fag | P04, D08 or D09 of Student B's fag as A | P12 404, nothing changed | 404 |
| Unknown URL | `/nope/` signed in | P12 in the shell | 404 |
| HTMX dialog | GET D02 with `HX-Request`, `HX-Target: dialog` | only the dialog partial; `Vary` header set | N/A |
| Theme | choose «Mørk» | `theme=dark` cookie; next page has `data-theme="dark"`; «System» clears it | invalid value ignored |
| Unsafe next | rename with `next=https://evil.example/` | lands on the fag's P04 | N/A |

</frozen-after-approval>

## Code Map

- `core/ownership.py` -- `OwnedQuerySet`, `get_owned_or_404`; reuse.
- `core/messages.py` -- add Student-facing texts by code.
- `accounts/forms.py` `LinkedErrorsMixin`, `templates/components/text_input.html`, `inline_message.html` -- reuse for D02/D08 fields.
- `accounts/views.py` `safe_next` -- reuse the relative-only `next` rule (move to `core.http` and import from both).
- `templates/layouts/base.html` -- already sets `lang`, `hx-headers` CSRF; add `data-theme`, `<head>` scripts, `#dialog`, `#live-polite`, `#live-assertive`.
- `static/css/tokens.css`, `components.css` -- extend; `--font-sans` already names Public Sans.
- `web/views.py`, `web/urls.py`, `templates/web/home.html` -- placeholder to replace with P03.
- `tests/conftest.py` -- `student` fixture, `PASSWORD`.
- `mockups/14-fagskinnen.html` (UX folder) -- visual reference for rail, top-bar, P03, P04, P12, D01, D02, D08, D09.

## Tasks & Acceptance

**Execution:**
- [x] `courses/models.py`, `courses/migrations/0001_initial.py`, `courses/forms.py`, `courses/services.py`, `courses/views.py`, `courses/urls.py` -- Course + D02/D08/D09 (`courses:create`, `courses:rename`, `courses:delete`; URLs `/courses/new/`, `/courses/<id>/rename/`, `/courses/<id>/delete/`)
- [x] `core/http.py` -- Vary/partial decorator, `safe_next`
- [x] `web/views.py`, `web/urls.py`, `web/context_processors.py` -- P03 `/`, P04 `/courses/<id>/`, `handler404`, shell context (fag list, current fag, theme), theme POST
- [x] `templates/layouts/shell.html`, `templates/components/` (fag-rail, top-bar, fag-switcher, dialog, menu, empty-state, breadcrumb), `templates/courses/*.html`, `templates/web/{home,course,404}.html`
- [x] `static/vendor/htmx-2.0.11.min.js`, `static/js/app.js`, `static/fonts/public-sans/*` + `OFL.txt`, CSS additions
- [x] `config/urls.py`, `config/settings.py` -- routes, `handler404`, context processor
- [x] `tests/test_courses.py`, `tests/test_shell.py` -- every matrix row; plus `student` set on create, creation order, rail `aria-current`, `Vary` on partials, CSRF on every POST, Course of B never listed for A

**Acceptance Criteria:**
- Given a signed-in Student with JavaScript off, when they create, rename and delete a fag, then every step works as full pages.
- Given `uv run pytest` offline, then everything passes, including the import-graph test.
- Given 360 px and 1280 px in light and dark, when Hjem, P04, P12 and every dialog are viewed, then nothing scrolls horizontally and focus is visible.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap). No intent_gap or bad_spec; patches sent to the implementation agent; one defer.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Focus falls to `<body>` after an HX-Location submit | medium | patch | Dialog `close` never runs after the body swap; AD-18 focus rule |
| `resize` closes popovers on mobile URL-bar/keyboard changes (BH, ECH) | medium | patch | Height-only resizes fire on phones, where the fag-switcher is the navigation |
| fag-switcher list can exceed the viewport | low | patch | Top-layer popover with no max-height; many fag unreachable on a phone |
| Theme form drops the query string | low | patch | `request.path` in account_menu.html |
| HEAD on Hjem/P04 answers 405 | low | patch | `require_GET`; one-word fix |
| Comment says Hjem shares `shell_courses`; it queries again | low | patch | `home` passes its own queryset |
| Duplicate status assertion | low | patch | Copy slip |
| D08 HTMX partial never requested in tests (VG) | low | patch | Only valid HTMX POST tested |
| Failure-message templates never asserted (VG) | low | patch | `showFailure` returns silently when missing |
| Theme cookie attributes unasserted (VG) | low | patch | Only value checked |
| Missing tests: too-long rename, signed-out course URLs | low | patch | Untested paths |
| app.js dialog lifecycle only checked as source text (VG) | medium | defer | No browser/JS harness in repo; deferred-work.md |
| Duplicate ids when a page-mode dialog and the HTMX dialog coexist (BH, ECH) | low | reject | Needs JS on while on a full-page dialog URL (reload/direct link); fix adds id scoping |
| fag-switcher uses listbox roles on links | false | reject | EXPERIENCE.md specifies `aria-haspopup="listbox"` for the fag-switcher |
| `courses` imports `accounts.forms` | false | reject | courses→accounts is an allowed AD-1 edge |
| No success announcement after delete | false | reject | EXPERIENCE.md: no success message |
| P12 text wrong for signed-out visitors | false | reject | Signed-out requests are redirected to sign-in before any 404 |
| Fragile `.split` in a test | low | reject | No user or developer harm named |
| Hard-coded white on selected segment | low | reject | Renders with contrast in both themes |
| Busy style on every disabled button | low | reject | UX forbids disabled buttons outside a running request |
| `vary_on_htmx` on views without partials | low | reject | Harmless; no cache in front |
| Avbryt reloads when `next` is the dialog page itself | low | reject | Needs a page-mode dialog plus opening another; adds a guard |
| Rename after delete in another tab gives 500 | low | reject | Rare cross-tab race; adds a guard |
| Double-click with JS off creates two fag | low | reject | JS-off path only; fix needs a nonce |
| Breadcrumb with empty crumbs | false | reject | No caller passes an empty list |
| HTMX dialog for a foreign fag shows the response-error message | false | reject | That is the intended AD-18 behaviour for a 404 |

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes
- `uv run manage.py runserver` -- expected: rail at 1280 px, top-bar and fag-switcher at 360 px, dialogs open in `<dialog>` with JS and as pages without
