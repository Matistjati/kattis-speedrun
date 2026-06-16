# CLAUDE.md

Guidance for working in this repository.

## What this is

A live "Kattis speedrun" contest app: users log in with just a username, submit
solutions to [Kattis](https://open.kattis.com) problems, and a background worker relays
each submission to Kattis, records the verdict, and broadcasts an updated queue +
leaderboard to all connected clients over WebSocket.

Flask + Flask-SQLAlchemy (SQLite) + Flask-Login + Flask-SocketIO. Submissions are
relayed to Kattis through the vendored `kattis-cli/submit.py`.

## Running it

```bash
source environ.sh                 # sets FLASK_APP=backend.app:create_app, PYTHONPATH=.:./kattis-cli
python3.12 backend/app.py         # serves on 0.0.0.0:5000 (debug reloader on)
```

- **Use `python3.12`, not `python3`.** On this machine bare `python3` is 3.10 and lacks
  the dependencies; the project's packages (Flask, lxml 6.x, etc.) live under 3.12, which
  is also what the `flask` CLI uses.
- First-time DB setup: `flask init_db` creates the schema and seeds the single `SpeedRun`
  row. The DB lives at `instance/app.db`.
- **Kattis auth:** submissions require `~/.kattisrc` (the `[user]` token + `[kattis]`
  URLs). Without it, `submit.py` calls `sys.exit(1)`, which the queue worker now catches.
- The background judging thread starts in `app.py`'s `__main__` block (gated on
  `WERKZEUG_RUN_MAIN`), so it runs under the reloader child — look for
  `[main] Starting queue runner` in the log.

## Deployment (dev.progolymp.se)

Deployed on the `po` host (`webmaster@37.152.61.245`, alias `po` in `~/.bashrc`) at
`~/dev/kattis-speedrun`, served at **https://dev.progolymp.se**.

- **Production entry point:** `serve.py` — starts the judging thread and runs
  `socketio.run(..., debug=False, allow_unsafe_werkzeug=True)` (the `__main__` reloader
  gate means a plain import wouldn't start the worker). Binds `127.0.0.1:5000` (override
  via `HOST`/`PORT`).
- **systemd:** `/etc/systemd/system/kattis-speedrun.service` (runs as `webmaster`, the
  venv python, `Restart=on-failure`, enabled at boot).
- **nginx:** `/etc/nginx/sites-available/kattis-speedrun.nginx` proxies to `:5000` with a
  dedicated `/socket.io` location carrying the WebSocket upgrade headers. TLS via certbot
  (auto-renew); HTTP→HTTPS redirect. HTTPS is required because `SESSION_COOKIE_SECURE=True`.
