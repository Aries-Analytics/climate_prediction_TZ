"""
Data Refresh Scheduler - Phase 2
Provides automated scheduling for periodic data refreshes.
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path

import schedule
from utils.config import get_data_path
from utils.logger import log_error, log_info


class DataRefreshScheduler:
    """
    Manages automated data refresh scheduling for climate data sources.
    """

    def __init__(self, config_path=None):
        """
        Initialize the scheduler.

        Args:
            config_path: Path to scheduler configuration file (default: data/scheduler_config.json)
        """
        if config_path is None:
            config_path = get_data_path("scheduler_config.json")
        self.config_path = Path(config_path)
        self.jobs = {}
        self.running = False
        self.thread = None
        self.load_config()

    def load_config(self):
        """Load scheduler configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    log_info(f"Loaded scheduler configuration from {self.config_path}")
                    return config
            except Exception as e:
                log_error(f"Failed to load scheduler config: {e}")
        return {}

    def save_config(self, config):
        """Save scheduler configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            log_info(f"Saved scheduler configuration to {self.config_path}")
        except Exception as e:
            log_error(f"Failed to save scheduler config: {e}")

    def schedule_job(self, job_name, func, schedule_type="daily", schedule_time="00:00", **kwargs):
        """
        Schedule a data refresh job.

        Args:
            job_name: Unique name for the job
            func: Function to execute
            schedule_type: Type of schedule ('daily', 'weekly', 'hourly', 'interval')
            schedule_time: Time to run (for daily/weekly) or interval (for interval type)
            **kwargs: Additional arguments to pass to the function

        Examples:
            - Daily at 2 AM: schedule_type='daily', schedule_time='02:00'
            - Every 6 hours: schedule_type='interval', schedule_time='6'
            - Weekly on Monday: schedule_type='weekly', schedule_time='monday'
        """
        try:
            if schedule_type == "daily":
                job = schedule.every().day.at(schedule_time).do(func, **kwargs)
            elif schedule_type == "weekly":
                # schedule_time should be day name like 'monday'
                day_func = getattr(schedule.every(), schedule_time.lower())
                job = day_func.do(func, **kwargs)
            elif schedule_type == "hourly":
                job = schedule.every().hour.do(func, **kwargs)
            elif schedule_type == "interval":
                # schedule_time should be number of hours
                hours = int(schedule_time)
                job = schedule.every(hours).hours.do(func, **kwargs)
            else:
                log_error(f"Unknown schedule type: {schedule_type}")
                return False

            self.jobs[job_name] = {
                "job": job,
                "func": func.__name__,
                "schedule_type": schedule_type,
                "schedule_time": schedule_time,
                "created_at": datetime.now().isoformat(),
            }

            log_info(f"Scheduled job '{job_name}': {schedule_type} at {schedule_time}")
            return True

        except Exception as e:
            log_error(f"Failed to schedule job '{job_name}': {e}")
            return False

    def cancel_job(self, job_name):
        """
        Cancel a scheduled job.

        Args:
            job_name: Name of the job to cancel
        """
        if job_name in self.jobs:
            schedule.cancel_job(self.jobs[job_name]["job"])
            del self.jobs[job_name]
            log_info(f"Cancelled job: {job_name}")
            return True
        else:
            log_error(f"Job not found: {job_name}")
            return False

    def list_jobs(self):
        """
        List all scheduled jobs.

        Returns:
            Dictionary of job information
        """
        job_info = {}
        for name, info in self.jobs.items():
            job_info[name] = {
                "function": info["func"],
                "schedule_type": info["schedule_type"],
                "schedule_time": info["schedule_time"],
                "created_at": info["created_at"],
                "next_run": str(info["job"].next_run) if info["job"].next_run else "Not scheduled",
            }
        return job_info

    def start(self, run_pending_immediately=False):
        """
        Start the scheduler in a background thread.

        Args:
            run_pending_immediately: If True, run any pending jobs immediately on start
        """
        if self.running:
            log_info("Scheduler is already running")
            return

        self.running = True

        if run_pending_immediately:
            schedule.run_all()

        def run_scheduler():
            log_info("Scheduler started")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            log_info("Scheduler stopped")

        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        log_info("Scheduler thread started")

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
            log_info("Scheduler stopped")
        else:
            log_info("Scheduler is not running")

    def run_once(self):
        """Run all pending jobs once (useful for testing)."""
        schedule.run_all()
        log_info("Executed all scheduled jobs once")

    def clear_all_jobs(self):
        """Clear all scheduled jobs."""
        schedule.clear()
        self.jobs = {}
        log_info("Cleared all scheduled jobs")


def create_data_refresh_job(source_name, fetch_function, **fetch_kwargs):
    """
    Create a data refresh job function.

    Args:
        source_name: Name of the data source
        fetch_function: Function to fetch data
        **fetch_kwargs: Arguments to pass to fetch function

    Returns:
        Job function
    """

    def job():
        try:
            log_info(f"Starting scheduled refresh for {source_name}")
            start_time = datetime.now()

            # Execute the fetch function
            result = fetch_function(**fetch_kwargs)

            duration = (datetime.now() - start_time).total_seconds()
            log_info(f"Completed refresh for {source_name} in {duration:.2f} seconds")

            return result

        except Exception as e:
            log_error(f"Failed to refresh {source_name}: {e}")
            return None

    job.__name__ = f"refresh_{source_name}"
    return job


# Global scheduler instance
_scheduler = None


def get_scheduler(config_path=None):
    """
    Get or create the global scheduler instance.

    Args:
        config_path: Path to scheduler configuration file

    Returns:
        DataRefreshScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = DataRefreshScheduler(config_path=config_path)
    return _scheduler
