---
review: verification (reality check of versions and assumed behaviour)
target: ../ARCHITECTURE-SPINE.md (draft, 2026-11-13)
lens: "Every committed decision web-researched or reality-checked, not asserted from training data"
checked: 2026-11-13/14 against the PyPI JSON API, the npm registry, official docs, upstream source (htmx 2.0.11 dist, pypdf 7.0.1 wheel, Django stable/6.1.x on GitHub), GitHub API, MDN browser-compat-data 8.1.9
spine edited: no
---

# Verification review: AI Study Buddy v1 architecture spine

## Verdict

The Stack is current and every named technology exists. Most of the behaviour the spine relies on works as assumed. Eight items are **wrong or incomplete** and four are **unverified**. None of them changes the paradigm. They are rule-level fixes to AD-7, AD-13, AD-18, AD-2 and to the Stack, Deferred and OQ sections. The largest gaps:

1. The `Vary` and history-restore rule in AD-13 is incomplete.
2. Claude Haiku 5.5 thinks by default, and AD-2 does not account for that.
3. pytest-django 4.14.0 does not officially support Django 6.1.
4. The FR-26 route assumes a database worker that Django does not ship.
5. Case-insensitive email login is not something Django provides.

Status key: **verified** = confirmed against a live source. **wrong** = the spine's claim or rule is incorrect or incomplete as written. **unverified** = could not be confirmed and needs a check.

## Summary table

| # | Item | Status |
| --- | --- | --- |
| S1 | Python 3.13; Django needs ≥ 3.12 | verified |
| S2 | uv 0.12 | wrong (out of date) |
| S3 | Django 6.1.3 | verified (note: SQLite ≥ 3.37) |
| S4 | django-htmx 1.29.0 supports Django 6.1 | verified (note: its tag vendors htmx 2.0.10) |
| S5 | htmx 2.0.11 is the current 2.x and npm `latest` | verified |
| S6 | anthropic 2.8.0 "brings in pydantic < 3" | verified, with a fix (declare pydantic ≥ 2 directly) |
| S7 | `claude-haiku-5-5` exists | verified |
| S8 | pypdf 7.0.1 | verified |
| S9 | python-dotenv 1.2.4 | verified |
| S10 | pytest-django 4.14.0 supports Django 6.1 | wrong (works, but not officially) |
| D1 | `{% partialdef %}` + rendering `"t.html#name"` from a view | verified (note on `inline`) |
| D2 | Django 6 Tasks framework "with a database-backed worker" (Deferred) | wrong |
| D3 | `LoginRequiredMiddleware`; "only sign-in, sign-up and static files are exempt" | verified, with gaps |
| D4 | Custom user model, email as `USERNAME_FIELD`, case-insensitive unique | wrong (case-insensitivity is not built in) |
| H1 | `request.htmx`, `.target`, `.history_restore_request` | verified (note: `target` can be `None`) |
| H2 | HX-Location helper | verified (`HttpResponseLocation`) |
| H3 | "Such views send `Vary: HX-Request`" | wrong (incomplete) |
| X1 | htmx 2 history restore request headers | verified; the spine misses the config switch |
| X2 | `hx-disabled-elt="this"` | verified |
| X3 | `hx-sync="closest form:drop"` | verified (caveat outside forms) |
| X4 | 4xx/5xx not swapped by default | verified |
| X5 | `htmx:sendError` / `htmx:responseError` | verified |
| X6 | `autofocus` honoured after swap | verified (source only, not in the docs) |
| X7 | "A partial swapped with `hx-push-url` carries its `<title>`" | wrong (incomplete: placement matters) |
| X8 | HX-Location reloads `<body>`, including scripts | unverified risk |
| A1 | Structured output via `output_config.format`, GA | verified |
| A2 | Citations incompatible with structured output | verified |
| A3 | Reject `refusal` and `max_tokens` stop reasons | verified; incomplete (also `model_context_window_exceeded`) |
| A4 | Per-request timeout and `max_retries`; grading gives up in about 15 s | verified API; budget arithmetic wrong |
| A5 | Haiku 5.5 thinking, effort and sampling defaults | wrong (not addressed in the spine) |
| A6 | Key-free tests "network access blocked" with SDK 2.x (httpx2) | unverified |
| B1 | Native `popover` | verified |
| B2 | `<dialog>.showModal()` | verified (note: `closedby`) |
| O1 | Host must run FR-26 worker and bundle SQLite ≥ 3.37 | unverified (OQ-3 extension) |
| O2 | PythonAnywhere free tier facts (memlog line 29) | unverified (already flagged in the spine as OQ-3) |