- **Kattis auth:** `.kattisrc` lives in the **project root** (the service's cwd) on the
  server, not `~`. `submit.py`'s `get_config()` checks cwd first; `.kattisrc` is gitignored.
- **Deploy is git-based.** The server dir is a clone tracking `origin/master`. Commit +
  push, then run the deploy script on the host (uses your forwarded SSH agent — go through
  the `po` alias, which is `ssh -A`):
  ```bash
  git push origin master
  ssh -A po 'cd ~/dev/kattis-speedrun && ./deploy.sh'
  ```
  `deploy.sh` does `git pull --ff-only`, `pip install -r requirements.txt` into the venv,
  and `sudo systemctl restart kattis-speedrun`. `instance/` (DB + secret key) and
  `.kattisrc` are gitignored, so the pull never touches the live DB or the Kattis token.
- **Sync the DB up** (overwrites the server's, e.g. seeding from local): stop the service
  first for a clean SQLite copy —
  `sudo systemctl stop kattis-speedrun`, `rsync instance/app.db …:~/dev/kattis-speedrun/instance/app.db`,
  `sudo systemctl start kattis-speedrun`.
- Logs: `ssh -A po 'journalctl -u kattis-speedrun -f'`.

## Architecture

- `backend/app.py` — app factory (`create_app`), blueprint registration, `/` and
  `/debug/db` routes, the SocketIO handlers, `init_db` CLI command, and
  `load_secret_key()` (see gotchas). Starts the judging thread.
- `backend/models.py` — `User` (username-only, no password), `Submission`, `SpeedRun`,
  and the `Status` enum.
- `backend/login/` — `login.py` (username-only, auto-creates the account on first login),
  `logout.py`.
- `backend/model/`
  - `submit_route.py` — `/submit`: accepts the code textarea **or** uploaded files
    (single/multi). Uploaded files are stored in `Submission.source_code` as a JSON
    list `[{name, content}, ...]`; the textarea path stores a plain string.
  - `submission_queue.py` — `/queue` page.
  - `eventhandler.py` — the worker loop: picks the hardest unjudged submission, relays it
    to Kattis, records the verdict, re-emits the queue. Wrapped in try/except so one bad
    submission can't kill the thread.
  - `make_submission.py` — `write_submission_files()` materializes a submission to disk
    (multi-file keeps real filenames so Kattis detects the main file/language; textarea
    uses `SUFFIX_MAP`, incl. Rust `.rs`), then calls `submit.submit()`.
- `backend/data_emit/queue_data.py` — builds the `queue_data` payload (pending, judged
  with `kattis_url`, leaderboard, token refresh) and emits it over SocketIO. Submission
  times are stored naive-UTC and rendered in `Europe/Stockholm` (DST-aware) by
  `_local_time()` at emit time — don't store local time. The pending list is the 10
  **hardest** unjudged submissions (`order_by(problem_difficulty.desc()).limit(10)`),
  matching the worker's hardest-first judging order; with >10 pending the easy tail is
  intentionally not shown.
- `backend/scraping/get_difficulty.py` — scrapes a problem's difficulty (used as the
  queue priority). Difficulty can be a single value (`"3.4"`) or a range (`"1.7 - 1.9"`);
  the scraper regex-extracts all numbers and returns the **max** (returns `None` on a bad
  shortname, which `/submit` rejects with "Invalid problem shortname").
- `kattis-cli/submit.py` — vendored + customized: `submit(problem, files)` returns
  `(verdict, cpu_time, score, kattis_submission_id)` (or an int = seconds until the next
  submission token), instead of acting as a CLI.
- `frontend/` — Jinja templates (`base.html` is the shared layout/nav) and static
  CSS/JS. `static/js/submit.js` handles drag-and-drop upload and infers shortname +
  language from filenames. `static/js/queue.js` renders the live queue/leaderboard.

## Gotchas / conventions

- **Never run table-wide `DELETE` / `Model.query.delete()` on `instance/app.db`.** It is a
  live DB that can contain real user data at any time; this has caused data loss. To clean
  up your own test rows, delete by the exact usernames/ids you created, or use a throwaway
  DB for verification.
- `SECRET_KEY` is persisted to `instance/secret_key` (via `load_secret_key`, overridable
  with the `SECRET_KEY` env var) so a reload/restart doesn't invalidate everyone's session
  cookie. Don't go back to a per-start random key.
- Login is **username-only** — there are no passwords and no `/register`. First login with
  a new username auto-creates the account.
- Scoring: leaderboard weight = `(best_score / 100) * problem_difficulty`, taking each
  user's best submission per problem. `queue.js` renders each leaderboard score to one
  decimal (`toFixed(1)`), right-aligned with `tabular-nums` via the `.lb-score` span.
- Editing `.py` files trips the Werkzeug reloader (brief restart); editing templates /
  CSS / JS is hot (no restart). Prefer the hot path for live tweaks — the app runs live.
- A standalone CLI submitter lives at `~/temp/openkattis/submit.py` (outside the repo):
  logs in username-only via `requests.Session`, then multipart-uploads file(s) to
  `/submit`, inferring shortname/language from filenames. Needs the
  `ngrok-skip-browser-warning` header against the ngrok URL.
- `instance/app.db` and `instance/secret_key` are gitignored.
