# /deploy — Deploy HewaSense to Production Server

**GOTCHA Law: Push alone is NOT deployment.** This skill enforces the full cycle.

Server: `root@37.27.200.227`
Path: `/opt/hewasense/app/phase2`
Compose file: `docker-compose.dev.yml`

## Step 0 — Local verification gate

Ask the user: **"Have you tested these changes locally with Docker?"**

- **Yes** → proceed to Step 1
- **No** → remind them of the local test command and ask if they want to test first:

```bash
docker compose -f docker-compose.dev.yml up --build frontend
# then verify at http://localhost:3000
```

Only proceed without local testing if the user explicitly confirms (e.g. docs-only change, config tweak with no visual/functional impact). Log the bypass reason in your response.

## Step 1 — Confirm scope

Ask the user which service(s) to deploy:
- `frontend` — React/Vite app (requires build step)
- `backend` — FastAPI app (requires build step)
- `all` — both services

## Step 2 — Check local git state

Run `git status` and `git log -1 --oneline` in the phase2 directory.

- If there are **uncommitted changes**: warn the user, ask if they want to commit first before deploying
- If there are **unpushed commits**: run `git push` now — the server pulls from remote

## Step 3 — Push to remote (if needed)

If the latest local commit is not yet on remote, run `git push` and confirm it succeeded.

## Step 4 — SSH and pull

```bash
ssh root@37.27.200.227
cd /opt/hewasense/app/phase2
git pull
```

Confirm the pull output shows the expected commit hash / "Already up to date."

## Step 5 — Build and restart

Run **only** the service(s) requested in Step 1:

**Frontend:**
```bash
docker compose -f docker-compose.dev.yml build frontend
docker compose -f docker-compose.dev.yml up -d frontend
```

**Backend:**
```bash
docker compose -f docker-compose.dev.yml build backend
docker compose -f docker-compose.dev.yml up -d backend
```

**All:**
```bash
docker compose -f docker-compose.dev.yml build frontend backend
docker compose -f docker-compose.dev.yml up -d frontend backend
```

## Step 6 — Verify

```bash
docker compose -f docker-compose.dev.yml ps
```

All deployed services must show status `Up`. If any show `Exit` or `Restarting`, read the logs immediately:
```bash
docker compose -f docker-compose.dev.yml logs --tail=50 <service>
```

## Step 7 — Report

Confirm to the user: which services were deployed, the commit hash now running on server, and container status.

## GOTCHA reminders
- NEVER skip the `build` step for frontend/backend — just `up -d` alone will run the old image
- Backend changes (Python only, no static assets) may only need restart (`up -d` without `build`) if you are certain the image is already current — when in doubt, always build
- The scheduler runs inside the backend container — restarting backend briefly interrupts the scheduler (it self-heals on startup, stale locks are cleared automatically)