Counts: **wrong 8** (S2, S10, D2, D4, H3, X7, A3/A4 combined as one, A5), **unverified 4** (X8, A6, O1, O2). A3 and A4 are counted once: both are "the error and timeout contract in AD-2 is under-specified".

---

## Stack

### S1. Python 3.13 (Django requires ≥ 3.12): verified
- PyPI `Django` 6.1.3: `requires_python >=3.12`, with classifiers 3.12 to 3.15. The release notes say: "Django 6.1 supports Python 3.12, 3.13, 3.14, and 3.15 (as of 6.1.3)."
- The local interpreter is 3.13.7, matching memlog line 15.
- Evidence: https://pypi.org/pypi/django/json, https://github.com/django/django/blob/stable/6.1.x/docs/releases/6.1.txt

### S2. uv 0.12: wrong (out of date)
- PyPI `uv` latest is **0.13.8**. 0.12.13 is only what happens to be installed locally (memlog line 15).
- Evidence: https://pypi.org/pypi/uv/json
- **Fix:** write either "uv ≥ 0.12 (tested with 0.12.13)" or update to 0.13.x after a quick `uv sync` check. The README's 15-minute Examiner path (NFR-2) should name a minimum version, not a stale exact one.

### S3. Django 6.1.3: verified
- It is the latest release on PyPI (uploaded 2026-11-03; 6.0.10 and 5.2.19 came out the same day).
- **Note:** Django 6.1 raised the minimum SQLite to **3.37.0** (release notes, backwards-incompatible changes). Local Python bundles SQLite 3.50.4, which is fine. The Stack row "SQLite: bundled with Python" is only safe if the Hosted instance's Python bundles ≥ 3.37. Add this to the OQ-3 host checks.
- Evidence: https://pypi.org/pypi/django/json, https://github.com/django/django/blob/stable/6.1.x/docs/releases/6.1.txt

### S4. django-htmx 1.29.0 supports Django 6.1: verified
- It is the latest release (2026-08-05). It depends on `django>=5.2` and declares the classifier `Framework :: Django :: 6.1`.
- The 1.28.0 changelog says "Add Django 6.1 support". 1.28.0 also dropped Django 4.2 to 5.1.
- **Note:** 1.29.0's `{% htmx_script %}` tag ships its own vendored **htmx 2.0.10**, while the spine vendors 2.0.11 in `static/js/htmx.min.js`. Use one source only. The simplest choice is the spine's own file, and not using `{% htmx_script %}`.
- Evidence: https://pypi.org/pypi/django-htmx/json, https://django-htmx.readthedocs.io/en/latest/changelog.html

### S5. htmx 2.0.11 (vendored): verified
- npm dist-tags are `{"latest": "2.0.11", "next": "4.0.1"}`, and 2.0.11 was published 2026-09-22.
- htmx.org says 4.0 is released but "not currently marked as `latest`… We will mark it `latest` at some point in 2027." The site's docs and quick start still target 2.0.11.
- Choosing 2.x is sound for v1.
- Evidence: https://registry.npmjs.org/htmx.org, https://htmx.org/

