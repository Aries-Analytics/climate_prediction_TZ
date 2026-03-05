"""
Pipeline CLI Commands

Command-line interface for manual pipeline operations.

**Validates: Requirements 7.1, 7.3, 6.5**
"""
import click
import asyncio
from datetime import datetime, timedelta, timezone
from tabulate import tabulate
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.pipeline.scheduler import PipelineScheduler
from app.services.pipeline.orchestrator import PipelineOrchestrator
from app.services.pipeline.monitoring import MonitoringService
from app.services.pipeline.alerts import AlertService
from app.models.pipeline_execution import PipelineExecution


@click.group()
def pipeline():
    """Pipeline management commands"""
    pass


@pipeline.command()
@click.option('--incremental/--full', default=True, help='Incremental or full data fetch')
@click.option('--sources', default=None, help='Comma-separated list of sources (default: all)')
def run(incremental: bool, sources: str):
    """
    Run pipeline execution manually
    
    **Validates: Requirements 7.1**
    
    Examples:
        pipeline run                          # Run with incremental fetch
        pipeline run --full                   # Run with full data fetch
        pipeline run --sources chirps,era5    # Run specific sources only
    """
    click.echo("=" * 60)
    click.echo("Manual Pipeline Execution")
    click.echo("=" * 60)
    click.echo(f"Mode: {'Incremental' if incremental else 'Full'}")
    if sources:
        click.echo(f"Sources: {sources}")
    click.echo()
    
    db = SessionLocal()
    try:
        scheduler = PipelineScheduler(db)
        
        click.echo("Starting pipeline execution...")
        start_time = datetime.now(timezone.utc)
        
        # Trigger manual run
        result = scheduler.trigger_manual_run(incremental=incremental)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        click.echo()
        click.echo("=" * 60)
        click.echo("Execution Results")
        click.echo("=" * 60)
        
        status_color = 'green' if result.status == 'completed' else 'yellow' if result.status == 'partial' else 'red'
        click.echo(f"Status: {click.style(result.status.upper(), fg=status_color)}")
        click.echo(f"Execution ID: {result.execution_id}")
        click.echo(f"Duration: {duration:.2f} seconds")
        click.echo()
        
        click.echo("Ingestion:")
        click.echo(f"  Records Fetched: {result.records_fetched}")
        click.echo(f"  Records Stored: {result.records_stored}")
        click.echo(f"  Sources Succeeded: {', '.join(result.sources_succeeded) if result.sources_succeeded else 'None'}")
        if result.sources_failed:
            click.echo(f"  Sources Failed: {click.style(', '.join(result.sources_failed), fg='red')}")
        click.echo()
        
        click.echo("Forecasting:")
        click.echo(f"  Forecasts Generated: {result.forecasts_generated}")
        click.echo(f"  Recommendations Created: {result.recommendations_created}")
        
        if result.error_message:
            click.echo()
            click.echo(click.style("Error:", fg='red'))
            click.echo(f"  {result.error_message}")
        
        click.echo()
        if result.status == 'completed':
            click.echo(click.style("✓ Pipeline execution completed successfully!", fg='green'))
        elif result.status == 'partial':
            click.echo(click.style("⚠ Pipeline execution completed with some failures", fg='yellow'))
        else:
            click.echo(click.style("✗ Pipeline execution failed", fg='red'))
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
        raise
    finally:
        db.close()


