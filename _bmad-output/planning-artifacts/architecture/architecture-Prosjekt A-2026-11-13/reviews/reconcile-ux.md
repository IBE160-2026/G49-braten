# Reconcile: Architecture Spine vs UX (EXPERIENCE.md, DESIGN.md)

- **Spine:** `ARCHITECTURE-SPINE.md` (2026-11-13, draft). Not edited.
- **UX sources:** `ux-designs/ux-Prosjekt A-2026-11-09/EXPERIENCE.md`, `DESIGN.md` (both final, 2026-11-13). `decisions.md` holds only concept preferences (14 Fagskinnen, oversiktlig, adult tone) and adds no architectural constraint.
- **Scope:** only what matters architecturally: UX behavior AD-13 makes hard or that needs a shared mechanism the spine does not name, outright contradictions, and shared UI conventions where two builders would diverge. Screen-level detail that is not an invariant is ignored.
- **Date:** 2026-11-13

## Summary

| Severity | Count |
|---|---|
| High | 5 |
| Medium | 15 |
| Low | 10 |
| **Total** | **30** |

**Landed well (no action):** Norwegian bokmål UI with English identifiers; vendored Public Sans (answers the DESIGN.md `[ASSUMPTION]` about font loading); light and dark tokens; "UI system: architecture picks it" is answered by plain CSS on tokens; 404 for other Students' data (P12); the Grade override matches `effective_grade` (AD-9); Retry rounds excluded from mastery (AD-10); Leitner intervals produce exactly the UX return labels («i morgen», «om 3 dager», «om 1 uke»); the daily limit applies in Mock mode; errors mapped to Norwegian text in one module (`core/messages.py`) fit the UX "inline-message, never a toast" rule.

---

## High

### R-01 — Aggregating pages have no home under AD-1
- **What's missing:** Hjem, Fagoversikt and the Tema page each combine data from several apps: Course/Topic (`courses`), Summary and Key concepts (`studymat`), quiz-history (`quiz`), Due cards and forecast (`review`), mastery, trend and Weak topics (`progress`). The fag-rail (due count and mastery per fag) appears on every signed-in page, including pages served by `courses`, `studymat` and `quiz`. Under AD-1 only `progress` (or a new top app) can import all of these. A builder who puts the Tema view in `courses` (where Topic lives) gets a forbidden upward import. The spine names no app that owns page composition and no mechanism for the shell's data on every page.
- **UX reference:** EXPERIENCE Information Architecture (P03, P04, P05); Shell and navigation (fag-rail on every signed-in page); DESIGN Brand & Style (the fag rail is the overview).
- **Suggested spine fix:** Add a top-level `web` (or `pages`) app above `progress` in the AD-1 graph that owns Hjem, Fagoversikt, Tema and the shell context processor (fag-rail, «I dag · N», mode-banner); feature apps own only their own forms and sessions.

### R-02 — In-request generation needs a named two-step HTMX flow and a concurrency guarantee
- **What's missing:** The UX wants D05 to close at once, the source-row to show «Lager studiemateriell …» with a spinner, and "the tabs and other kilder work as normal meanwhile" while a request of up to ~2 minutes runs. AD-5 says only "generation runs inside the request". That leaves open:
  - whether the upload POST itself blocks for 2 minutes (the dialog hangs and no row appears) or returns a row that then fires a separate generate request (for example `hx-trigger="load"`);
  - what stops a reload, or a second tab, from firing generate again on a Source already `generating` (that is a double Generation call under AD-3 and two writers);
  - whether the single WSGI process (AD-16) serves other requests while one generation blocks. On a single-threaded worker, such as PythonAnywhere's free tier, "the rest of the page stays usable" is impossible.
- **UX reference:** EXPERIENCE State Patterns "Generating (v1)"; Interaction Primitives "Generation"; Key Flow UJ-1 steps 4 to 6.
- **Suggested spine fix:** In AD-5, state that upload stores the Source and returns its row, a separate idempotent `POST generate` runs the model (refused unless the status is `failed` or new), and AD-16 requires a threaded WSGI worker (at least 2 concurrent requests).

