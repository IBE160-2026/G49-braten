# NFR-2: fresh-clone runs (implementer's machine)

Status: **passed from the GitHub URL with a cold uv cache and a freshly downloaded Python (run 2, below).** Run 1's deviations 1–3 are closed by run 2, except that both runs used the implementer's machine with uv already installed. The run on another machine is still the Author's (NFR-2, SETUP-GUIDE Part A).

## Run 2: from GitHub, cold cache (2026-11-19)

| Item | Value |
| --- | --- |
| Source | `git clone https://github.com/IBE160-2026/G49-braten.git` at `fa16e0f` (pushed the same day), into an empty temp dir |
| Isolation | empty `UV_CACHE_DIR`, empty `UV_PYTHON_INSTALL_DIR` with `UV_PYTHON_PREFERENCE=only-managed` (uv downloaded Python itself), `ANTHROPIC_API_KEY` and `AI_PROVIDER` unset |
| uv | 0.12.13 (already installed; not part of the run) |
| Python (downloaded by `uv sync`) | 3.13.15 |

| Step | Result | Wall-clock |
| --- | --- | --- |
| `git clone …` | OK | 1 s |
| `cp .env.example .env` | OK | – |
| `uv sync` | OK, downloaded Python 3.13.15 and the packages (68 MB cache) | 2 s on a fast network |
| `uv run manage.py migrate` | OK | 3 s |
| `uv run manage.py runserver 127.0.0.1:8765` | OK | ~1 s |
| `GET /` | 302 to `/accounts/sign-in/?next=/`; the page shows «Demomodus:» and «Opprett konto» | – |
| `GET /accounts/sign-up/` | 200 | – |
| `uv run pytest` | **886 passed**, sockets disabled, no Key | 101 s |

No deviation from the README; nothing to fix.

## Run 1: local clone (2026-11-19)

## Setup

| Item | Value |
| --- | --- |
| Date | 2026-11-19 |
| OS | macOS 27.2.1 (Apple silicon) |
| uv | 0.12.13 |
| Python (installed by `uv sync`) | 3.13.7 |
| Source | `git clone` of the local repository into a temp dir, at HEAD `3509f6b`, plus the story-14 working-tree files (`README.md`, `tests/test_examiner_path.py`, `tests/test_sm2_checklist.py`) copied in, since they were not committed yet |

## Steps, as written in the README

| Step | Result | Wall-clock |
| --- | --- | --- |
| `git clone …` | OK | < 1 s (local clone) |
| `cp .env.example .env` | OK | – |
| `uv sync` | OK, 29 packages | 0.1 s with a warm uv cache; 1 s with an empty package cache (Python 3.13 was already on the machine) |
| `uv run manage.py migrate` | OK, created `data/db.sqlite3` (`DATA_DIR` is created on start) | 3.9 s |
| `uv run manage.py runserver <free port>` | OK | ~1 s to serve |
| `GET /` | 302 to `/accounts/sign-in/?next=/`, which answers 200 | – |
| `GET /accounts/sign-up/` | 200, the Mock-mode banner (`class="mode-banner"`) shown | – |
| `uv run pytest` | **885 passed**, sockets disabled, no Key | 224 s |

Total from clone to a served sign-up page: under 10 s on this machine, well inside the 15-minute target. A first-time Examiner also downloads uv, Python 3.13 and the packages, which depends on their network.

## Deviations and fixes

Deviations from the README in this run (not fixed; they limit what the run proves):

1. **Local clone, not the README's URL.** The repository was cloned from the local working copy, not from `https://github.com/IBE160-2026/G49-braten.git`. The GitHub URL and what is pushed there are untested.
2. **Uncommitted files copied in.** `README.md`, `tests/test_examiner_path.py` and `tests/test_sm2_checklist.py` were not committed yet, so they were copied into the clone by hand. The clone is HEAD plus those files, not a pure commit.
3. **Warm machine, not a cold install.** uv and Python 3.13 were already installed, and uv's cache was warm (also with an empty package cache, Python came from the machine). The download time for uv, Python and the packages on a new machine is unmeasured.

Found and fixed:

- The test run takes almost 4 minutes, which the README did not say; the README's «Kjør testene» now says it takes a few minutes.

## Still open

- The NFR-2 run on another machine (ideally Windows, or without uv installed), following the README from the first line: the Author's.
