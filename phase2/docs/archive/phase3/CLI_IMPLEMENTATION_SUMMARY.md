# CLI Implementation Summary - Task 19

## Overview

A comprehensive command-line interface (CLI) has been implemented for manual pipeline operations, providing full control over the automated forecast pipeline.

## Files Created

### 1. `backend/app/cli/pipeline_cli.py`
Main CLI implementation with all pipeline commands.

**Lines of Code**: ~600
**Commands**: 6 commands
**Features**:
- Colored output for better readability
- Tabular data display
- Error handling
- Async support for alerts
- Comprehensive help text

### 2. `backend/cli.py`
Main CLI entry point that integrates all command groups.

### 3. `backend/setup_cli.py`
Setup script for CLI installation as a package.

### 4. `backend/app/cli/__init__.py`
Module initialization file.

### 5. `docs/CLI_USAGE_GUIDE.md`
Comprehensive CLI usage documentation (500+ lines).

## Commands Implemented

### 1. `pipeline run` - Manual Pipeline Execution
**Validates: Requirements 7.1**

**Features**:
- Incremental or full data fetch
- Source selection
- Real-time progress display
- Colored status indicators
- Detailed execution results
- Error reporting

**Options**:
- `--incremental/--full`: Data fetch mode
- `--sources TEXT`: Comma-separated source list

**Example**:
```bash
pipeline run --incremental
pipeline run --full --sources chirps,era5
```

### 2. `pipeline status` - View Pipeline Status
**Validates: Requirements 7.3**

**Features**:
- System health status
- Last execution information
- Data freshness indicators
- Failed sources display
- Recent executions table
- Metrics display (verbose mode)
- Specific execution details

**Options**:
- `--execution-id TEXT`: Show specific execution
- `--verbose`: Show detailed metrics

**Example**:
```bash
pipeline status
pipeline status --verbose
pipeline status --execution-id exec-123
```

### 3. `pipeline history` - View Execution History
**Validates: Requirements 6.5**

**Features**:
- Execution history table
- Status filtering
- Date range filtering
- Execution statistics
- Success rate calculation
- Average duration
- Grid table format

**Options**:
- `--limit INTEGER`: Number of executions (default: 10)
- `--status-filter TEXT`: Filter by status
- `--days INTEGER`: Days to look back (default: 7)

**Example**:
```bash
pipeline history
pipeline history --limit 20 --status-filter failed
pipeline history --days 30
```

### 4. `pipeline test-alerts` - Test Alert Delivery
**Validates: Requirements 3.1**

**Features**:
- Email alert testing
- Slack alert testing
- Channel selection
- Test result summary
- Error reporting

**Options**:
- `--email/--no-email`: Test email alerts
- `--slack/--no-slack`: Test Slack alerts

**Example**:
```bash
pipeline test-alerts
pipeline test-alerts --no-slack
pipeline test-alerts --no-email
```

### 5. `pipeline metrics` - Display Metrics

**Features**:
- Prometheus-formatted metrics
- All available metrics
- Metric count summary

**Example**:
```bash
pipeline metrics
```

### 6. Helper Functions

**`_display_execution_details()`**:
- Detailed execution information
- Timing details
- Ingestion statistics
- Forecasting results
- Error messages
- Verbose mode support

## Technical Features

### Color-Coded Output
- **Green**: Success, healthy status
- **Yellow**: Warnings, degraded status, partial completion
- **Red**: Errors, failures, unhealthy status

### Status Symbols
- `✓`: Completed successfully
- `⚠`: Partial completion or warnings
- `✗`: Failed

### Table Formatting
Uses `tabulate` library for clean table display:
- Simple format for compact tables
- Grid format for detailed tables
- Headers and alignment
- Status symbols in tables

### Error Handling
- Try-catch blocks for all operations
- Graceful error messages
- Proper exit codes (0=success, 1=error)
- Database session cleanup

### Async Support
- Async/await for alert testing
- `asyncio.run()` for async operations
- Proper async function handling

## Installation Methods

### Method 1: Direct Execution
```bash
cd backend
python cli.py pipeline [command]
```

### Method 2: Package Installation (Recommended)
```bash
cd backend
pip install -e .
climate-cli pipeline [command]
```

### Method 3: Alias
```bash
alias pipeline="python /path/to/backend/cli.py pipeline"
```

## Dependencies

### Required Packages
- `click>=8.0.0`: CLI framework
- `tabulate>=0.9.0`: Table formatting
- `asyncio`: Async operations (built-in)
- `sqlalchemy`: Database operations
- `datetime`: Date/time handling (built-in)

