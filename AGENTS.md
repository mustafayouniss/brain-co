# Organizational Brain — Legal V1 (backend)

## Stack (non-negotiable)
Python 3.12, FastAPI, PostgreSQL (+ pgvector), SQLAlchemy 2.0, Alembic,
Pydantic v2, PyJWT, pytest. Do NOT use Node, Express, Prisma, or Neo4j.

## Source of truth order
1. docs/decisions.md  2. docs/rings/<current ring>.md  3. docs/constitution.md
If they conflict, the higher one wins. If something isn't in any of them, STOP and ask. Never invent requirements.

## Rules of behavior
- Plan first. Write the plan, wait for my approval, then code.
- One small task per turn. Don't touch files outside the task.
- Never invent library APIs. Check the installed version / official docs. Pin versions in requirements.txt.
- Every change ships with tests. Run them and show the real output. Never say "tests pass" without running them.
- Every schema change = an Alembic migration. No manual DB edits.
- Tests must only use the test_engine and db_session fixtures. Never create an engine or connection from the development DATABASE_URL inside tests.
- Permissions are enforced server-side. Case data is always filtered by case_id.
- If unsure, say "I don't know" and list what you'd need to check.
- Never mark anything as done or passing without showing evidence in this chat. If you did not verify it, write UNVERIFIED.
- Cite the Constitution by section heading only, never by page or line number. Do not read the whole Constitution again; open the specific section you need.

## Start of every task
Read, in this order: AGENTS.md, docs/progress.md, docs/decisions.md, docs/vision.md, then the current ring spec in docs/rings/. Don't start before reading.

## End of every task (task is NOT done until this is finished)
1. Update docs/progress.md (done / next / broken).
2. Add an entry to docs/journal/ for today: what was done, which commands were run, what went wrong and how it was fixed.
3. If folders, tables, or endpoints changed, update docs/architecture.md.
4. If a decision was made, add it to docs/decisions.md.
5. Explain in plain language in docs/how-it-works.md what was added.
6. Anything important created outside the repo (plans, notes) must be copied into docs/ before the task ends.
Documentation must only describe things that actually happened and were verified. Never invent. If unsure, write "UNVERIFIED".

## Safety and logging rules
- Log every command that changes anything (install, create/move/delete, docker, alembic, git) in docs/journal/<today>.md: time, exact command, result.
<<<<<<< HEAD
- Never delete any file or folder (even one you created by mistake) without first showing me the exact command and waiting for my OK.
- Never run these without first showing me the exact command and waiting for my OK: deleting files or folders, `docker compose down -v`, `docker volume rm`, `git push`, `git reset --hard`, `git clean`, any force flag, anything outside D:\Study\projects\OrgBrain, changing global or system settings.
- Stage files explicitly by path, never `git add -A` or `git add .`; if `git status` shows an unexpected file, STOP.
- Final task reports must include `git diff --cached --stat` before the commit and `git show --stat HEAD` after it, not only a summary.
- Finish every task with git status, then a commit with a clear message. Never commit .env or .venv.
- A new calendar day means creating a new `docs/journal/<YYYY-MM-DD>.md` file; otherwise append to today's file (never recreate or overwrite).
- Write markdown and journal files from PowerShell only with single-quoted here-strings `@' ... '@` or with Python, never double-quoted `@" ... "@` (a backtick followed by b or t becomes a control character), and always save as UTF-8 without BOM.
=======
- Never run these without first showing me the exact command and waiting for my OK: deleting files or folders, `docker compose down -v`, `docker volume rm`, `git push`, `git reset --hard`, `git clean`, any force flag, anything outside D:\Study\projects\OrgBrain, changing global or system settings.
- Finish every task with git status, then a commit with a clear message. Never commit .env or .venv.
>>>>>>> origin/main

## Token-saving rules
- Never read whole files that keep growing: docs/journal/* and docs/verification-log.md. Read only the last 40 lines of the latest journal, and APPEND to it.
- Never read docs/constitution.md in full; search for the section heading you need.
- Do not re-read a file you already read in this chat.
- Keep docs/progress.md short: current status, next tasks, known issues only.
- Append to journal and log files only with `Add-Content` (PowerShell) or an append-only edit. NEVER recreate or overwrite an existing file after reading only part of it.