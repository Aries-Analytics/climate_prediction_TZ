"""
Auto-Log Service — Stage 6 of the pipeline orchestrator.

Runs after every successful pipeline execution (completed or partial).
Creates the daily memory log file, updates repo MEMORY.md and 5 business
docs with current shadow run counters, then git commits and pushes.

Non-blocking: any failure here is logged as a warning and does NOT affect
pipeline status or the Slack alert.

Phase-aware:
- While valid_run_days < 90: updates all 5 business docs (counter lines only)
- After valid_run_days >= 90: writes daily log + MEMORY.md only; business
  docs get milestone updates instead of daily counter churn
"""

import logging
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Inside the scheduler container:
#   /app/repo_root  → phase2/ directory (memory/, docs/, all project files)
# The .git directory lives one level up (the outer repo root), so git
# commands use --git-dir and --work-tree to specify both explicitly.
PHASE2_DIR   = Path("/app/repo_root")   # phase2/ (files to read/write)
GIT_DIR      = Path("/app/repo_git")    # ../.git mounted directly (outer repo root)
REPO_ROOT    = PHASE2_DIR               # alias for file path construction

# Convenience re-exports used throughout
MEMORY_MD       = PHASE2_DIR / "memory" / "MEMORY.md"
LOGS_DIR        = PHASE2_DIR / "memory" / "logs"
PARAMETRIC_DOC  = PHASE2_DIR / "docs" / "references" / "PARAMETRIC_INSURANCE_FINAL.md"
EXTERNAL_BRIEF  = PHASE2_DIR / "docs" / "references" / "HEWASENSE_EXTERNAL_BRIEF.md"
EXECUTIVE_SUM   = PHASE2_DIR / "docs" / "current" / "EXECUTIVE_SUMMARY.md"
PIPELINE_STATUS = PHASE2_DIR / "docs" / "current" / "PIPELINE_STATUS_MARCH2026.md"
BUSINESS_CASE   = PHASE2_DIR / "docs" / "references" / "BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md"