### S6. anthropic 2.8.0 (brings in pydantic < 3): verified, with a fix
- It is the latest release (2026-11-10), with Python ≥ 3.10. Its requirements are `pydantic<3,>=1.10.0` and `httpx2<3,>=2.0.0`.
- The SDK permits pydantic **1.10**, but `ai/schemas.py` uses Pydantic directly, and the spine assumes v2 APIs and SDK v2 helpers.
- SDK 2.0.0 and later send `anthropic-version: 2026-10-21` by default. On that version, any `temperature`, `top_p` or `top_k` returns 400. The spine sets none of them, but the rule belongs in AD-2.
- Evidence: https://pypi.org/pypi/anthropic/json, https://pypi.org/pypi/pydantic/json (latest 2.14.3)
- **Fix:** add `pydantic>=2,<3` as a direct dependency in the Stack. In AD-2, add: "no sampling parameters".

### S7. Claude Haiku 5.5, `claude-haiku-5-5`: verified (see A5 for what the spine misses)
- The models overview lists the Claude API ID and alias `claude-haiku-5-5`, a 1M-token context and 128K max output.
- Thinking is "Adaptive", and default effort is `medium`. Retirement is "not sooner than October 7, 2027".
- Pricing starts at $0.10 / $0.50 per MTok for prompts up to 100K tokens, and is $0.50 / $2.50 for longer prompts. The spine's rule of an input ceiling below 100k tokens (Conventions) therefore also keeps the lower rate. Say so explicitly, so nobody raises the ceiling casually.
- Evidence: https://platform.claude.com/docs/en/about-claude/models/overview

### S8. pypdf 7.0.1 [PROVISIONAL]: verified
- It is the latest release (2026-11-10), after 7.0.0 on 2026-11-06.
- The 7.0.0 changelog covers deprecation cleanup, dropping Python 3.9, cryptography ≥ 43 and security hardening. It lists no change to text extraction. 7.0.1 adds the performance fix "Don't parse content streams without text operators in extract_text()".
- The 7.0.1 wheel source has `PageObject.extract_text(..., extraction_mode: Literal["plain", "layout"] = "plain", **kwargs)` in `pypdf/_page.py` lines 2191 to 2273. Both the per-page `extract_text()` and `extraction_mode="layout"` still exist.
- OQ-1 still stands, because extraction quality is an empirical question.
- Evidence: https://pypi.org/pypi/pypdf/json, https://pypdf.readthedocs.io/en/latest/meta/CHANGELOG.html, and the wheel `pypdf-7.0.1-py3-none-any.whl`

### S9. python-dotenv 1.2.4: verified
- It is the latest release (2026-10-01), with Python ≥ 3.10 and no dependencies.
- Evidence: https://pypi.org/pypi/python-dotenv/json

### S10. pytest-django 4.14.0 with Django 6.1: wrong (works, but not officially supported)
- 4.14.0 is the latest release (2026-08-10 14:13 UTC). Its classifiers list only Django **5.2 and 6.0**.
- PR #1288 "Adds support for Django 6.1" was merged at 2026-08-10 20:42 UTC, after the 4.14.0 release. `main` is 4 commits ahead of `v4.14.0`. The changelog lists "Official Django 6.1 support" under **v4.15.0 (unreleased)**.
- The PR only touched CI, tox, README, classifiers and the changelog, with no plugin code. 4.14.0's tox already tested `dj61` and `djmain`. In practice it should work.
- Evidence: https://pypi.org/pypi/pytest-django/json, https://github.com/pytest-dev/pytest-django/pull/1288, https://pytest-django.readthedocs.io/en/latest/changelog.html
- **Fix:** in the Stack, write "pytest-django 4.14.0 (Django 6.1 support unofficial until 4.15.0; no code change upstream)". Bump the version when 4.15.0 ships. Make the first Key-free test run part of step 1 so a problem shows up early.

## Django 6.x features

### D1. Template partials: verified (one note)
- `{% partialdef name %}…{% endpartialdef %}` and `{% partial name %}` are new in Django 6.0. A view renders one partial with `render(request, "authors.html#user-info", ctx)`, and `{% include "authors.html#user-info" %}` also works.
- **Note:** a partial only appears in the full page if it is defined with `{% partialdef name inline %}` or used through `{% partial name %}`. Without `inline`, the definition renders nothing in place. The AD-13 rule "every URL renders a full page" depends on this, so add "partials that are also regions of the page are declared `inline`" to the Templates convention.
- Evidence: https://docs.djangoproject.com/en/6.1/ref/templates/language/ (template partials section)

