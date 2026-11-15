---
title: 'Accounts, sign-in and ownership'
type: 'feature'
created: '2026-11-15'
status: 'done'
baseline_commit: '37a2186835f57ad6a61170d0a161c0f669b1fd49'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-ai-study-buddy/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-Prosjekt A-2026-11-09/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `Student` exists but nobody can sign up, sign in or out, every route is open, and there is no shared way to load only the signed-in Student's data (CAP-1, FR-1, AD-7).

**Approach:** Add P01 «Logg inn» and P02 «Opprett konto» on an auth layout styled from DESIGN.md tokens, POST-only sign-out, sign-in required everywhere by middleware (HTMX gets `HX-Redirect`), and `core.ownership` (`for_student`, `get_owned_or_404`) so later owned models answer 404 for anything not the Student's.

## Boundaries & Constraints

**Always:**
- Email and password only. Passwords stored with Django's default slow salted hasher; validators from settings, errors in bokmål.
- Emails go through `accounts.managers.normalize()`; sign-in with any case or surrounding spaces works, including Æ/Ø/Å.
- `LoginRequiredMiddleware` on; sign-in and sign-up are `@login_not_required`. Non-HTMX gets a redirect to sign-in with `next`; an HTMX request gets `HX-Redirect` to sign-in (never the login page swapped into a region).
- After sign-in the Student lands on `next` when it is a safe relative URL, otherwise `/`. Sign-up signs the new Student in. A signed-in visit to P01/P02 redirects to `/`.
- Sign-out is POST with CSRF only; it ends the session and lands on P01.
- `core.ownership` imports no app (AD-1): `OwnedQuerySet.for_student(student)` filters `student=student`; `get_owned_or_404(model_or_queryset, student, **lookup)` raises `Http404` for missing and not-owned alike.
- Student-facing text comes from `core/messages.py` by code; bokmål, «du», no exclamation marks. Wrong credentials: «Feil e-post eller passord.»; email in use: «Det finnes allerede en konto med denne e-postadressen.» with a «Logg inn» link.
- 360 px without horizontal scroll, light and dark through `prefers-color-scheme`, labels above fields, errors linked to fields (`aria-describedby`), visible focus.

**Never:**
- Password reset, third-party login, rate limiting, remember-me.
- Closed sign-up / `SIGNUP_ALLOWED_EMAILS` gate (FR-25, story 18), mode-banner (story 5), app shell, D01 account menu, theme cookie, P12 404 page, vendored Public Sans (story 3).
- Feature models; the admin.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sign up | new `Ida@Example.no`, valid password | Student `ida@example.no` created, signed in, redirected to `/` | N/A |
| Email taken | sign up ` IDA@example.no ` when `ida@example.no` exists | P02 re-rendered, email-in-use message under the field | 200, no row added |
| Weak password | `12345678` | P02 re-rendered with validator text | 200, no row added |
| Sign in | `ØYVIND@eksempel.no` for `øyvind@eksempel.no` | signed in, redirected to `/` | N/A |
| Wrong password | known email, wrong password | P01 with «Feil e-post eller passord.» | 200 |
| Unsafe next | `?next=https://evil.example/` | lands on `/` | N/A |
| Signed out, page | GET `/` | 302 to sign-in with `next=/` | N/A |
| Signed out, HTMX | GET `/` with `HX-Request: true` | `HX-Redirect` to sign-in | 200, no page body |
| Sign out | POST sign-out | session ended, P01 | GET → 405 |
| Not owned | owned row of Student B loaded for Student A | 404, same as a missing id | `Http404` |

</frozen-after-approval>

## Code Map

