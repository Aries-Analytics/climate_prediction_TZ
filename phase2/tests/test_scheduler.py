"""
Tests for data refresh scheduler
"""

import tempfile

from utils.scheduler import DataRefreshScheduler, create_data_refresh_job


def test_schedule_daily_job():
    """Test scheduling a daily job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scheduler = DataRefreshScheduler(config_path=f"{tmpdir}/config.json")

        def dummy_task():
            return "executed"

        success = scheduler.schedule_job("test_job", dummy_task, schedule_type="daily", schedule_time="10:00")

        assert success is True
        assert "test_job" in scheduler.jobs


def test_schedule_interval_job():
    """Test scheduling an interval-based job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scheduler = DataRefreshScheduler(config_path=f"{tmpdir}/config.json")

        def dummy_task():
            return "executed"

        success = scheduler.schedule_job("test_job", dummy_task, schedule_type="interval", schedule_time="6")

        assert success is True
        assert "test_job" in scheduler.jobs


def test_cancel_job():
    """Test cancelling a scheduled job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scheduler = DataRefreshScheduler(config_path=f"{tmpdir}/config.json")

        def dummy_task():
            return "executed"

        scheduler.schedule_job("test_job", dummy_task, schedule_type="daily", schedule_time="10:00")
        assert "test_job" in scheduler.jobs

        success = scheduler.cancel_job("test_job")
        assert success is True
        assert "test_job" not in scheduler.jobs


def test_list_jobs():
    """Test listing scheduled jobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scheduler = DataRefreshScheduler(config_path=f"{tmpdir}/config.json")

        def dummy_task():
            return "executed"

        scheduler.schedule_job("job1", dummy_task, schedule_type="daily", schedule_time="10:00")
        scheduler.schedule_job("job2", dummy_task, schedule_type="hourly")

        jobs = scheduler.list_jobs()
        assert len(jobs) == 2
        assert "job1" in jobs
        assert "job2" in jobs


def test_create_data_refresh_job():
    """Test creating a data refresh job."""

    def mock_fetch(source):
        return f"fetched {source}"

    job = create_data_refresh_job("test_source", mock_fetch, source="test_data")

    result = job()
    assert result == "fetched test_data"


def test_run_once():
    """Test running all jobs once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scheduler = DataRefreshScheduler(config_path=f"{tmpdir}/config.json")

        executed = []

        def dummy_task(name):
            executed.append(name)

        scheduler.schedule_job("job1", dummy_task, schedule_type="daily", schedule_time="10:00", name="task1")
        scheduler.run_once()

        assert "task1" in executed