### D2. "Django 6's Tasks framework with a database-backed worker" (Deferred, FR-26): wrong
- `django.tasks` exists (`@task`, `.enqueue()`, `TASKS` setting). Django ships only `ImmediateBackend` (the default, which runs tasks synchronously) and `DummyBackend`, both "for development and testing only". The docs say Django "does not provide a worker mechanism to run Tasks."
- The database backend and the `db_worker` command now live in the third-party package **`django-tasks-db` 0.13.0** (`django_tasks_db.DatabaseBackend`). Its classifiers declare Django 5.2 and 6.0, **not 6.1**. The older `django-tasks` 0.12.0 is now only a backport for Django < 6.
- A worker is a **second, always-running process**. AD-16's host requirements do not cover this, and PythonAnywhere free (the candidate) is not known to offer one.
- Evidence: https://docs.djangoproject.com/en/6.1/topics/tasks/, https://pypi.org/pypi/django-tasks-db/json, https://pypi.org/pypi/django-tasks/json
- **Fix:** in Deferred, write "Django 6 `django.tasks` with the third-party `django-tasks-db` backend and a `db_worker` process (check its Django 6.1 support when FR-26 starts)". Add "can run a second long-lived process" to the FR-26 host check in OQ-3, or note that FR-26 may need a different route on the free host.

### D3. `LoginRequiredMiddleware`: verified, with gaps in the exemption rule
- The middleware is `django.contrib.auth.middleware.LoginRequiredMiddleware`, placed **after** `AuthenticationMiddleware`. Views opt out with `@login_not_required`. It has overridable `get_login_url`, `get_redirect_field_name` and `handle_no_permission(request, view_func)` (6.1 source).
- Django's own `LoginView` and the password-reset views are already decorated with `login_not_required` in 6.1. `LogoutView` is not.
- Static files are not something you exempt. Under `runserver`, the staticfiles handler serves `/static/` before the middleware runs, and on a host they are served outside Django. "Static files are exempt" is therefore a non-action, not a rule.
- **Gaps:**
  - (a) The custom sign-up view must carry `@login_not_required`, and so must any public privacy or "about" page, if one exists.
  - (b) When a session expires, an **HTMX** request gets a 302 to the login page. The XHR follows it, and htmx swaps the login page **into the target region**. Override `handle_no_permission` so that, when `request.htmx` is set, it returns `HX-Redirect` (`django_htmx.http.HttpResponseClientRedirect`) to the login URL.
- Evidence: https://docs.djangoproject.com/en/6.1/ref/middleware/, https://github.com/django/django/blob/stable/6.1.x/django/contrib/auth/middleware.py, https://github.com/django/django/blob/stable/6.1.x/django/contrib/auth/views.py

### D4. Custom user, email `USERNAME_FIELD`, case-insensitive unique: wrong (not built in)
- Verified:
  - `USERNAME_FIELD` must be unique.
  - `AUTH_USER_MODEL` must be set before the first migration, and the model must be in the app's `0001_initial`.
  - A custom `BaseUserManager` with `create_user` and `create_superuser` is needed.
  - `REQUIRED_FIELDS` must not contain the `USERNAME_FIELD`.
- Not provided: case-insensitivity. `normalize_email()` lowercases **only the domain**. `ModelBackend` looks users up with an exact `get_by_natural_key`.
- Evidence: https://docs.djangoproject.com/en/6.1/topics/auth/customizing/
- **Fix:** add to AD-7:
  - store `email` lowercased (in the manager and the forms);
  - add `UniqueConstraint(Lower("email"), name=…)`;
  - override `get_by_natural_key` to use `email__iexact` (or lowercase before lookup).
- Name the test `test_fr1_email_case_insensitive`.

## django-htmx