SHADOW_RUN_TARGET_DAYS = 90
SHADOW_RUN_TARGET_FORECASTS = 1080


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_auto_log(
    db,
    execution_id: str,
    run_date: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    sources_failed: Optional[list] = None,
) -> None:
    """
    Main entry point. Called from Stage 6 of orchestrator.execute_pipeline().

    Args:
        db: SQLAlchemy session (read-only queries)
        execution_id: UUID of the just-completed pipeline execution
        run_date: UTC datetime of the run (defaults to now)
        duration_seconds: Pipeline duration in seconds
        sources_failed: List of failed source names ([] = all clean)
    """
    try:
        run_date = run_date or datetime.now(timezone.utc)
        sources_failed = sources_failed or []

        metrics = _query_metrics(db)
        if metrics is None:
            logger.warning("Auto-log: could not query metrics, skipping")
            return

        total_forecasts = metrics["total_forecasts"]
        valid_run_days  = metrics["valid_run_days"]
        run_day_dates   = metrics["run_day_dates"]

        pct = (total_forecasts / SHADOW_RUN_TARGET_FORECASTS) * 100

        # Write daily log file
        _write_daily_log(
            run_date=run_date,
            execution_id=execution_id,
            duration_seconds=duration_seconds,
            total_forecasts=total_forecasts,
            valid_run_days=valid_run_days,
            run_day_dates=run_day_dates,
            pct=pct,
            sources_failed=sources_failed,
        )

        # Update repo MEMORY.md
        _update_memory_md(
            run_date=run_date,
            total_forecasts=total_forecasts,
            valid_run_days=valid_run_days,
            run_day_dates=run_day_dates,
            pct=pct,
        )

        # Update 5 business docs (only while shadow run is active)
        if valid_run_days < SHADOW_RUN_TARGET_DAYS:
            _update_business_docs(
                run_date=run_date,
                total_forecasts=total_forecasts,
                valid_run_days=valid_run_days,
                run_day_dates=run_day_dates,
                pct=pct,
            )

        # Commit and push
        _git_commit_and_push(run_date, total_forecasts, pct, valid_run_days)

        logger.info(
            f"Auto-log complete: {total_forecasts}/1080 ({pct:.1f}%), "
            f"Day {valid_run_days}"
        )

    except Exception as e:
        logger.warning(f"Auto-log Stage 6 failed (non-blocking): {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Metrics query
# ---------------------------------------------------------------------------

def _query_metrics(db) -> Optional[dict]:
    """Query DB for current shadow run counters."""
    try:
        from sqlalchemy import func, text
        from app.models.forecast_log import ForecastLog

        total = db.query(func.count(ForecastLog.id)).scalar() or 0
        valid_days = db.query(
            func.count(func.distinct(func.date(ForecastLog.issued_at)))
        ).scalar() or 0

        # All distinct run-day dates sorted
        rows = db.execute(
            text(
                "SELECT DISTINCT DATE(issued_at) AS d "
                "FROM forecast_logs ORDER BY d"
            )
        ).fetchall()
        run_day_dates = [str(r[0]) for r in rows]

        return {
            "total_forecasts": total,
            "valid_run_days":  valid_days,
            "run_day_dates":   run_day_dates,
        }
    except Exception as e:
        logger.error(f"Auto-log: metrics query failed: {e}", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Daily log file
# ---------------------------------------------------------------------------

def _write_daily_log(
    run_date, execution_id, duration_seconds,
    total_forecasts, valid_run_days, run_day_dates, pct,
    sources_failed,
) -> None:
    """Create memory/logs/YYYY-MM-DD.md for this run."""
    # Use EAT date (UTC+3) for filename and header
    eat_date = (run_date + timedelta(hours=3)).date()
    log_path = LOGS_DIR / f"{eat_date}.md"

    if log_path.exists():
        logger.info(f"Auto-log: daily log already exists for {eat_date}, skipping create")
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    streak_note = _streak_note(run_day_dates, valid_run_days)
    remaining   = SHADOW_RUN_TARGET_DAYS - valid_run_days
    # Days until Jun 12 2026
    target_end  = datetime(2026, 6, 12, tzinfo=timezone.utc)
    cal_days    = max(0, (target_end - run_date).days)
    track_str   = "on track" if cal_days >= remaining else "at risk"

    weekday = eat_date.strftime("%A")
    month_day = eat_date.strftime("%B %d")
    next_run = eat_date + timedelta(days=1)

    ingestion_line = ""
    if sources_failed:
        ingestion_line = (
            f"\n**Ingestion:** Sources failed: {', '.join(sources_failed)}. "
            "Check pipeline logs.\n"
        )

    duration_str = f"{duration_seconds}s" if duration_seconds else "N/A"

    run_day_list = _run_day_list_str(run_day_dates)

    content = f"""# Daily Log: {eat_date}

> Session log for {weekday}, {month_day}, {eat_date.year}

---

## Pipeline Run — {month_day}

**Status:** SUCCESS | Duration: {duration_str} | Trigger: Scheduled (06:00 EAT)
**Forecasts:** 12 generated | Location: Morogoro | Data Quality: 100%
**Shadow Run:** {total_forecasts} / {SHADOW_RUN_TARGET_FORECASTS} ({pct:.1f}%) — {valid_run_days} valid run-days
**Execution ID:** {execution_id}
{ingestion_line}
---

## Shadow Run Status

| Metric | Value |
|---|---|
| `forecast_logs` | {total_forecasts} |
| Valid run-days | {valid_run_days} ({run_day_list}) |
| Target | {SHADOW_RUN_TARGET_FORECASTS} |
| Progress | {pct:.1f}% |
| Next scheduled run | {next_run} 06:00 EAT |

**Note:** {valid_run_days} total valid run-days. {streak_note} {remaining} valid run-days remaining; revised end date Jun 12 provides {cal_days} calendar days — {track_str}.
"""
    log_path.write_text(content, encoding="utf-8")
    logger.info(f"Auto-log: wrote {log_path}")


def _run_day_list_str(run_day_dates: list) -> str:
    """Format run day dates as a compact string e.g. 'Mar 11, Mar 15 – Apr 2'"""
    if not run_day_dates:
        return "none"
    if len(run_day_dates) == 1:
        return _fmt_date(run_day_dates[0])

    # Find consecutive streaks
    from datetime import date as date_type
    parsed = [datetime.strptime(d, "%Y-%m-%d").date() for d in run_day_dates]
    streaks = []
    start = parsed[0]
    prev  = parsed[0]
    for d in parsed[1:]:
        if (d - prev).days == 1:
            prev = d
        else:
            streaks.append((start, prev))
            start = d
            prev  = d
    streaks.append((start, prev))

    parts = []
    for s, e in streaks:
        if s == e:
            parts.append(_fmt_date(str(s)))
        else:
            parts.append(f"{_fmt_date(str(s))} – {_fmt_date(str(e))}")
    return ", ".join(parts)


def _fmt_date(d: str) -> str:
    """'2026-03-11' → 'Mar 11'"""
    return datetime.strptime(d, "%Y-%m-%d").strftime("%b %-d") if os.name != "nt" \
        else datetime.strptime(d, "%Y-%m-%d").strftime("%b %d").lstrip("0")


def _streak_note(run_day_dates: list, valid_run_days: int) -> str:
    """Generate streak description for the Note line."""
    if not run_day_dates:
        return ""
    from datetime import date as date_type
    parsed = [datetime.strptime(d, "%Y-%m-%d").date() for d in run_day_dates]
    # Count trailing consecutive streak
    streak = 1
    for i in range(len(parsed) - 1, 0, -1):
        if (parsed[i] - parsed[i-1]).days == 1:
            streak += 1
        else:
            break
    isolated = valid_run_days - streak
    streak_start = parsed[-(streak)]
    streak_end   = parsed[-1]
    streak_str   = f"{streak} consecutive ({_fmt_date(str(streak_start))}–{_fmt_date(str(streak_end))})"
    if isolated > 0:
        return f"Current streak: {streak_str} + {isolated} isolated earlier."
    return f"Current streak: {streak_str}."


# ---------------------------------------------------------------------------
# memory/MEMORY.md update
# ---------------------------------------------------------------------------

def _update_memory_md(
    run_date, total_forecasts, valid_run_days, run_day_dates, pct
) -> None:
    """Update pipeline status counter and Logs Index in memory/MEMORY.md."""
    if not MEMORY_MD.exists():
        logger.warning(f"Auto-log: {MEMORY_MD} not found, skipping")
        return

    eat_date = (run_date + timedelta(hours=3)).date()
    text_content = MEMORY_MD.read_text(encoding="utf-8")

    run_day_list = _run_day_list_str(run_day_dates)
    streak_note  = _streak_note(run_day_dates, valid_run_days)
    # Build streak phrase for Key Facts (compact)
    streak_compact = streak_note.replace("Current streak: ", "").rstrip(".")

    # 1. Update Key Facts pipeline status line
    text_content = re.sub(
        r'\*\*Pipeline status \([^)]+\):\*\*.*?(?=\n-|\n\n)',
        (
            f"**Pipeline status ({eat_date.strftime('%B %Y')}):** "
            f"Shadow run ACTIVE Mar 7 – Jun 12, 2026 (revised — 7 missed days). "
            f"12 forecasts/run (3 triggers × 4 horizons × Morogoro). "
            f"**{total_forecasts}/{SHADOW_RUN_TARGET_FORECASTS} forecasts ({pct:.1f}%), "
            f"{valid_run_days} valid run-days ({run_day_list}). "
            f"Current streak: {streak_compact}.** "
            f"Evidence Pack accumulates; Brier Score auto-evaluation starts ~Jun 9. "
            f"Completion auto-detected at day 90 — final report + Slack alert fire automatically."
        ),
        text_content,
        flags=re.DOTALL,
    )

    # 2. Append or update Logs Index row for today
    date_str = str(eat_date)
    log_line = (
        f"| {date_str} | Pipeline SUCCESS — "
        f"{total_forecasts}/{SHADOW_RUN_TARGET_FORECASTS} ({pct:.1f}%), "
        f"Day {valid_run_days} |"
    )
    if date_str in text_content:
        # Row already exists (e.g. from manual /log-run earlier) — skip to avoid duplicate
        logger.info(f"Auto-log: MEMORY.md already has entry for {date_str}, skipping row insert")
    else:
        # Insert before the closing "Last updated" line
        text_content = re.sub(
            r'(\*Last updated:.*)',
            f"{log_line}\n\n\\1",
            text_content,
        )

    # 3. Update Last updated date
    text_content = re.sub(
        r'\*Last updated:.*',
        f"*Last updated: {date_str}*",
        text_content,
    )

    MEMORY_MD.write_text(text_content, encoding="utf-8")
    logger.info(f"Auto-log: updated {MEMORY_MD}")


# ---------------------------------------------------------------------------
# Business docs — 5 files
# ---------------------------------------------------------------------------

def _update_business_docs(
    run_date, total_forecasts, valid_run_days, run_day_dates, pct
) -> None:
    """Update shadow run counters in the 5 business/reference docs."""
    eat_date = (run_date + timedelta(hours=3)).date()
    day_str  = str(eat_date)
    month_day_yr = eat_date.strftime("%B %d, %Y").replace(" 0", " ")  # "April 2, 2026"

    # Em-dash U+2014 and en-dash U+2013 must use unicode escapes in regex
    # strings to avoid encoding mismatches between source file and target docs.
    EM  = u'\u2014'   # —
    EN  = u'\u2013'   # –
    ROT = u'\U0001f504'  # 🔄

    # 1. PARAMETRIC_INSURANCE_FINAL.md
    _replace_in_file(
        PARAMETRIC_DOC,
        u'### Phase 2 \u2014 Shadow Run \U0001f504 ACTIVE \u2014 Day \\d+ of 90 valid run-days \\(\\d+/1,080 forecasts, \\d+\\.\\d+%\\)',
        f'### Phase 2 {EM} Shadow Run {ROT} ACTIVE {EM} Day {valid_run_days} of 90 valid run-days ({total_forecasts}/1,080 forecasts, {pct:.1f}%)',
    )

    # 2. HEWASENSE_EXTERNAL_BRIEF.md  — "Forecasts accumulated" table row
    # Pattern captures the full row (value cell + trailing cell) to prevent duplication
    _replace_in_file(
        EXTERNAL_BRIEF,
        r'\| Forecasts accumulated\s+\|[^\n]+\n',
        f'| Forecasts accumulated       | {total_forecasts} ({valid_run_days} valid run-days, {month_day_yr})         | Live system — updated as shadow run progresses    |\n',
    )

    # 3. EXECUTIVE_SUMMARY.md — line 5 header + Next Steps section (2 places)
    _replace_in_file(
        EXECUTIVE_SUM,
        u'Shadow Run ACTIVE \\(Mar 7 \u2013 Jun 12, 2026 revised \u2014 Day \\d+ of 90 \u00b7 \\d+/1,080 forecasts \u00b7 \\d+\\.\\d+%\\)',
        f'Shadow Run ACTIVE (Mar 7 {EN} Jun 12, 2026 revised {EM} Day {valid_run_days} of 90 \u00b7 {total_forecasts}/1,080 forecasts \u00b7 {pct:.1f}%)',
        replace_all=True,
    )
    _replace_in_file(
        EXECUTIVE_SUM,
        r'Day \d+ of 90 \(\d+/1,080 forecasts, \d+\.\d+%\)\.',
        f'Day {valid_run_days} of 90 ({total_forecasts}/1,080 forecasts, {pct:.1f}%).',
        replace_all=True,
    )

    # 4. PIPELINE_STATUS_MARCH2026.md — table rows + Last Updated
    run_day_list = _run_day_list_str(run_day_dates)
    _replace_in_file(
        PIPELINE_STATUS,
        r'\| `forecast_logs` rows\s+\|[^\|]+\|',
        f'| `forecast_logs` rows | {total_forecasts} ({valid_run_days} valid run-days: {run_day_list}) |',
    )
    _replace_in_file(
        PIPELINE_STATUS,
        r'\| Valid run-days achieved\s+\|[^\|]+\|',
        f'| Valid run-days achieved | {valid_run_days} of 90 target ({pct:.1f}%) |',
    )
    _replace_in_file(
        PIPELINE_STATUS,
        r'\*\*Last Updated\*\*:.*',
        f'**Last Updated**: {month_day_yr}',
    )

    # 5. BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md — header status line
    _replace_in_file(
        BUSINESS_CASE,
        u'\\*\\*Status\\*\\*: Shadow Run ACTIVE \u2014 Day \\d+ of 90 valid run-days \\(\\d+/1,080 forecasts, \\d+\\.\\d+%\\)',
        f'**Status**: Shadow Run ACTIVE {EM} Day {valid_run_days} of 90 valid run-days ({total_forecasts}/1,080 forecasts, {pct:.1f}%)',
    )

    logger.info("Auto-log: updated 5 business docs")


def _replace_in_file(path: Path, pattern: str, replacement: str, replace_all: bool = False) -> None:
    """Replace first (or all) regex match in a file."""
    if not path.exists():
        logger.warning(f"Auto-log: {path} not found, skipping")
        return
    content = path.read_text(encoding="utf-8")
    if replace_all:
        new_content = re.sub(pattern, replacement, content)
    else:
        new_content = re.sub(pattern, replacement, content, count=1)
    if new_content == content:
        logger.warning(f"Auto-log: pattern not matched in {path.name}: {pattern[:60]}")
    else:
        path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Git commit and push
# ---------------------------------------------------------------------------

def _git_commit_and_push(run_date, total_forecasts, pct, valid_run_days) -> None:
    """Stage changed files, commit, and push to origin.

    The .git directory is one level above phase2/ on the host, so we pass
    --git-dir and --work-tree explicitly rather than relying on cwd discovery.
    All paths passed to git add are relative to PHASE2_DIR (the work-tree).
    """
    eat_date = (run_date + timedelta(hours=3)).date()

    # Paths relative to PHASE2_DIR (the git work-tree)
    files_to_stage = [
        "phase2/memory/logs/",
        "phase2/memory/MEMORY.md",
        "phase2/docs/references/PARAMETRIC_INSURANCE_FINAL.md",
        "phase2/docs/references/HEWASENSE_EXTERNAL_BRIEF.md",
        "phase2/docs/current/EXECUTIVE_SUMMARY.md",
        "phase2/docs/current/PIPELINE_STATUS_MARCH2026.md",
        "phase2/docs/references/BUSINESS_CASE_AND_DEPLOYMENT_RATIONALE.md",
    ]

    commit_msg = (
        f"docs(log): pipeline run {eat_date} — "
        f"{total_forecasts}/1080 forecasts ({pct:.1f}%), Day {valid_run_days}\n\n"
        f"Auto-generated by Stage 6 auto_log_service.py"
    )

    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "HewaSense Pipeline",
        "GIT_AUTHOR_EMAIL": "pipeline@hewasense.majaribio.com",
        "GIT_COMMITTER_NAME": "HewaSense Pipeline",
        "GIT_COMMITTER_EMAIL": "pipeline@hewasense.majaribio.com",
        # Tell git where .git is and what the work-tree root is
        "GIT_DIR": str(GIT_DIR),                  # /app/repo_git (mounted ../.git)
        "GIT_WORK_TREE": "/app/repo_root_parent", # outer repo root (mounted ../)
    }

    try:
        # Stage files
        subprocess.run(
            ["git", "add"] + files_to_stage,
            check=True, capture_output=True, text=True, env=git_env,
        )

        # Check if there's anything to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True, env=git_env,
        )
        if result.returncode == 0:
            logger.info("Auto-log: nothing to commit (no changes staged)")
            return

        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True, capture_output=True, text=True, env=git_env,
        )

        # Push — use the remote URL already configured with PAT
        subprocess.run(
            ["git", "push", "origin", "phase2/feature-expansion"],
            check=True, capture_output=True, text=True, env=git_env,
        )

        logger.info(f"Auto-log: committed and pushed for {eat_date}")

    except subprocess.CalledProcessError as e:
        logger.warning(
            f"Auto-log: git operation failed (non-blocking): "
            f"{e.cmd} → stderr: {e.stderr.strip()}"
        )