@pipeline.command()
@click.option('--execution-id', default=None, help='Show specific execution by ID')
@click.option('--verbose', is_flag=True, help='Show detailed information')
def status(execution_id: str, verbose: bool):
    """
    View current pipeline status
    
    **Validates: Requirements 7.3**
    
    Examples:
        pipeline status                       # Show current status
        pipeline status --verbose             # Show detailed status
        pipeline status --execution-id abc123 # Show specific execution
    """
    db = SessionLocal()
    try:
        monitoring = MonitoringService(db)
        
        if execution_id:
            # Show specific execution
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == execution_id
            ).first()
            
            if not execution:
                click.echo(click.style(f"✗ Execution {execution_id} not found", fg='red'))
                return
            
            _display_execution_details(execution, verbose)
        else:
            # Show current system status
            click.echo("=" * 60)
            click.echo("Pipeline Status")
            click.echo("=" * 60)
            click.echo()
            
            # Get health status
            health = monitoring.get_health_status()
            
            # Display health status
            status_color = 'green' if health.status == 'healthy' else 'yellow' if health.status == 'degraded' else 'red'
            click.echo(f"System Health: {click.style(health.status.upper(), fg=status_color)}")
            click.echo()
            
            # Display last execution
            if health.last_execution:
                click.echo(f"Last Execution: {health.last_execution.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                click.echo("Last Execution: Never")
            click.echo()
            
            # Display data freshness
            click.echo("Data Freshness:")
            if health.data_freshness_days is not None:
                freshness_color = 'green' if health.data_freshness_days <= 2 else 'yellow' if health.data_freshness_days <= 7 else 'red'
                click.echo(f"  Climate Data: {click.style(f'{health.data_freshness_days} days old', fg=freshness_color)}")
            else:
                click.echo(f"  Climate Data: {click.style('No data', fg='red')}")
            
            if health.forecast_freshness_days is not None:
                forecast_color = 'green' if health.forecast_freshness_days <= 2 else 'yellow' if health.forecast_freshness_days <= 7 else 'red'
                click.echo(f"  Forecasts: {click.style(f'{health.forecast_freshness_days} days old', fg=forecast_color)}")
            else:
                click.echo(f"  Forecasts: {click.style('No forecasts', fg='red')}")
            click.echo()
            
            # Display failed sources
            if health.failed_sources:
                click.echo(click.style("Failed Sources:", fg='red'))
                for source in health.failed_sources:
                    click.echo(f"  - {source}")
                click.echo()
            
            # Display metrics if verbose
            if verbose:
                click.echo("Metrics:")
                metrics = monitoring.get_metrics()
                for metric_name, value in sorted(metrics.items()):
                    click.echo(f"  {metric_name}: {value}")
                click.echo()
            
            # Display recent executions
            recent_executions = db.query(PipelineExecution).order_by(
                PipelineExecution.started_at.desc()
            ).limit(5).all()
            
            if recent_executions:
                click.echo("Recent Executions:")
                table_data = []
                for exec in recent_executions:
                    status_symbol = '✓' if exec.status == 'completed' else '⚠' if exec.status == 'partial' else '✗'
                    table_data.append([
                        status_symbol,
                        exec.id[:12] + '...',
                        exec.execution_type,
                        exec.started_at.strftime('%Y-%m-%d %H:%M'),
                        f"{exec.duration_seconds}s" if exec.duration_seconds else 'N/A',
                        exec.status
                    ])
                
                click.echo(tabulate(
                    table_data,
                    headers=['', 'ID', 'Type', 'Started', 'Duration', 'Status'],
                    tablefmt='simple'
                ))
    
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
        raise
    finally:
        db.close()


@pipeline.command()
@click.option('--limit', default=10, help='Number of executions to show')
@click.option('--status-filter', default=None, help='Filter by status (completed/failed/partial)')
@click.option('--days', default=7, help='Show executions from last N days')
def history(limit: int, status_filter: str, days: int):
    """
    View pipeline execution history
    
    **Validates: Requirements 6.5**
    
    Examples:
        pipeline history                      # Show last 10 executions
        pipeline history --limit 20           # Show last 20 executions
        pipeline history --status-filter failed  # Show only failed executions
        pipeline history --days 30            # Show last 30 days
    """
    db = SessionLocal()
    try:
        click.echo("=" * 80)
        click.echo("Pipeline Execution History")
        click.echo("=" * 80)
        click.echo()
        
        # Build query
        query = db.query(PipelineExecution)
        
        # Filter by date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(PipelineExecution.started_at >= cutoff_date)
        
        # Filter by status
        if status_filter:
            query = query.filter(PipelineExecution.status == status_filter)
        
        # Order and limit
        executions = query.order_by(
            PipelineExecution.started_at.desc()
        ).limit(limit).all()
        
        if not executions:
            click.echo("No executions found matching criteria")
            return
        
        # Display summary
        click.echo(f"Showing {len(executions)} execution(s) from last {days} days")
        if status_filter:
            click.echo(f"Filtered by status: {status_filter}")
        click.echo()
        
        # Display table
        table_data = []
        for exec in executions:
            status_symbol = '✓' if exec.status == 'completed' else '⚠' if exec.status == 'partial' else '✗'
            
            table_data.append([
                status_symbol,
                exec.id[:16] + '...',
                exec.execution_type,
                exec.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                f"{exec.duration_seconds}s" if exec.duration_seconds else 'N/A',
                exec.records_stored or 0,
                exec.forecasts_generated or 0,
                exec.status
            ])
        
        click.echo(tabulate(
            table_data,
            headers=['', 'Execution ID', 'Type', 'Started At', 'Duration', 'Records', 'Forecasts', 'Status'],
            tablefmt='grid'
        ))
        
        # Display statistics
        click.echo()
        click.echo("Statistics:")
        total = len(executions)
        completed = sum(1 for e in executions if e.status == 'completed')
        partial = sum(1 for e in executions if e.status == 'partial')
        failed = sum(1 for e in executions if e.status == 'failed')
        
        click.echo(f"  Total: {total}")
        click.echo(f"  Completed: {click.style(str(completed), fg='green')} ({completed/total*100:.1f}%)")
        if partial > 0:
            click.echo(f"  Partial: {click.style(str(partial), fg='yellow')} ({partial/total*100:.1f}%)")
        if failed > 0:
            click.echo(f"  Failed: {click.style(str(failed), fg='red')} ({failed/total*100:.1f}%)")
        
        # Average duration
        durations = [e.duration_seconds for e in executions if e.duration_seconds]
        if durations:
            avg_duration = sum(durations) / len(durations)
            click.echo(f"  Average Duration: {avg_duration:.1f}s")
    
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
        raise
    finally:
        db.close()


@pipeline.command()
@click.option('--email/--no-email', default=True, help='Test email alerts')
@click.option('--slack/--no-slack', default=True, help='Test Slack alerts')
def test_alerts(email: bool, slack: bool):
    """
    Test alert delivery channels
    
    **Validates: Requirements 3.1**
    
    Examples:
        pipeline test-alerts                  # Test all channels
        pipeline test-alerts --no-slack       # Test email only
        pipeline test-alerts --no-email       # Test Slack only
    """
    click.echo("=" * 60)
    click.echo("Alert Delivery Test")
    click.echo("=" * 60)
    click.echo()
    
    async def run_tests():
        alert_service = AlertService()
        results = {}
        
        # Test email
        if email:
            click.echo("Testing email alerts...")
            try:
                await alert_service.send_email_alert(
                    subject="Test Alert - Climate EWS",
                    body="This is a test alert from the Climate Early Warning System.\n\n"
                         "If you receive this email, email alerts are configured correctly.",
                    alert_type="test"
                )
                click.echo(click.style("✓ Email alert sent successfully", fg='green'))
                results['email'] = True
            except Exception as e:
                click.echo(click.style(f"✗ Email alert failed: {str(e)}", fg='red'))
                results['email'] = False
            click.echo()
        
        # Test Slack
        if slack:
            click.echo("Testing Slack alerts...")
            try:
                await alert_service.send_slack_alert(
                    title="Test Alert - Climate EWS",
                    message="This is a test alert from the Climate Early Warning System.\n\n"
                            "If you receive this message, Slack alerts are configured correctly.",
                    severity="info",
                    alert_type="test"
                )
                click.echo(click.style("✓ Slack alert sent successfully", fg='green'))
                results['slack'] = True
            except Exception as e:
                click.echo(click.style(f"✗ Slack alert failed: {str(e)}", fg='red'))
                results['slack'] = False
            click.echo()
        
        # Summary
        click.echo("=" * 60)
        click.echo("Test Summary")
        click.echo("=" * 60)
        
        tested = []
        if email:
            tested.append(('Email', results.get('email', False)))
        if slack:
            tested.append(('Slack', results.get('slack', False)))
        
        for channel, success in tested:
            status = click.style('PASSED', fg='green') if success else click.style('FAILED', fg='red')
            click.echo(f"{channel}: {status}")
        
        all_passed = all(result for result in results.values())
        click.echo()
        if all_passed:
            click.echo(click.style("✓ All alert tests passed!", fg='green'))
        else:
            click.echo(click.style("✗ Some alert tests failed", fg='red'))
        
        return all_passed
    
    try:
        success = asyncio.run(run_tests())
        if not success:
            raise click.ClickException("Alert tests failed")
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
        raise


@pipeline.command()
def metrics():
    """
    Display pipeline metrics
    
    Shows Prometheus-formatted metrics for monitoring.
    
    Examples:
        pipeline metrics                      # Show all metrics
    """
    db = SessionLocal()
    try:
        monitoring = MonitoringService(db)
        
        click.echo("=" * 60)
        click.echo("Pipeline Metrics")
        click.echo("=" * 60)
        click.echo()
        
        # Get metrics
        metrics_dict = monitoring.get_metrics()
        
        if not metrics_dict:
            click.echo("No metrics available")
            return
        
        # Display in Prometheus format
        prometheus_text = monitoring.format_prometheus_metrics(metrics_dict)
        click.echo(prometheus_text)
        
        click.echo()
        click.echo("=" * 60)
        click.echo(f"Total Metrics: {len(metrics_dict)}")
    
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'))
        raise
    finally:
        db.close()


def _display_execution_details(execution: PipelineExecution, verbose: bool):
    """Helper function to display execution details"""
    click.echo("=" * 60)
    click.echo(f"Execution Details: {execution.id}")
    click.echo("=" * 60)
    click.echo()
    
    # Status
    status_color = 'green' if execution.status == 'completed' else 'yellow' if execution.status == 'partial' else 'red'
    click.echo(f"Status: {click.style(execution.status.upper(), fg=status_color)}")
    click.echo(f"Type: {execution.execution_type}")
    click.echo()
    
    # Timing
    click.echo("Timing:")
    click.echo(f"  Started: {execution.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if execution.completed_at:
        click.echo(f"  Completed: {execution.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if execution.duration_seconds:
        click.echo(f"  Duration: {execution.duration_seconds} seconds")
    click.echo()
    
    # Ingestion
    click.echo("Ingestion:")
    click.echo(f"  Records Fetched: {execution.records_fetched or 0}")
    click.echo(f"  Records Stored: {execution.records_stored or 0}")
    if execution.sources_succeeded:
        click.echo(f"  Sources Succeeded: {', '.join(execution.sources_succeeded)}")
    if execution.sources_failed:
        click.echo(f"  Sources Failed: {click.style(', '.join(execution.sources_failed), fg='red')}")
    click.echo()
    
    # Forecasting
    click.echo("Forecasting:")
    click.echo(f"  Forecasts Generated: {execution.forecasts_generated or 0}")
    click.echo(f"  Recommendations Created: {execution.recommendations_created or 0}")
    click.echo()
    
    # Error
    if execution.error_message:
        click.echo(click.style("Error Message:", fg='red'))
        click.echo(f"  {execution.error_message}")
        click.echo()
    
    # Verbose details
    if verbose and execution.error_details:
        click.echo("Error Details:")
        click.echo(execution.error_details)


if __name__ == '__main__':
    pipeline()
