---
title: 'Project skeleton, environment settings and test harness'
type: 'chore'
created: '2026-11-14'
status: 'done'
baseline_commit: 'b7ec0f1c8730bf60af68cdef46a00f9ad1604dee'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-ai-study-buddy/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/SETUP-GUIDE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There is no application code. Every later story needs the Django project, the module layout, environment-driven settings that start with an empty `.env`, and a Key-free test harness that enforces the module graph.

**Approach:** Create the uv-managed Django 6.1 project with all ten apps from the architecture as empty modules, settings read from the environment (AD-14), `core.time` (AD-12), the custom user model from the first migration (AD-7), and pytest-django with sockets blocked and an import-graph test (AD-1, AD-15).

## Boundaries & Constraints

**Always:**
- Commands from SETUP-GUIDE Part A work: `uv sync`, `uv run manage.py migrate`, `uv run manage.py runserver`, `uv run pytest`. No Docker, no Node.
- An empty or missing `.env` starts the app locally on SQLite at `DATA_DIR/db.sqlite3` (default `./data`, created on start) with the effective AI provider `mock`.
- No `ANTHROPIC_API_KEY` means `mock` whatever `AI_PROVIDER` says; `AI_PROVIDER=mock` forces mock even with a Key.
- When `APP_ENV` is not `local`, start-up refuses unless: non-default `SECRET_KEY`, `DEBUG` off, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` set, secure session and CSRF cookies, admin disabled.
- `USE_TZ=True`, `TIME_ZONE="Europe/Oslo"`; `core.time.today()` returns the Oslo date, `core.time.now()` an aware datetime.
- SQLite: WAL, `transaction_mode: "IMMEDIATE"`, busy timeout ≥ 5 s; `ATOMIC_REQUESTS` off (AD-19).
- `accounts.Student` is `AUTH_USER_MODEL` in the very first migration: `email` is `USERNAME_FIELD`, lower-cased on save, unique under `Lower("email")`; nullable `privacy_accepted_at`.
- The Key never appears in logs or settings output.

**Never:**
- No sign-up or sign-in views, login middleware, pages, templates or CSS (later stories).
- No AI gateway, adapters or `anthropic` import (story 5 and 10).
- No feature models beyond `Student`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fresh clone | no `.env`, no `data/` | `migrate` creates `data/db.sqlite3`; effective provider `mock`; `DEBUG` on | N/A |
| Key set | `ANTHROPIC_API_KEY=x` | effective provider `anthropic` | N/A |
| Forced mock | Key set, `AI_PROVIDER=mock` | effective provider `mock` | N/A |
| Unsafe prod | `APP_ENV=production`, default `SECRET_KEY` | start-up fails naming the unmet setting | `ImproperlyConfigured` |
| Safe prod | `APP_ENV=production`, all guards met | settings load | N/A |
| Email case | Student saved as `Ida@Example.no` | stored as `ida@example.no`; second `IDA@example.no` rejected | `IntegrityError` |
| Oslo midnight | frozen UTC 2026-11-14 23:30 | `today()` is 2026-11-15 | N/A |

</frozen-after-approval>

## Code Map

Greenfield: only planning docs exist. Repo root is `G49-braten/` (Structural Seed in ARCHITECTURE-SPINE).
- `.gitignore` -- has `.env` and Python caches; lacks `data/`.
- `_bmad-output/planning-artifacts/architecture/architecture-Prosjekt A-2026-11-13/ARCHITECTURE-SPINE.md` -- app list, import graph (mermaid under Invariants & Rules), Stack versions.
- `.../SETUP-GUIDE.md` -- "Environment variables" table is the source for `.env.example`.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock`, `.python-version` -- uv project, Python 3.13, deps and pytest config from Stack (Django 6.1.3, django-htmx 1.29.0, pydantic 2.14.3, python-dotenv 1.2.4; dev: pytest-django, pytest-socket) -- pinned, Examiner path
- [x] `manage.py`, `config/{settings,urls,wsgi}.py` -- env-driven settings with the guards, SQLite options, effective `AI_PROVIDER` setting -- AD-14, AD-19
- [x] `core/` (`apps.py`, `time.py`) and `accounts/`, `courses/`, `ai/`, `ingestion/`, `studymat/`, `quiz/`, `review/`, `progress/`, `web/` as registered empty apps -- AD-1 layout
- [x] `accounts/models.py`, `accounts/managers.py`, `accounts/migrations/0001_initial.py` -- `Student` -- AD-7
- [x] `.env.example` -- every variable from SETUP-GUIDE, no secret filled; `.gitignore` -- add `data/`
- [x] `tests/conftest.py`, `tests/test_settings.py`, `tests/test_time.py`, `tests/test_student_model.py`, `tests/test_import_graph.py` -- matrix cases; import-graph test parses every app's imports and fails on edges outside the AD-1 graph (reachability counts; `core` imports no app; only `ai` may import `anthropic`)

**Acceptance Criteria:**
- Given a fresh clone with no `.env`, when the SETUP-GUIDE Part A commands run, then migrate succeeds and runserver serves without error.
- Given the test suite, when `uv run pytest` runs offline, then all tests pass and any socket use fails the test.
- Given a test module that adds `from quiz import x` inside `studymat`, when the import-graph test runs, then it fails naming the edge.

## Implementation Notes