### R-03 — "Leaving the page stops the run" contradicts in-request WSGI generation
- **What's contradictory:** The UX says leaving or closing the page stops generation, and on return the kilde shows «Feilet» with «Genereringen stoppet fordi siden ble lukket.» Under WSGI, a client disconnect is not seen by the view. The server keeps calling the model, and the Source usually ends `ready` (the AD-3 counter has already been charged). If it is still running on return, it shows as generating, which is correct. Only the 5-minute staleness rule in AD-5 can produce `failed`, and no reason code says "page closed". Builders will either try to detect disconnects (they cannot) or show text that is untrue.
- **UX reference:** EXPERIENCE State Patterns "Generation interrupted"; Interaction Primitives "Generation" ("leaving the page stops the run (FR-9)").
- **Suggested spine fix:** In AD-5, state that leaving does not cancel a run: it completes or goes stale, and the stale reason code is `timed_out`. Ask UX to reword the message to «Genereringen ble ikke ferdig. Prøv igjen.» (wording to be confirmed by UX).

### R-04 — No convention for updating several regions after one action
- **What's missing:** Many UX actions change more than the element that triggered them:
  - delete (D09): "the item disappears and the counts and forecast update", with no success message;
  - generation completing: the source-row, the «Sammendrag» panel, the «Test deg selv · 22 kort» tab count and the band (to «Ta en quiz»);
  - a Grade override on P07 or P11: the score, the strip and the «Øv på feilene (N)» count, in place;
  - a rating: the session progress and the return-forecast.

  AD-13 says only "the same view returns a named template partial". One builder will use `hx-swap-oob`, another `HX-Refresh` or `HX-Redirect`, and a third will re-render the whole `<main>`.
- **UX reference:** EXPERIENCE State Patterns "Item deleted"; result-summary; tema-tabs; status-label.
- **Suggested spine fix:** In AD-13, add: a mutating HTMX POST either returns `HX-Location` back to its page (default), or swaps one named region plus listed `hx-swap-oob` regions (`band`, `tab-counts`, `forecast`). It never returns a success toast.