### H1. `request.htmx`, `.target`, `.history_restore_request`: verified (one note)
- `bool(request.htmx)` is true when `HX-Request: true` is sent. `.target` reads `HX-Target`, and `.history_restore_request` reads `HX-History-Restore-Request`.
- In htmx 2.0.11, `HX-Target` is the target element's **`id` without `#`** (`'HX-Target': getAttributeValue(target, 'id')`).
- **Note:** `.target` is `None` when the target has no id. One case is the default `<body>` target of an HX-Location follow-up GET. The AD-13 rule should read: "a named partial only when `request.htmx`, not a history restore, **and `request.htmx.target` names a known region**; otherwise the full page".
- Evidence: https://django-htmx.readthedocs.io/en/latest/middleware.html, https://htmx.org/reference/ (request headers), and htmx 2.0.11 `dist/htmx.js` line 3756

### H2. HX-Location helper: verified
- `django_htmx.http.HttpResponseLocation(redirect_to, *, source, event, target, swap, select, values, headers)`.
- htmx 2.0.11 handles `HX-Location` with an ajax GET (`push` defaults to `'true'`) and returns early.
- Evidence: https://django-htmx.readthedocs.io/en/latest/http.html, htmx.js lines 4867 to 4878

### H3. "Such views send `Vary: HX-Request`": wrong (incomplete)
- django-htmx documents no Vary helper. Use Django's `vary_on_headers` or `patch_vary_headers`.
- The response of these views depends on **three** request headers:
  - `HX-Request`;
  - `HX-Target`, because the partial is chosen by target;
  - `HX-History-Restore-Request`, because in htmx 2.0.11 `historyRestoreAsHxRequest` defaults to **true**, so a history-restore request also sends `HX-Request: true` (htmx.js lines 281 and 3368 to 3371).
- With only `Vary: HX-Request`, a cache can serve a partial for target A to a request for target B, or to a history restore.
- **Fix:** send `Vary: HX-Request, HX-Target, HX-History-Restore-Request` (one decorator in `core`). Also see X1.

## htmx 2.0

### X1. History-restore header behaviour: verified; config switch missing
- On a cache miss, htmx GETs the URL with `HX-History-Restore-Request: true`, plus `HX-Request: true` while `historyRestoreAsHxRequest` is true (the default), and expects the whole page.
- The config comment in the 2.0.11 source says: "This should always be disabled when using HX-Request header to optionally return partial responses". htmx docs give the same recommendation.
- **Fix:** in AD-13, add "`app.js` (or a `<meta name="htmx-config">`) sets `historyRestoreAsHxRequest: false`". Keep the server-side history-restore check as defence in depth.
- Evidence: https://htmx.org/docs/ (history section), htmx.js line 281

### X2. `hx-disabled-elt="this"`: verified
- `findAttributeTargets()` special-cases `'this'` (htmx.js line 1352). The attribute adds `disabled` while the request is in flight (reference).
- Evidence: https://htmx.org/reference/, htmx.js lines 1349 to 1355 and 3443

### X3. `hx-sync="closest form:drop"`: verified (caveat)
- The value is split on `:`. The selector goes through `querySelectorExt`, which supports `closest …`, and the strategy defaults to `drop`. A second request on the same sync element is dropped while one is in flight.
- **Caveat:** on a control **not inside a `<form>`** (for example a standalone rating button), `closest form` resolves to nothing. Use `hx-sync="this:drop"` there.
- **Fix:** in AD-18, add "`closest form:drop` inside forms, `this:drop` otherwise".
- Evidence: htmx.js lines 4381 to 4398

### X4. 4xx/5xx not swapped: verified
- The default `responseHandling` is `[{code:'204',swap:false},{code:'[23]..',swap:true},{code:'[45]..',swap:false,error:true}]`.
- This fits AD-18: expected failures return 200 with the inline message, and AD-7's 404s fall through to `htmx:responseError`.
- Evidence: https://htmx.org/docs/, htmx.js lines 264 to 268

### X5. Event names: verified
- `htmx:sendError` is "a network error prevents an HTTP request". `htmx:responseError` is "non-200 or 300 response code".
- Evidence: https://htmx.org/reference/, htmx.js lines 4656 and 5020