- `accounts/models.py`, `accounts/managers.py` -- `Student`, `normalize()`, `get_by_natural_key` already case-insensitive; reuse, do not change the model (no migration in this story).
- `config/settings.py` -- add `LoginRequiredMiddleware` after `AuthenticationMiddleware` (replaced by the accounts subclass), `LOGIN_URL`, `LOGIN_REDIRECT_URL="/"`, `LOGOUT_REDIRECT_URL`; `HtmxMiddleware` must run before the login middleware so `request.htmx` exists.
- `config/settings_test.py` -- add the test-only app for ownership tests.
- `config/urls.py` -- empty; include `accounts.urls` and the placeholder home.
- `django_htmx.http.HttpResponseClientRedirect` -- the `HX-Redirect` response.
- `django.contrib.auth.views.LoginView` (`redirect_authenticated_user`, safe `next`), `LogoutView` (POST-only), `login_not_required` -- reuse.
- DESIGN.md frontmatter `colors:` (light keys, `-dark` twins) and the text-input, button, inline-message notes (lines ~860–882); P01 layout note at ~746.
- `tests/conftest.py` -- `freeze_now`; add a `student` factory fixture here.

## Tasks & Acceptance

**Execution:**
- [x] `core/messages.py` -- code → bokmål text dict (`wrong_credentials`, `email_in_use`) -- AD conventions
- [x] `core/ownership.py` -- `OwnedQuerySet`, `get_owned_or_404` -- AD-7
- [x] `accounts/forms.py` -- `SignInForm` (AuthenticationForm with normalised email, message by code), `SignUpForm` (email + one password, `validate_password`, case-insensitive duplicate check, IntegrityError race → same field error)
- [x] `accounts/views.py`, `accounts/urls.py` (`accounts:sign_in`, `accounts:sign_up`, `accounts:sign_out` under `/accounts/`) -- P01, P02, sign-out
- [x] `accounts/middleware.py` -- `LoginRequiredMiddleware` subclass returning `HttpResponseClientRedirect` for HTMX
- [x] `web/views.py`, `web/urls.py` -- placeholder `/` («Du er logget inn som …» and a «Logg ut» button), replaced by Home in story 3
- [x] `templates/layouts/base.html`, `templates/layouts/auth.html`, `templates/accounts/sign_in.html`, `templates/accounts/sign_up.html`, `templates/web/home.html` -- `lang="nb"`, P01 petrol pane from 1024 px
- [x] `static/css/tokens.css` -- every DESIGN.md color token as `--<name>` on `:root`, twins under `prefers-color-scheme: dark` and `[data-theme=dark]`; `static/css/components.css` -- `.text-input`, `.button-primary`, `.inline-message`, auth layout
- [x] `config/settings.py`, `config/urls.py`, `config/settings_test.py` -- wiring above
- [x] `tests/ownership_app/` (model `Note` with `student` FK, no migrations), `tests/test_ownership.py`, `tests/test_accounts.py` -- every matrix row, plus: password stored hashed, CSRF required on sign-out, session survives a new client using the same cookie

**Acceptance Criteria:**
- Given a fresh clone, when the Examiner opens `/`, then P01 appears and P02 is one link away.
- Given the whole suite, when `uv run pytest` runs offline, then all tests pass, including the import-graph test with `core.ownership` importing no app.
- Given P01 and P02 at 360 px in light and dark, when inspected, then nothing scrolls horizontally and every field has a visible label and focus ring.

## Implementation Notes