### R-05 — Dialogs (D02 to D12) have no shared mechanism
- **What's missing:** There are 11 dialogs: forms (D02, D03, D08), confirm-delete (D09), the privacy notice (D04), D05 upload, the D06, D10 and D11 setups, and D12. The UX requires that each:
  - opens over the current surface and is a bottom sheet below 600 px;
  - closes with Esc and «Avbryt»;
  - keeps focus inside, starts focus on its title and returns focus to its trigger;
  - is never stacked;
  - shows validation errors in place;
  - for D09, names exactly what is deleted and repeats the verb on a destructive button.

  AD-13 ("every URL renders a full page") does not say whether a dialog has a URL, what that URL renders without HTMX, where the dialog container lives, or how a successful submit closes it. `hx-confirm` (the browser's native confirm) is the obvious shortcut, and it breaks D09.
- **UX reference:** EXPERIENCE dialog, Interaction Primitives "Destructive actions", Accessibility Floor "Focus"; DESIGN dialog.
- **Suggested spine fix:** In AD-13, add: each dialog is a GET URL that renders a standalone page normally and, under HTMX, a `<dialog>` partial into one `#dialog` slot in `base.html` (opened with `showModal()` by one shared JS file). A valid submit answers with `HX-Location`, an invalid one re-renders the dialog, and `hx-confirm` is banned.

---

## Medium

### R-06 — The AD-13 rule "request.htmx → partial" breaks history restore and caching
- **What's missing:** The tema-tabs keep the tab in the URL "so the browser's back button and a shared link return to it", which needs `hx-push-url`. On a history-cache miss, htmx 2 re-requests the URL with `HX-Request: true` and `HX-History-Restore-Request: true`. A view that follows AD-13 literally returns a bare partial as the whole page. Without `Vary: HX-Request`, the browser cache can also serve a partial for a normal navigation. When one view has several partials (tab panel, row, dialog), the spine does not say how the view picks one.
- **UX reference:** EXPERIENCE tema-tabs (selected tab in the URL, back button).
- **Suggested spine fix:** Change AD-13 to: return the partial only when `request.htmx and not request.htmx.history_restore_request`, choose it by `request.htmx.target`, and always send `Vary: HX-Request` (django-htmx `vary_on_headers`).

### R-07 — The next-step-band has no data contract or owner beyond FR-28
- **What's missing:** The band is "exactly one per page" on P03, P04, P05, P07 and P11. It always has the same shape: size number and unit, imperative heading, why line, one button with a URL, «ca. N min», or else a calm-message or nothing. FR-28 (`progress`) covers only Hjem and Fagoversikt. The bands on Tema and Resultat are a "UX-level extension" that no app owns, and the «ca. N min» estimate has no rule (UX `[ASSUMPTION]`). Without one data shape and one template, builders will produce bands that look and behave differently.
- **UX reference:** EXPERIENCE Next step (band, row, calm-message, the priority rule, the per-page action table); DESIGN next-step-band.
- **Suggested spine fix:** Add a convention row: every band comes from a `NextStep` dataclass `(size, unit, heading, why, button_label, url, minutes) | Calm(text) | None` rendered by one `components/next_step_band.html`, built by `progress.next_step(...)` (or by `web`, see R-01), with the minute constants in `progress/rules.py`.

### R-08 — The theme override and the dark-token mapping are not specified
- **What's missing:**
  - **Storing the override.** The UX has «Utseende» (System, Lys, Mørk) in D01, and the choice has to persist. It needs storage (a user field or a cookie) and a server-rendered `data-theme` on `<html>` to avoid a flash of the wrong theme on full-page loads.
  - **Token naming.** DESIGN.md names dark values as `-dark` twins (`ground-dark`). CSS must redefine the same custom property (`--ground`) under `@media (prefers-color-scheme: dark)` and under `[data-theme=dark]`. A builder who references `--ground-dark` directly breaks theming.
  - **Location.** The spine does not say where the tokens live or how they stay in sync with the DESIGN.md frontmatter.
- **UX reference:** EXPERIENCE Foundation "Themes", D01; DESIGN colors frontmatter, "Dark theme (designed, not inverted)".
- **Suggested spine fix:** Add: `static/css/tokens.css` holds every DESIGN.md token as `--<name>`, light on `:root` and redefined for dark under `prefers-color-scheme` and `[data-theme=dark]`; the override is a `theme` cookie read by a context processor into `<html data-theme>`.

### R-09 — Errors in HTMX responses and network loss have no convention
- **What's missing:** The UX sends every problem (generation failed, rate limit, daily limit, grading failed, Key rejected, network lost on a rating) to an inline-message in place, with «Prøv igjen», and never to a toast. By default htmx 2 does not swap 4xx or 5xx responses, so a view that returns 422 or 503 with error HTML shows nothing. A network failure (`htmx:sendError`) produces no response at all, yet UJ-2 needs "the rating was not saved … the card stays".
- **UX reference:** EXPERIENCE inline-message; State Patterns "Network lost"; UJ-2 Failure.
- **Suggested spine fix:** In AD-13, add: an expected failure returns 200 (or 422 with `htmx.config.responseHandling` set to swap it) with the `components/inline_message.html` partial, and the one shared JS file renders a fixed inline-message on `htmx:sendError` and `htmx:responseError`.

### R-10 — Double-submit and the busy state are not specified
- **What's missing:** "While an action runs, the button keeps its label, shows a spinner and ignores further presses." Without a shared rule, a double tap on a rating rates a card twice, a double click on «Prøv igjen» or «Lag ny» charges two Generation calls (AD-3), and a double «Svar» saves two Answers. The client-side rule (`hx-disabled-elt`, `hx-indicator`, `hx-sync`) and server-side idempotency are both unnamed.
- **UX reference:** EXPERIENCE button; rating-buttons ("a rating saves at once").
- **Suggested spine fix:** Add: every mutating control sets `hx-disabled-elt="this"` and `hx-sync="closest form:drop"`; `rate()`, answer-save and `generate()` are idempotent per (card, review position) or (quiz, question) or (Source status).

### R-11 — "Return to where the session started" has no mechanism
- **What's missing:** The session exit («Avslutt»), «Tilbake» on results and the P12 links must "return to the surface the session started from". The same Quiz can start from P05, D10, P07 or P11. Builders will pick different routes: the HTTP Referer header, a `?next=` parameter, or a field stored on the Quiz. The Referer route breaks after a reload or a history restore.
- **UX reference:** EXPERIENCE Navigation rules "Sessions"; result-summary «Tilbake».
- **Suggested spine fix:** Add: each session stores `return_url` (validated with `url_has_allowed_host_and_scheme`) when created (on `Quiz`, or in the Review session); exit links read only that field.

### R-12 — Reload-safe state for the Review round, and for Quiz or exam position, is unowned
- **What's missing:** AD-13 says every URL renders a full page, so a reload in mid-session must restore it. Repetisjon needs persistent round state:
  - «1 av 14» and the progress bar;
  - cards rated «Igjen» returning "before the Review ends";
  - the end summary «Du repeterte 14 kort»;
  - the per-day cap of 20 new cards.

  AD-11 has only `ReviewState(box, due_date)`, which holds none of this. The exam's free «Forrige/Neste» navigation needs a position (URL or server). Builders will spread this state across the Django session, query strings and JS.
- **UX reference:** EXPERIENCE session-bar; rating-buttons; State Patterns "End of Review", "Daily limit on new cards", "Moving around in an exam".
- **Suggested spine fix:** In AD-11, add a `Review` session record (student, date, card queue, ratings count) and a `ReviewState.introduced_on` for the 20-a-day cap; Quiz and exam position is a URL parameter, derived from saved Answers when it is missing.

### R-13 — The exam clock must be authoritative on the server, but the spine defers it to "a small JS file"
- **What's missing:**
  - "The clock keeps running" while the tab is closed, and the exam resumes with the correct remaining time.
  - At 0 the Answers are submitted even if the Student is away.
  - Answers can change until «Lever».

  All of this needs `started_at`, `time_limit` and `submitted_at` on `Quiz`, a lazy auto-submit on the next request after the deadline, and refusal of Answers after it. AD-9 says "an Answer is saved as soon as it is given" and does not say whether an exam Answer is updated or appended. The Deferred entry treats the timer as presentation only.
- **UX reference:** EXPERIENCE exam clock; State Patterns "Exam left mid-way", "Time running out", "Moving around in an exam".
- **Suggested spine fix:** In AD-9, add: an `exam` Quiz stores `started_at`, `time_limit` and `submitted_at`; the server rejects Answers after the deadline and auto-submits on the next request; an exam Answer is updated in place until submit; the JS timer only displays the time.

### R-14 — Grading exam Free-text Answers after submission can exceed the 150 s timeout
- **What's missing:** At «Lever», P11 shows «12 av 18 rettet · Retter 2 fritekstsvar …» and says "Mestringen oppdateres når alle svarene er rettet. Du kan vente her eller gå tilbake." With 20 Questions at up to 15 s each (NFR-3), grading in the submit request can pass the 150 s limit in AD-16. The UX implies incremental grading, but the spine does not say who grades, when, or how P11 learns of progress.
- **UX reference:** EXPERIENCE State Patterns "Grading after submission"; P11.
- **Suggested spine fix:** In AD-9 or AD-13, add: submit saves the exam and redirects to P11, which grades each `not_graded` Free-text Answer through one HTMX request per Answer (`hx-trigger="load"`), so no single request grades more than one.

### R-15 — "Checked before upload … Nothing is uploaded" cannot hold for the page count
- **What's contradictory:** The UX says size, type **and length** are checked before upload, and that a 70-page PDF is rejected with "nothing uploaded". A browser can check size and type cheaply. A PDF's page count needs a PDF parser such as pdf.js, which a vendored-only, no-build setup will not carry. The spine places the upload limits in `ingestion` (server) without saying which checks run where.
- **UX reference:** EXPERIENCE upload-panel; State Patterns "Upload rejected"; UJ-1 Failure.
- **Suggested spine fix:** Add to the `ingestion` row or AD-13: a small JS file checks size and type before sending; the page limit is enforced by the server, which discards the file and stores nothing; the UX wording "nothing is uploaded" means "nothing is kept".

### R-16 — URL shape in the UX contradicts the spine's URL and ID conventions
- **What's contradictory:** The UX example `…/normalisering?fane=quiz` uses a Norwegian slug and a Norwegian query parameter. The spine requires English URLs and integer `BigAutoField` IDs. The UX marks the tab-in-URL rule as `[ASSUMPTION]`, but builders copying the example will mix the two styles.
- **UX reference:** EXPERIENCE tema-tabs.
- **Suggested spine fix:** Add to Conventions: URLs are `/<plural-noun>/<id>/…` with English query keys (`?tab=summary|quiz|selftest|sources`); no slugs in v1.

### R-17 — Focus moves and live regions after HTMX swaps are not specified
- **What's missing:**
  - **Focus moves.** After an Answer, focus goes to the feedback-panel heading; after «Neste spørsmål», to the next Question; after a dialog closes, back to its trigger.
  - **Polite live regions.** Needed for the source-row status, card progress and the return-forecast sentence.
  - **Assertive live regions.** Needed for errors that block the current action.

  Swapping a live region's own element stops screen readers from announcing it, so live regions must persist in the DOM and only their contents change. Without a shared rule, builders will place `autofocus`, `aria-live` and JS focus calls in different ways.
- **UX reference:** EXPERIENCE Accessibility Floor "Announcements", "Focus".
- **Suggested spine fix:** Add: swapped content marks its focus target with `autofocus` (htmx honors it); `base.html` holds two permanent live regions (`#live-polite`, `#live-assertive`) that are filled through `hx-swap-oob="innerHTML"`; a swap never replaces the live-region elements themselves.

### R-18 — Component partials, CSS files and class names are not named
- **What's missing:** The spine says "partials defined inside the page template" and `templates/` holds "shared partials". DESIGN.md names about 40 components (`fag-rail`, `next-step-band`, `mastery-meter`, `forecast-chart`, `source-row`, `inline-message`, `empty-state` and others), and most appear on several pages owned by different apps. The spine is silent on:
  - **Shared component markup:** `{% include %}`, `{% partialdef %}` in a shared file, or an inclusion tag;
  - **Component files:** where they live;
  - **CSS files:** one file or one per component;
  - **Class names:** whether they follow the DESIGN component names.

  Two builders will produce two `mastery-meter`s.
- **UX reference:** DESIGN Components (all); EXPERIENCE Component Patterns.
- **Suggested spine fix:** Add a convention row: a shared component is `templates/components/<design-name>.html` used through `{% include %}` with explicit `with` arguments; its CSS uses the class `.<design-name>` (BEM-style modifiers) in `static/css/components.css` after `tokens.css`; a component is never redefined per app.

### R-19 — Pages cannot render the daily-limit and Mock-mode states before acting
- **What's missing:** The daily-limit message "comes before anything is sent, never after a wait", and the control that would send a call "stays inactive with the message beside it" in D05, «Prøv igjen», the Detail level, «Forklar enklere» and «Lag ny». D05 offers «Bruk eksempeldokumentet» only in Mock mode, and the mode-banner shows on every page, including P01 and P02. This needs a read-only `ai` query, separate from AD-3's atomic check-and-increment, that any page can render. Under AD-1, `ingestion` and `courses` cannot import `ai`, so D05 cannot read it from there.
- **UX reference:** EXPERIENCE State Patterns "Daily limit reached", "Mock mode"; upload-panel; mode-banner.
- **Suggested spine fix:** In AD-3, add `ai.gateway.remaining_today(student)` and `ai.gateway.mode()` as read-only queries exposed to templates by a context processor; the D05 view lives in `studymat` or `web`; AD-3's check-and-increment stays the only gate.

### R-20 — Base layouts are not named, and the 404 page needs the shell
- **What's missing:** The UX has four page frames:
  - the signed-in shell: fag-rail at ≥ 1024 px, top-bar and fag-switcher below;
  - the session frame: session-bar, next-step-row, no rail;
  - the signed-out frame: P01 and P02 with a 440 px pane and the mode-banner;
  - P12, which keeps the fag-rail ("Nothing about the data is shown").

  Django's default `handler404` has no shell context, so P12 with the rail needs a custom handler that uses the R-01 shell context. The spine lists only `base.html`.
- **UX reference:** EXPERIENCE Navigation rules; State Patterns "Not found"; DESIGN Layout & Spacing "The shell", "Sessions".
- **Suggested spine fix:** Name `base.html` → `layouts/shell.html`, `layouts/session.html`, `layouts/auth.html`, and add a custom `handler404` that renders P12 in `shell.html` for signed-in users.

---

## Low

### R-21 — Skeletons on first load have nothing to do in server-rendered pages
- **What's contradictory:** The UX shows a skeleton when Hjem, Fagoversikt or Tema take more than 300 ms to load. A full server-rendered page arrives complete, so there is nothing to show a skeleton in, unless sections are lazy-loaded through HTMX, which AD-13 does not suggest.
- **UX reference:** EXPERIENCE skeleton; State Patterns "First load".
- **Suggested spine fix:** In AD-13, add: pages render complete with no lazy sections in v1; skeletons are not built (ask UX to drop them).

### R-22 — Keyboard shortcuts need one shared handler
- **What's missing:** The sessions use these keys: 1 to 4 for options and ratings, Enter to answer or advance, Space to flip, ← and → in Bla i kort. Key hints show from 1024 px. Scattered inline `onkeydown` handlers will conflict with text inputs and with each other.
- **UX reference:** EXPERIENCE Interaction Primitives "Keyboard"; next-step-row.
- **Suggested spine fix:** Add: one `static/js/keys.js` maps `data-key="1"` attributes to clicks and skips focused inputs; templates declare keys and never bind them.

### R-23 — Icons have no source or mechanism
- **What's missing:** DESIGN uses 2 px stroke line icons at 16, 20 and 24 px throughout: status, trend arrows, practice-tag, timer, book, pencil. The spine vendors fonts but says nothing about icons. Builders may use inline SVG copies, an icon font from a CDN (forbidden), or a sprite.
- **UX reference:** DESIGN Shapes "Icons".
- **Suggested spine fix:** Add `static/icons/sprite.svg` (one vendored line-icon set) and an `{% icon "name" %}` template tag to Structural Seed and Conventions.

### R-24 — Trend definitions are missing from the progress rules
- **What's missing:** The trend-label (per tema: the point change from the latest session that changed mastery; per fag: how many tema went up or down) and P11's «Endring» are computed values that AD-10 does not list. They are also UX `[ASSUMPTION]`s. Without a rule, the Hjem and P11 builders will each define "session" and "change" their own way.
- **UX reference:** EXPERIENCE trend-label; result-summary (P11).
- **Suggested spine fix:** Extend AD-10: trend is computed on read in `progress` as the Topic score before and after the latest non-retry Quiz with Answers in the Topic.

### R-25 — The return-forecast preview needs a read-only scheduling query
- **What's missing:** The rating-buttons show the real next date for each rating, and the return-forecast previews the target day on focus or hover. Without a server round trip, this needs all four outcomes computed when the page renders. AD-11 makes `rate()` the only mutator but names no read-only preview, so a builder might call `rate()` in a dry-run transaction, or repeat the interval logic in JS.
- **UX reference:** EXPERIENCE rating-buttons; return-forecast.
- **Suggested spine fix:** In AD-11, add a pure `review.rules.next_due(state, rating, today)` used by both `rate()` and the page, which renders the four previews into `data-` attributes for a small JS file.

### R-26 — The forecast's "only cards with a date" rule needs a nullable `due_date`
- **What's missing:** The forecast counts "only Due cards that already have a date", and new Flashcards enter Due today at most 20 per day. Under AD-11 every Flashcard has a `ReviewState` with a `due_date`. If new cards get today's date at creation, the forecast and «I dag · N» count all of them at once.
- **UX reference:** EXPERIENCE forecast-chart `[ASSUMPTION]`; State Patterns "Daily limit on new cards".
- **Suggested spine fix:** In AD-11, add: a new card has `due_date = NULL` until it is introduced into a day's Due today; forecasts count non-null dates only.

### R-27 — Page titles must follow HTMX navigation
- **What's missing:** Each surface needs its own `<title>` («Normalisering – Databaser – AI Study Buddy»). When tab switches push a URL, the partial must carry a `<title>` or the old title stays.
- **UX reference:** EXPERIENCE Accessibility Floor "Page titles".
- **Suggested spine fix:** Add: any partial swapped with `hx-push-url` includes its page `<title>`, which htmx applies.

### R-28 — Menus (D01, D07) have no named mechanism
- **What's missing:** The «⋯» and account menus open at their trigger and close on Esc or a click outside. The «⋯» trigger is separate from the row link. A builder could reach for `<details>`, the native `popover` attribute or custom JS.
- **UX reference:** EXPERIENCE menu; Interaction Primitives "Pointer".
- **Suggested spine fix:** Add: menus use the native `popover` attribute and `popovertarget`, with no custom JS.

### R-29 — Background generation (FR-26) will need status polling
- **What's missing:** With FR-26, "on return the source-row shows the current status, and Study material that finished meanwhile is shown", with polite announcements. That needs polling of the row (`hx-trigger="every 5s"` while generating), which the Deferred entry does not mention.
- **UX reference:** EXPERIENCE State Patterns "Generating in the background (Should)".
- **Suggested spine fix:** In Deferred (FR-26), add: the source-row polls its own URL every 5 s while `effective_status == generating` and stops polling once the status is final.

### R-30 — Deleting a Question in mid-session is not covered
- **What's missing:** «Slett spørsmålet» in the feedback-panel (D09, during P06) cascades the Answer away under AD-8. The live Quiz then has to handle a missing Question: the strip «4 av 10» and the next-question order. The spine does not say how the Quiz order relates to deleted Questions.
- **UX reference:** EXPERIENCE feedback-panel; State Patterns "Item deleted".
- **Suggested spine fix:** In AD-9, add: a Quiz stores its ordered Question ids and skips those that no longer exist; the Quiz's own counts derive from the remaining Questions.