### X6. `autofocus` honoured after swap: verified (source only)
- `processFocus()` focuses the first `[autofocus]` in newly added content during settle (htmx.js lines 1576 to 1593). The htmx docs do not document this behaviour, so pin it with a Key-free template test, or with a manual check in `docs/quality/`, in case a future 2.x changes it.
- The `autofocus` attribute itself is supported in Chrome 79+, Safari 15.4+ (iOS 16.4+) and Firefox 110+ (MDN BCD).

### X7. `<title>` in swapped content: wrong (incomplete)
- By default (`ignoreTitle: false`), htmx updates `document.title`. For a non-full-document response, it only picks up a `<title>` that is a **top-level node of the partial** (htmx.js lines 629 to 639). A `<title>` nested inside the partial's wrapper element is ignored.
- htmx applies the title on **every** swap, not only with `hx-push-url`.
- **Fix:** in AD-13, write "a partial that changes the URL emits `<title>` as its first top-level node; other partials emit no `<title>`".
- Evidence: https://htmx.org/docs/ ("swap in the title of a title tag found anywhere in the new content"), htmx.js lines 608 to 645 and 2042 to 2044

### X8. HX-Location reloads `<body>`: unverified risk
- The HX-Location follow-up GET targets `<body>` and swaps the body of the full page that comes back. Any `<script>` inside `<body>` (for example `static/js/app.js`) is re-inserted and can run again, which would double-bind `data-key` handlers and the dialog listeners.
- **Fix:** load `htmx.min.js` and `app.js` in `<head>` with `defer`, and make `app.js` bind once with delegated listeners on `document`. Confirm this in the first HTMX story.

## Anthropic SDK and API

### A1. Structured output via `output_config.format`: verified
- The docs page has status "stable", and no beta header is used. The old `output_format` request parameter is deprecated (it needs the `structured-outputs-2025-11-13` beta header, otherwise it returns 400).
- In Python, `client.messages.parse(..., output_format=PydanticModel)` is still the helper, and it sends `output_config`.
- `claude-haiku-5-5` is in the supported models list.
- Schema limits match AD-2: no recursion, no numeric or `minLength`/`maxLength` constraints, `additionalProperties: false`, and at most 24 optional parameters and 16 union-typed parameters per request. Keep fields required.
- Enum casing is "not guaranteed", which confirms AD-2's lower-casing rule.
- Evidence: https://platform.claude.com/docs/en/build-with-claude/structured-outputs

### A2. Citations incompatible with structured output: verified
- The docs say: "The API returns a 400 error if citations are enabled with `output_config.format`." Message prefilling is also incompatible.
- Evidence: the same page, "Feature compatibility"

### A3. Stop reasons: verified; rule incomplete
- `"refusal"` and `"max_tokens"` exist. The full set is `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal` and `model_context_window_exceeded`. `stop_details` is set only for `refusal`.
- Claude Haiku 5.5 runs safety classifiers (categories `cyber`, `bio`, `frontier_llm`, `general_harms`), and it has **no server-side fallback**.
- The structured-output page warns that a schema field asking for "thinking or step-by-step reasoning" can trigger a `reasoning_extraction` refusal.
- **Fix:** in AD-2, write "accept only `stop_reason == "end_turn"`; `refusal` → `Refused`, `max_tokens` or `model_context_window_exceeded` → `Truncated`, anything else → `InvalidFormat`". Name explanation fields `explanation`, never `reasoning`.
- Evidence: https://platform.claude.com/docs/en/api/handling-stop-reasons, the structured-outputs page ("Invalid outputs")