- Email inputs are `type="text"` with `inputmode="email"`: browsers refuse Æ/Ø/Å before the @ in `type="email"`. Sign-up validates with `StudentEmailValidator` (Django's `EmailValidator` with Unicode letters allowed in the local part), so an Øyvind can also sign up, not only sign in.
- `LinkedErrorsMixin` (accounts/forms.py) sets `aria-invalid` and `aria-describedby` after validation: field errors render as `<id>-error`, the wrong-credentials message as `form-error`, linked from both fields.
- An HTMX request signed out gets `next` from `HX-Current-URL` (the page the browser shows), falling back to the request path.
- Sign-out is `login_not_required`, so a stale tab's POST still lands on P01 instead of looping through sign-in to a 405.
- `static/css/tokens.css` was generated from the DESIGN.md frontmatter (54 colors with dark twins, plus `--rounded-*` and `--spacing-*`). Public Sans is named first in the font stack but not vendored (story 3).
- Added `templates/components/text_input.html` and `templates/components/inline_message.html` as the shared components the auth pages use.

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap). No intent_gap or bad_spec; patches sent to the implementation agent.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| P02 at ≥1024 px: no pane, form squeezed into 440 px column, brand hidden | medium | patch | CSS grid applies to every `.auth-shell`; P02 overrides no `pane` block |
| P01 pane `<h2>` precedes the page `<h1>` | low | patch | DOM order in sign_in.html; WCAG AA heading structure |
| Decomposed Å rejected at sign-up; sign-in NFKC vs sign-up raw | low | patch | `\w` does not match combining marks; AuthenticationForm's UsernameField applies NFKC, sign-up did not |
| Password rules shown only after a failed submit | low | patch | No help_text; component never renders it |
| «Logg inn» link in email-in-use error drops `next` | low | patch | `extra_link_url=sign_in_url` without query |
| `MultipleObjectsReturned` mapped to 404 hides caller bugs | low | patch | Fix is a deletion |
| Duplicated aria linking in `SignUpForm.save()` | low | patch | Two copies of the same rule would diverge |
| Hidden `next` on P01 untested (VG) | low | patch | Every next-test posts `next` by hand |
| Sign-up `next` untested (VG) | low | patch | No test sends `next` to P02 |
| `aria-invalid` never asserted (VG) | low | patch | grep: no test |
| Race path linkage unasserted (VG) | low | patch | Test checks message text only |
| HTMX unsafe `HX-Current-URL` fallback untested (VG) | low | patch | Cheap test; behind `safe_next` anyway |
| Missing tests: malformed/empty sign-up, stale-tab sign-out | low | patch | Behaviour promised in code comment, untested |
| Signed-in `?next=` pointing at P01/P02 loops (ValueError/302 loop) | low | reject | Middleware never produces such `next` (auth pages are login-not-required); needs a hand-crafted URL; fix adds a guard |
| `next` pointing at sign-out lands on 405 | low | reject | Same: sign-out is login-not-required, so middleware never emits it |
| Empty POST body leaves sign-up unbound | low | reject | Browsers always send the fields and the CSRF token |
| IntegrityError from another constraint shown as email-in-use | false | reject | The only constraints on Student are the two email ones |
| `pk='abc'` gives ValueError (500) | low | reject | Callers use `<int:>` converters; no caller today |
| `for_student(AnonymousUser/None)` | low | reject | All views are behind LoginRequiredMiddleware; `student` is non-null per AD-7 |
| Sign-up reveals registered emails | false | reject | EXPERIENCE.md mandates the email-in-use message |
| No rate limiting / lockout | false | reject | Spec Never: rate limiting out of scope |
| No password max length | low | reject | Local single-user app; Django has no cap by default |
| htmx script and Public Sans not loaded | false | reject | Nothing uses htmx yet; font is story 3 by spec |
| Only first non-field error rendered | false | reject | AuthenticationForm raises a single non-field error |
| `from tests.conftest import PASSWORD`; hard-coded `LOGIN_REDIRECT_URL="/"` | low | reject | Works; no named harm |

## Design Notes

The placeholder `/` exists only so sign-in has somewhere to land and sign-out a button; story 3 replaces the view and template. The ownership test model lives under `tests/` so no feature model leaks into this story's migrations.

## Verification

**Commands:**
- `uv run pytest` -- expected: all pass, no network
- `uv run manage.py check && uv run manage.py makemigrations --check --dry-run` -- expected: no issues, no changes
- `uv run manage.py runserver`, then sign up, sign out, sign in at http://127.0.0.1:8000 -- expected: matrix behaviour