- Implemented directly in the session (no subagent). 40 tests pass offline in ~4 s.
- `config/env.py` holds the env rules as pure functions (`effective_ai_provider`, `production_problems`, `get_bool`, `get_list`); `config/settings.py` applies them at import, so a misconfigured non-local start raises `ImproperlyConfigured` naming every unmet setting.
- An empty value counts as unset (`DEBUG=` keeps the local default), so a copied `.env.example` works.
- Secure cookies are forced on outside `local`; the admin is never installed.
- `tests/conftest.py` sets `AI_PROVIDER=mock` before settings load and provides `freeze_now`, which patches `core.time.now` (`today()` derives from it).
- Settings tests start Django in a subprocess with an explicit environment and a temporary `DATA_DIR`, so the developer's `.env` cannot leak in (`shell --no-imports` keeps output clean).
- Extra: `tests/test_harness.py` proves sockets are blocked (AD-15); the Student model also has a case-insensitive sign-in test and a `bulk_create` test for the `Lower("email")` constraint.
- `config/urls.py` is empty; runserver answers 200 with Django's default debug page until story 2/3 add routes.

## Spec Change Log

## Review Triage Log

Pass 1 (Blind Hunter, Edge Case Hunter, Verification Gap). No intent_gap or bad_spec; patches applied in-session, 51 tests pass.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| conftest sets AI_PROVIDER after pytest-django loads settings | medium | patch | Reproduced: `ANTHROPIC_API_KEY=sk-fake pytest` failed. Fixed with `config/settings_test.py` + subprocess test |
| Sign-in `email__iexact` is ASCII-only on SQLite (Øyvind) | medium | patch | Reproduced: SQLite `'Ø' like 'ø'` is 0. Lookup now uses Python-normalised exact match; non-ASCII test added |
| Sign-in lookup does not strip whitespace | low | patch | Shared `normalize()` in manager; test added |
| Whitespace-only email passes `if not email` | low | patch | Normalise before the check; test added |
| `date_joined` default binds the original `core.time.now` | low | patch | Default is now `joined_now()` calling `time.now()` at run time; frozen-time test added |
| Unknown `AI_PROVIDER` accepted silently without a Key | low | patch | Validate before the no-Key return; test covers both cases |
| Invalid boolean refusal untested | low | patch | Test added |
| Production `DEBUG` default (empty means off) untested | low | patch | Test added |
| WAL/synchronous only checked in config, not on a connection | low | patch | Subprocess test reads `PRAGMA journal_mode`/`synchronous` |
| `run_django` leaks unlisted variables (e.g. SIGNUP_ALLOWED_EMAILS) from .env | low | patch | Now blanks every `.env.example` variable |
| `.gitignore` `data/` matches at any depth | low | patch | Changed to `/data/` |
| `--allow-unix-socket` contradicts "any socket use fails" | low | patch | Flag removed; suite still passes |
| `DATA_DIR` with `~` not expanded | low | patch | `expanduser()` added |
| `settings.APP_ENV` duplicates `is_local` and is unused | low | patch | Deleted |
| `unique=True` plus `Lower()` constraint look redundant | low | patch | Comment added: unique=True satisfies Django's USERNAME_FIELD check |
| Missing HTTPS hardening (SSL redirect, HSTS, proxy header, ALLOWED_HOSTS=*) | medium | defer | Real for a Hosted instance; values depend on the host (OQ-3). Logged in deferred-work.md |
| `update()`/`bulk_create` bypass lower-casing | false | reject | Spec says lower-cased on save; the `Lower()` constraint still blocks case duplicates |
| Cookie and admin guards can never fail at start-up | false | reject | By design: settings force them; the guard is defence in depth, tested directly |
| CSRF_TRUSTED_ORIGINS scheme not checked | low | reject | Django's own system check rejects schemeless origins; extra guard adds a branch |
| Import-graph misses dynamic imports, string model refs, `config/`/`tests/` | low | reject | Unlikely in this codebase; detection adds complexity |
| `DATA_DIR.mkdir` at import; unwritable dir gives raw OSError | low | reject | AD-14 says DATA_DIR is created on start; rare, wrapping adds a branch |
| Key-leak test cannot fail | low | reject | Smoke check only; the Key is not printed anywhere in this story |
| pytest not pinned / no uv.lock in diff | false | reject | uv.lock was excluded from the review diff only; it pins every transitive version |
| IPv6/DNS not covered by socket test | low | reject | pytest-socket blocks `socket.socket` for every family; extra cases add little |
| `accept_privacy()` referenced but missing | false | reject | Comment names the future writer (story 10); nothing calls it yet |
| `create_superuser` exists although the admin is off | false | reject | Superseded by the walkthrough change below |
| Password validators omit similarity/numeric | low | reject | Sign-up is story 2's scope |
| No route or smoke test for the middleware stack | low | reject | runserver verified serving; routes arrive in story 2–3 |
| Nothing forbids `datetime.now()` outside `core.time` | low | reject | Convention; an AST check adds machinery for no current caller |

Walkthrough (2026-11-15): `PermissionsMixin`, `is_staff` and `create_superuser` removed before push — admin is off and there is one role, so the groups/permissions tables and superuser flag had no reader. `0001_initial` regenerated in place (commit was unpushed); 51 tests pass.

## Design Notes

`Student` lands now, not in story 2, because Django cannot swap `AUTH_USER_MODEL` after the first `migrate` (AD-7). Settings guard checks run in `config/settings.py` at import so a misconfigured Hosted instance never starts.

## Verification

**Commands:**
- `uv sync && uv run manage.py migrate && uv run manage.py check` -- expected: no errors, `data/db.sqlite3` exists
- `uv run pytest` -- expected: all pass, no network
- `APP_ENV=production uv run manage.py check` -- expected: fails naming `SECRET_KEY`