### A4. Per-request timeout and `max_retries`: API verified; budget arithmetic wrong
- Use `client.with_options(timeout=…, max_retries=…).messages.create(...)` or `.parse(...)`. `timeout` is in seconds or an `anthropic.Timeout`. `max_retries` defaults to 2, and the SDK retries 408, 409, 429, 5xx and connection errors.
- **Timeouts are retried.** Wall-clock time can reach `timeout × (max_retries + 1)`.
- A schema's first use also adds grammar-compilation latency (cached for 24 h from last use).
- **Fix:** in AD-2, for `grade_free_text`, write "`max_retries=0` (or 1) and `timeout` chosen so that the total stays at or under 15 s". In `docs/quality/` timings, record a first-call (cold schema) timing as part of OQ-2.
- Evidence: SDK README (https://github.com/anthropics/anthropic-sdk-python), the structured-outputs page ("first time you use a specific schema… additional latency")

### A5. Haiku 5.5 thinking, effort and sampling defaults: wrong (not addressed in the spine)
- On `claude-haiku-5-5`, adaptive thinking is **on when `thinking` is omitted**, and effort defaults to `medium`.
- **Thinking tokens count toward `max_tokens`.** A tight `MAX_OUTPUT_TOKENS` can end in `stop_reason: "max_tokens"` after a thinking block with no JSON, which would show up as spurious `Truncated` failures.
- A response can start with `thinking` blocks, so code must read blocks **by type**.
- `thinking: {"type": "disabled"}` is allowed only at effort ≤ `high`. Sampling parameters return 400 (see S6).
- Thinking also adds latency, which affects NFR-3 and the 15 s grading budget.
- **Fix:** in AD-2, add "each operation sets `output_config.effort` explicitly (start at `low` for `grade_free_text` and `simpler_explanation`; tune generation in OQ-2); `MAX_OUTPUT_TOKENS` includes headroom for thinking; the adapter reads the text block by type". Add the effort level to the OQ-2 measurements.
- Evidence: https://platform.claude.com/docs/en/about-claude/models/overview (Thinking: Adaptive; Default effort: medium), the Haiku 5.5 migration notes in the Claude API docs (https://platform.claude.com/docs/en/about-claude/models/migration-guide)

### A6. "Network access blocked" in Key-free tests with SDK 2.x: unverified
- anthropic 2.x uses **`httpx2`**, not `httpx`. Mock libraries such as `respx` or `pytest-httpx` patch `httpx` and would not intercept or block it.
- With `AI_PROVIDER=mock` the SDK is never called, so the risk is low. But the rule "network access blocked" needs a mechanism that works.
- **Fix:** block at the socket level (for example `pytest-socket` with `--disable-socket`, version to be verified when added), and pin the chosen package in the Stack.

## Browser support (NFR-1)

### B1. Native `popover` attribute: verified
- Supported in Chrome and Chrome Android 114+, Safari and iOS Safari 17+, and Firefox 125+. It is standard-track and not experimental, so all current browsers support it.
- Phones on iOS < 17 get no menu. If the PRD's phone target includes older iPhones, write the minimum in NFR-1 or the README.
- Evidence: MDN browser-compat-data 8.1.9 `html.global_attributes.popover`, https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/popover

### B2. `<dialog>.showModal()`: verified (note)
- Supported in Chrome 37+, Safari and iOS 15.4+, and Firefox 98+.
- **Note:** the newer `closedby` attribute (light dismiss) needs Chrome 134, Firefox 141 and **Safari 27.3**. Do not rely on it. Keep Esc and backdrop closing in `app.js` (Esc is native through the `cancel` event).
- Evidence: MDN BCD 8.1.9 `api.HTMLDialogElement.showModal`, `html.elements.dialog.closedby`, https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal

## Other items not confirmed

### O1. Host constraints from the findings above: unverified
- Add these to OQ-3: Python on the host bundles SQLite ≥ 3.37 (S3), and the host can run a long-lived worker process if FR-26 is taken (D2).

### O2. PythonAnywhere free-tier facts: unverified
- Memlog line 29 records medium-low confidence: allowlist membership of `api.anthropic.com`, request timeout and concurrency are unconfirmed. The spine already carries this as OQ-3. No change needed beyond O1.

## What the memlog claims and what was re-checked

Memlog line 15 ("Verified 2026-11-13 against PyPI/npm JSON") was re-checked, and every version matches the live registries. Only uv is behind (S2), and that row recorded the local install rather than the latest release.

The verification did not cover behavioural claims: Vary and history restore, title placement, Tasks worker, case-insensitive email, Haiku thinking defaults, and pytest-django's Django 6.1 status. Those are the findings above.
