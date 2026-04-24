# HewaSense Data Protection Policy

**Effective:** 2026-04-24
**Last Updated:** 2026-04-24

This policy governs all data handling, backup, and deployment operations for the HewaSense platform. It exists because a destructive deployment action on 2026-04-24 destroyed 9 days of live shadow run pipeline data. This must never happen again.

---

## 1. Database Protection Rules

### 1.1 NEVER Delete or Destroy Database Volumes
- **No `docker compose down`** on any stack that has a running database. Use `docker compose stop` or restart individual containers instead.
- **No `--remove-orphans`** flag when other stacks share the Docker environment.
- **No `docker volume rm`** or `docker volume prune`** without explicit written approval.
- **No `docker system prune`** on production servers.

### 1.2 NEVER Recreate Database Containers Unnecessarily
- If only the frontend or backend changed, restart **only that container**: `docker compose up -d frontend`
- Never tear down the full stack to fix a single service.
- If a database container must be recreated, **take a backup first** (see Section 3).

### 1.3 NEVER Run Destructive SQL Without Backup
- No `DROP DATABASE`, `DROP TABLE`, `TRUNCATE`, or `DELETE FROM` on production without a verified backup taken in the same session.
- The `wipe_shadow_run_data.py` script requires `--confirm` flag and should only be used with Walter's explicit approval.

---

## 2. Deployment Rules

### 2.1 Safe Deployment Procedure
When deploying code changes to production:

1. **Pull the code** on the server: `git pull origin main`
2. **Build only the changed service**: `docker compose -f docker-compose.prod.yml build <service>`
3. **Restart only the changed service**: `docker compose -f docker-compose.prod.yml up -d <service>`
4. **Verify** the service is healthy: `docker ps`, `curl` health endpoints

### 2.2 Forbidden Commands on Production
| Command | Why |
|---------|-----|
| `docker compose down` | Destroys all containers including DB |
| `docker compose down --remove-orphans` | Removes containers from other stacks |
| `docker compose down -v` | Destroys volumes (permanent data loss) |
| `docker volume prune` | Removes all unused volumes |
| `docker system prune` | Removes everything unused |
| `docker rm <db_container>` | Removes database container |

### 2.3 Allowed Commands on Production
| Command | Use Case |
|---------|----------|
| `docker compose up -d <service>` | Start/recreate a single service |
| `docker compose restart <service>` | Restart without rebuilding |
| `docker compose build <service>` | Rebuild a single service image |
| `docker compose stop <service>` | Stop without removing |
| `docker compose logs <service>` | View logs |

---

## 3. Automated Backup Policy

### 3.1 Daily Automated Backup
- **Schedule:** Daily at 05:00 EAT (1 hour before pipeline run)
- **Method:** `pg_dump` of the full `climate_dev` database, gzipped
- **Location:** `/opt/hewasense/backups/` on the production server
- **Retention:** 30 days of daily backups, auto-pruned
- **Script:** `/opt/hewasense/backup_db.sh`
- **Cron:** `0 5 * * * /opt/hewasense/backup_db.sh >> /opt/hewasense/backups/backup.log 2>&1`

### 3.2 Pre-Deployment Backup
Before ANY deployment that touches the database, backend, or docker-compose:

```bash
ssh root@37.27.200.227 "/opt/hewasense/backup_db.sh"
```

Verify the backup was created before proceeding.

### 3.3 Backup Verification
Weekly manual check that backups are being created:

```bash
ssh root@37.27.200.227 "ls -la /opt/hewasense/backups/"
```

### 3.4 Restore Procedure
To restore from a backup:

```bash
# Stop the backend and scheduler (NOT the database)
docker compose -f docker-compose.prod.yml stop backend scheduler

# Restore the backup
gunzip -c /opt/hewasense/backups/hewasense_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i climate_db_prod psql -U user -d climate_dev

# Restart services
docker compose -f docker-compose.prod.yml start backend scheduler
```

---

## 4. Shadow Run Data Protection

### 4.1 Shadow Run Timeline
- The shadow run requires 90 valid run-days of continuous pipeline operation.
- Each day of lost data extends the completion date by one day.
- Shadow run data is irreplaceable once lost — it represents real-time forecast accuracy tracking.

### 4.2 Critical Tables
These tables contain live pipeline data that cannot be regenerated from files:

| Table | Content | Regenerable? |
|-------|---------|-------------|
| `forecast_logs` | Daily shadow run forecasts | NO - represents real-time predictions |
| `pipeline_executions` | Pipeline run history | NO - historical record |
| `source_ingestion_tracking` | Last ingestion dates per source | Partially - resets to 180-day lookback |
| `forecasts` | Active forecasts | NO - time-sensitive predictions |
| `forecast_validation` | Forecast accuracy tracking | NO - requires matched predictions + outcomes |

### 4.3 Reloadable Tables
These tables can be repopulated from existing files:

| Table | Source File | Command |
|-------|-----------|---------|
| `climate_data` | `/outputs/processed/master_dataset.csv` | `python scripts/load_climate_data.py --csv /outputs/processed/master_dataset.csv` |
| `model_metrics` | `/outputs/models/latest_training_results.json` | `python scripts/load_model_metrics.py --results /outputs/models/latest_training_results.json` |
| `locations` | Seed script | `python scripts/seed_locations.py` |
| `users` | Seed script | `python scripts/seed_users.py` |

---

## 5. Incident Log

### 2026-04-24: Database Destruction During Frontend Deployment
- **Cause:** Ran `docker compose -f docker-compose.prod.yml down --remove-orphans` which removed the dev DB container and its volume containing 9 days of shadow run data.
- **Data Lost:** All `forecast_logs`, `pipeline_executions`, `forecasts`, `source_ingestion_tracking`, and `climate_data` records from 9 days of live pipeline operation.
- **Impact:** Shadow run reset to day 0 of 90. Projected completion extended by 9 days.
- **Resolution:** Reloaded `climate_data` and `model_metrics` from files. Locations and users re-seeded. Pipeline will resume at next 6AM EAT run.
- **Prevention:** This policy document. Automated daily backups. Strict deployment rules.
