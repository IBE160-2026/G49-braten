---
title: 'Setup guide: AI Study Buddy v1'
status: final
created: '2026-11-14'
updated: '2026-11-14'
companions: ['ARCHITECTURE-SPINE.md']
---

# Setup guide: AI Study Buddy v1

This guide covers two paths: the **Examiner's**, from a fresh clone to Mock mode without a Key, and the **Author's**, covering the Key, the checks before step 1, and the Hosted instance.

The app is not built yet, so this guide is the **target** the README must meet. When step 1 is built, Part A is copied into the README and every command is tested from a fresh clone on another machine (NFR-2). Architecture references (AD-n) point to `ARCHITECTURE-SPINE.md` in this folder.

---

## Part A: The Examiner, Mock mode without a Key (target: under 15 minutes)

### What you need

| Tool | Why | Install |
| --- | --- | --- |
| git | Clone the repository | Usually installed already. Run `git --version` to check |
| uv | Installs Python 3.13 and all dependencies, then runs the app | macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh` · Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

You don't need Python installed beforehand, nor Node, Docker, a database server, a paid account or an API key.

### Start the app

```bash
git clone <repository-url>
cd G49-braten
cp .env.example .env          # Windows: copy .env.example .env
uv sync                       # installs Python 3.13 and the dependencies
uv run manage.py migrate      # creates data/db.sqlite3
uv run manage.py runserver
```

Open <http://127.0.0.1:8000>. A banner shows that the app is running in **Mock mode** (FR-20).

### Try every core function (UJ-5)

1. Create an account with any email address and password.
2. Create a Course, then a Topic inside it.
3. Under **Kilder**, choose **«Bruk eksempeldokumentet»**. The Sample document is processed with recorded responses, and nothing is sent over the network.
4. The Topic shows the Summary, Key concepts and Flashcards, plus **one item removed** by the Reference check. The removal is deliberate and shows that the check works (FR-8).
5. Take a Practice-mode Quiz, then the Retry round with the Questions you missed.
6. Do a Review under **Test deg selv**.
7. Optional: upload any other PDF. The app stores it and says that generating Study material for it needs a Key (FR-20).

In Mock mode, Free-text Answers get a placeholder Grade, marked as mock. It tests the flow, not the quality of the grading.

### Run the automated tests

```bash
uv run pytest
```

The tests need no Key and no network; sockets are blocked during the test run (AD-15). Test names start with the FR they cover, for example `test_fr15_…`.

### If something goes wrong

| Symptom | Fix |
| --- | --- |
| `uv: command not found` | Open a new terminal after installing uv, or follow the PATH hint the installer printed |
| `no such table` | You skipped `uv run manage.py migrate` |
| Port 8000 is busy | `uv run manage.py runserver 8001` |
| A clean restart | Stop the server and delete `data/db.sqlite3`, then run `migrate` again |

---

## Part B: The Author

### B1. Real mode on your own machine

1. **Create an account** at the Anthropic Console (console.anthropic.com).
2. **Buy a small prepaid credit.** Haiku 5.5 has no free tier. Generating one 20-page PDF costs well under 1 cent (research A2), and NFR-7 caps you at 20 Generation calls a day.
3. **Set a monthly spend limit** in the Console, so a bug can never cost more than you chose.
4. **Create an API key** and put it in `.env`. Never put it anywhere else: `.env` is git-ignored, and the app never logs or displays the Key (AD-2).
   ```dotenv
   ANTHROPIC_API_KEY=sk-ant-...
   ```
5. **Restart `runserver`.** The banner disappears, and the app is in Real mode.
6. **Accept the privacy notice** on your first upload. Until you do, the app sends no Source text anywhere (FR-22, AD-17).

To run in Mock mode while the Key is set, for example to demo the Examiner's path, set `AI_PROVIDER=mock`.

If the Key leaks, for example in a commit or a screenshot, revoke it in the Console at once and create a new one.

### B2. Checks to finish before step 1 is done (20 November)

Write both results to `docs/quality/` (AD-15).

- [ ] **OQ-1: extraction test.** Pick three of your own slide decks and extract them with pypdf 7.0.1 in plain mode, with pypdf in layout mode, and with pdfplumber.
  - For each, note whether every page's text lands on the right page, how tables and two-column slides come out, and whether ligatures (fi, fl) and hyphenation break.
  - Read the pypdf 7.0 changelog.
  - Choose the library and the mode. Set `MIN_TEXT_CHARS` (the limit below which a PDF counts as scanned).
- [ ] **OQ-2: timing and limits in Real mode.**
  - Time generation for a 20-page and a 50-page PDF. The first call with a new schema is slower, so record it separately.
  - Look up your rate-limit tier in the Console (input and output tokens per minute) and check it against a 50-page prompt.
  - If generation approaches 150 s or hits the limit, lower the FR-3 limits or move FR-26 forward.

### B3. The Hosted instance (FR-25, Should: only after every Must is done)

**Decision (2026-11-14):** if no free host meets the requirements below, FR-25 is dropped from v1. The architecture doesn't change.

**Host requirements (AD-16)**

- [ ] Costs nothing
- [ ] A disk that survives restarts and redeploys, for `DATA_DIR`
- [ ] SQLite 3.37 or newer in the host's Python
- [ ] Request timeout of at least 150 s, since generation runs inside the request
- [ ] At least 2 concurrent requests
- [ ] Outbound HTTPS to `api.anthropic.com`
- [ ] Configuration through environment variables
- [ ] A way to run a daily backup

**The candidate: PythonAnywhere, free Beginner tier (OQ-3).** Create a free account and check these first:

1. Is `api.anthropic.com` on the free tier's outbound allowlist? If not, request it through their allowlist form. Free accounts can reach only allowlisted sites.
2. What are the request timeout and the number of concurrent workers on the free tier?
3. Which SQLite version does its Python 3.13 have?
4. Can a free account run a scheduled task for the backup?

If any answer is no, look for another free host or drop FR-25.

**Environment on the Hosted instance.** The app refuses to start unless all of these are set correctly (AD-14):

```dotenv
APP_ENV=production
SECRET_KEY=<long random string, generated fresh>
DEBUG=false
ALLOWED_HOSTS=<your-host-name>
CSRF_TRUSTED_ORIGINS=https://<your-host-name>
SIGNUP_ALLOWED_EMAILS=<your own email address>
DATA_DIR=<path on the persistent disk>
ANTHROPIC_API_KEY=<a separate key for the hosted instance>
```

**Every deploy, in this order (AD-16)**

1. Back up the database: `sqlite3 "$DATA_DIR/db.sqlite3" "VACUUM INTO '$DATA_DIR/backup-$(date +%F).sqlite3'"`
2. Fetch the new code and run `uv sync`.
3. Run `uv run manage.py migrate`.
4. Reload the web app.

Also run the backup daily, and keep the last 7 copies. Never copy the live `db.sqlite3` file as a backup.

---

## Environment variables (`.env.example`)

| Variable | Default when empty | Local | Hosted | Notes |
| --- | --- | --- | --- | --- |
| `APP_ENV` | `local` | – | `production` | Anything other than `local` turns on the start-up guards (AD-14) |
| `SECRET_KEY` | development key | – | required | Must not be the development key outside `local` |
| `DEBUG` | `true` locally | – | `false` | |
| `DATA_DIR` | `./data` | – | required | Holds `db.sqlite3` and backups |
| `ANTHROPIC_API_KEY` | empty, which means Mock mode | your Key for Real mode | required | Secret. Never in git, logs or the browser |
| `AI_PROVIDER` | `anthropic` when a Key is set | `mock` to force Mock | – | No Key always means Mock (FR-20) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | – | required | |
| `CSRF_TRUSTED_ORIGINS` | empty | – | required | Must include `https://` |
| `SIGNUP_ALLOWED_EMAILS` | empty, meaning sign-up is open | – | your email | Closes sign-up to these addresses (FR-25) |