### Application Dependencies
- `app.core.database`: Database session
- `app.services.pipeline.scheduler`: Pipeline scheduler
- `app.services.pipeline.orchestrator`: Pipeline orchestrator
- `app.services.pipeline.monitoring`: Monitoring service
- `app.services.pipeline.alerts`: Alert service
- `app.models.pipeline_execution`: Execution model

## Usage Examples

### Daily Operations
```bash
# Check system health
pipeline status

# Run manual update
pipeline run

# Review recent activity
pipeline history --limit 5
```

### Troubleshooting
```bash
# Check for failures
pipeline history --status-filter failed

# View specific execution
pipeline status --execution-id exec-123

# Test alerts
pipeline test-alerts

# Detailed status
pipeline status --verbose
```

### Monitoring
```bash
# View metrics
pipeline metrics

# Check data freshness
pipeline status | grep "Data Freshness"

# Monitor success rate
pipeline history --days 30
```

### Automation
```bash
# Cron job for daily execution
0 6 * * * cd /path/to/backend && python cli.py pipeline run

# Error notification
pipeline run || mail -s "Pipeline Failed" admin@example.com

# Daily report
pipeline status > daily-report.txt
pipeline history --days 1 >> daily-report.txt
```

## Docker Integration

Run CLI commands in Docker:
```bash
# Run pipeline
docker-compose exec backend python cli.py pipeline run

# Check status
docker-compose exec backend python cli.py pipeline status

# View history
docker-compose exec backend python cli.py pipeline history
```

## Documentation

### CLI Usage Guide
Comprehensive 500+ line guide covering:
- Installation methods
- All commands with examples
- Common workflows
- Troubleshooting
- Best practices
- Integration with cron
- Docker usage
- Environment variables

**Location**: `docs/CLI_USAGE_GUIDE.md`

## Requirements Validation

### Requirement 7.1: Manual Trigger Execution ✓
- `pipeline run` command
- Immediate execution
- Incremental/full options
- Source selection
- Result display

### Requirement 7.3: Status Reporting ✓
- `pipeline status` command
- Current system health
- Last execution info
- Data freshness
- Recent executions
- Specific execution details

### Requirement 6.5: Execution History ✓
- `pipeline history` command
- Execution logs
- Filtering options
- Statistics
- Date ranges

### Requirement 3.1: Alert Testing ✓
- `pipeline test-alerts` command
- Email testing
- Slack testing
- Channel selection
- Result reporting

## Testing

### Manual Testing
```bash
# Test each command
python cli.py pipeline run --help
python cli.py pipeline status --help
python cli.py pipeline history --help
python cli.py pipeline test-alerts --help
python cli.py pipeline metrics --help

# Test execution
python cli.py pipeline run
python cli.py pipeline status
python cli.py pipeline history
```

### Integration Testing
CLI commands can be tested in integration tests:
```python
from click.testing import CliRunner
from cli import cli

def test_pipeline_status():
    runner = CliRunner()
    result = runner.invoke(cli, ['pipeline', 'status'])
    assert result.exit_code == 0
```

## Future Enhancements

### Potential Additions
1. `pipeline logs` - View pipeline logs
2. `pipeline config` - View/edit configuration
3. `pipeline sources` - Manage data sources
4. `pipeline schedule` - View/edit schedule
5. `pipeline export` - Export execution data
6. `pipeline import` - Import configuration
7. `pipeline validate` - Validate configuration
8. `pipeline backup` - Backup database
9. `pipeline restore` - Restore from backup

### Improvements
1. Progress bars for long operations
2. Interactive mode for confirmations
3. JSON output format option
4. CSV export for history
5. Real-time log streaming
6. Configuration wizard
7. Auto-completion support
8. Shell integration

## Conclusion

The CLI provides a complete interface for manual pipeline operations, enabling:

1. **Manual Execution**: Run pipeline on-demand with custom options
2. **Status Monitoring**: Check system health and execution status
3. **History Review**: Analyze past executions and trends
4. **Alert Testing**: Verify alert configuration
5. **Metrics Display**: View Prometheus metrics

The CLI is production-ready with:
- ✅ Comprehensive command set
- ✅ Color-coded output
- ✅ Error handling
- ✅ Detailed documentation
- ✅ Docker integration
- ✅ Automation support
- ✅ Requirements validation

**Task 19 is complete and ready for use!**
