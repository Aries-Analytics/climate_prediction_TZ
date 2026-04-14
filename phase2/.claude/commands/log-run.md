# /log-run — Log Daily Pipeline Run (GOTCHA Protocol)

Run this after every successful pipeline Slack alert. Updates ALL documentation in the correct order.

## Step 1 — Query the server

SSH to `root@37.27.200.227` and run these three queries:

**Latest pipeline execution:**
```sql
docker compose -f /opt/hewasense/app/phase2/docker-compose.dev.yml exec -T db \
  psql -U hewasense -d hewasense_db -c \
  "SELECT id, execution_id, status, duration_seconds, forecasts_generated,
          location_id, data_quality_score, sources_succeeded, sources_failed,
          records_stored, created_at
   FROM pipeline_executions ORDER BY created_at DESC LIMIT 1;"
```

**Shadow run total and valid run-days:**
```sql
docker compose -f /opt/hewasense/app/phase2/docker-compose.dev.yml exec -T db \
  psql -U hewasense -d hewasense_db -c \
  "SELECT COUNT(*) AS total_forecasts,
          COUNT(DISTINCT DATE(created_at)) AS valid_run_days
   FROM forecast_logs;"
```

**Individual run-day dates (for streak calculation):**
```sql
docker compose -f /opt/hewasense/app/phase2/docker-compose.dev.yml exec -T db \
  psql -U hewasense -d hewasense_db -c \
  "SELECT DISTINCT DATE(created_at) AS run_date
   FROM forecast_logs ORDER BY run_date;"
```

## Step 2 — Calculate shadow run metrics

From the query results:
- `total_forecasts` / 2,160 × 100 = progress %
- List all valid run-days and identify: current consecutive streak + any isolated earlier days
- Valid run-days remaining = 90 − valid_run_days_so_far
- Calendar days remaining = days until Jul 13, 2026

## Step 3 — Apply GOTCHA ingestion rules

**CRITICAL — read before writing anything:**
- `sources_failed = []` means no fetch errors. It does NOT mean all sources returned data.
- CHIRPS, NASA POWER, and NDVI routinely return 0 records — this is normal incremental ingestion (sources are current, no new data since last pull). Do NOT flag as noteworthy.
- ERA5 and Ocean Indices are the active daily updaters (~3 records/run combined).
- Only mention ingestion if `sources_failed` is non-empty (actual fetch error).

## Step 4 — Create daily log file

Create `memory/logs/YYYY-MM-DD.md` (use the run date, not today's date if different):

```markdown
# Daily Log: YYYY-MM-DD

> Session log for [Weekday], [Month] [Day], [Year]

---

## Pipeline Run — [Month Day]

**Status:** [SUCCESS/FAILURE] | Duration: [N]s | Trigger: Scheduled (06:00 EAT)
**Forecasts:** 24 generated | Zones: Ifakara TC + Mlimba DC | Data Quality: 100%
**Shadow Run:** [total] / 2,160 ([pct]%) — [N] valid run-days
**Execution ID:** [execution_id]

[Ingestion line ONLY if sources_failed is non-empty]

---

## Shadow Run Status

| Metric | Value |
|---|---|
| `forecast_logs` | [total] |
| Valid run-days | [N] ([list of dates]) |
| Target | 2,160 |
| Progress | [pct]% |
| Next scheduled run | [tomorrow] 06:00 EAT |

**Note:** [N] total valid run-days. Current streak: [streak description]. [remaining] valid run-days remaining; revised end date Jul 13 provides [calendar_days] calendar days — [on track / tight / at risk assessment].
```

## Step 5 — Update docs/references/PARAMETRIC_INSURANCE_FINAL.md

Find the Phase 2 shadow run progress line (contains "Day X of 90 valid run-days") and update:
- Day count, forecast count, percentage

## Step 6 — Update docs/references/HEWASENSE_EXTERNAL_BRIEF.md

Find the "Forecasts accumulated" row in the shadow run table and update with new count, run-days, and date.

## Step 7 — Update docs/current/EXECUTIVE_SUMMARY.md

Two locations — both must be updated:
1. **Line 5 header status**: `Shadow Run ACTIVE (Mar 7 – Jul 13, 2026 revised — Day X of 90 · XXX/2,160 forecasts · XX.X%)`
2. **Next Steps section**: `Shadow run live Mar 7 – Jul 13, 2026 (revised). Day X of 90 (XXX/2,160 forecasts, XX.X%).`

## Step 8 — Update docs/current/PIPELINE_STATUS_MARCH2026.md

In the "Current State" table, update two rows:
1. `forecast_logs rows` — new count + list of valid run-days
2. `Valid run-days achieved` — new count of 90 target + percentage

Also update the `Last Updated` date in the file header (line 6).

## Step 9 — Update docs/references/BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md

Update the header status line (line 7):
`**Status**: Shadow Run ACTIVE — Day X of 90 valid run-days (XXX/2,160 forecasts, XX.X%)`

## Step 10 — Update memory/MEMORY.md

Three locations:
1. **Pipeline status line** (near top, "Pipeline status (April 2026)"): update forecast count, percentage, valid run-days list, current streak
2. **Session log table** (near bottom): add new row for this date
3. **Last updated** date at the bottom of the file

## Step 11 — Commit and push

Stage all changed files and commit:
```
docs(log): pipeline run YYYY-MM-DD — [total]/2,160 forecasts ([pct]%), Day [N]
```

Then push to remote immediately.

## Full checklist before committing

- [ ] Daily log file created with correct run date
- [ ] Ingestion section absent (or accurate) — no false "all sources clean" claims
- [ ] Streak calculation is correct (count consecutive days from the date list)
- [ ] `PARAMETRIC_INSURANCE_FINAL.md` updated
- [ ] `HEWASENSE_EXTERNAL_BRIEF.md` updated
- [ ] `EXECUTIVE_SUMMARY.md` updated (both instances)
- [ ] `PIPELINE_STATUS_MARCH2026.md` updated (table + Last Updated date)
- [ ] `BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md` updated
- [ ] `memory/MEMORY.md` updated (pipeline status + log index + last updated)
- [ ] Committed and pushed to remote
