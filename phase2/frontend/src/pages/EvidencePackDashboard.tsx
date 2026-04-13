import { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Grid,
    Card,
    CardContent,
    CircularProgress,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Chip,
    Button,
    LinearProgress,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ScienceIcon from '@mui/icons-material/Science';
import GetAppIcon from '@mui/icons-material/GetApp';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ScheduleIcon from '@mui/icons-material/Schedule';

// Existing types
interface EventMetric {
    id: string;
    issued_at: string;
    predicted_prob: number;
    actual_outcome: number;
    brier_score: number;
}

interface EvidenceMetrics {
    brier_score: number;
    rmse: number;
    calibration_error: number;
    total_evaluated: number;
    confusion_matrix: { tp: number; fp: number; tn: number; fn: number };
    events: EventMetric[];
}

// New types for execution log
interface ShadowRunProgress {
    total_forecast_logs: number;
    target: number;
    pct_complete: number;
    start_date: string;
    end_date: string;
}

interface ExecutionRecord {
    id: string;
    execution_type: string;
    status: string;
    started_at: string | null;
    duration_seconds: number | null;
    forecasts_generated: number;
    records_stored: number;
    sources_succeeded: string[];
    sources_failed: string[];
    error_message: string | null;
}

interface ExecutionLog {
    shadow_run: ShadowRunProgress;
    executions: ExecutionRecord[];
}

export default function EvidencePackDashboard() {
    const [metrics, setMetrics] = useState<EvidenceMetrics | null>(null);
    const [executionLog, setExecutionLog] = useState<ExecutionLog | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const apiUrl = import.meta.env.VITE_API_BASE_URL || '/api';

    const fetchMetrics = async () => {
        setLoading(true);
        setError(null);
        try {
            const [metricsRes, logRes] = await Promise.all([
                fetch(`${apiUrl}/v1/evidence-pack/metrics`),
                fetch(`${apiUrl}/v1/evidence-pack/execution-log`),
            ]);
            if (!metricsRes.ok) throw new Error('Failed to fetch evidence metrics');
            if (!logRes.ok) throw new Error('Failed to fetch execution log');
            const [metricsData, logData] = await Promise.all([
                metricsRes.json(),
                logRes.json(),
            ]);
            setMetrics(metricsData);
            setExecutionLog(logData);
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'An error occurred while fetching metrics');
        } finally {
            setLoading(false);
        }
    };

    const triggerEvaluation = async () => {
        try {
            await fetch(`${apiUrl}/v1/evidence-pack/evaluate`, { method: 'POST' });
            fetchMetrics();
        } catch (err) {
            console.error('Trigger eval failed', err);
        }
    };

    const downloadEvidencePack = async () => {
        try {
            const response = await fetch(`${apiUrl}/v1/evidence-pack/generate`, { method: 'POST' });
            if (!response.ok) throw new Error('Failed to generate evidence pack');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'hewasense_evidence_pack.zip';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err: any) {
            console.error('Download failed', err);
            setError(err.message || 'Failed to download evidence pack');
        }
    };

    useEffect(() => {
        fetchMetrics();
    }, []);

    if (loading && !metrics) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    const sr = executionLog?.shadow_run;

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScienceIcon fontSize="large" color="primary" />
                    Shadow-Run Evidence Pack
                </Typography>
                <Box>
                    <Button
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={fetchMetrics}
                        sx={{ mr: 1 }}
                    >
                        Refresh
                    </Button>
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={triggerEvaluation}
                    >
                        Run Evaluation
                    </Button>
                    <Button
                        variant="contained"
                        color="success"
                        startIcon={<GetAppIcon />}
                        onClick={downloadEvidencePack}
                        sx={{ ml: 1 }}
                    >
                        Download Evidence Pack
                    </Button>
                </Box>
            </Box>

            {error && (
                <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>
            )}

            {/* ── Shadow Run Progress ── */}
            <Card elevation={3} sx={{ mb: 4, borderTop: '4px solid #1976d2' }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ScheduleIcon color="primary" />
                        Shadow Run Progress
                    </Typography>
                    <Grid container spacing={3} alignItems="center">
                        <Grid item xs={12} md={7}>
                            <Box sx={{ mb: 1, display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2" color="textSecondary">
                                    Forecast logs accumulated
                                </Typography>
                                <Typography variant="body2" fontWeight="bold">
                                    {sr?.total_forecast_logs ?? '--'} / {sr?.target ?? 2160} ({sr?.pct_complete ?? 0}%)
                                </Typography>
                            </Box>
                            <LinearProgress
                                variant="determinate"
                                value={sr?.pct_complete ?? 0}
                                sx={{ height: 12, borderRadius: 6 }}
                            />
                            <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                                {sr?.start_date ?? '2026-04-14'} → {sr?.end_date ?? '2026-07-13'} · 90 days × {sr?.forecasts_per_day ?? 24} forecasts/day
                            </Typography>
                            <Box sx={{ mt: 1, p: 1.5, bgcolor: '#e3f2fd', borderRadius: 1, border: '1px solid #90caf9' }}>
                                <Typography variant="caption" color="textSecondary">
                                    <strong>Two-zone configuration:</strong> Ifakara TC (id=7, 400 farmers) + Mlimba DC (id=8, 600 farmers).
                                    Each zone generates 12 forecasts/day (3 triggers × 4 horizons) = 24 total.
                                    Target: 2,160 forecasts over 90 days.
                                </Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} md={5}>
                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <Box sx={{ textAlign: 'center', p: 1, bgcolor: '#f0f4ff', borderRadius: 2 }}>
                                        <Typography variant="h4" color="primary" fontWeight="bold">
                                            {sr ? Math.round(sr.total_forecast_logs / 24) : '--'}
                                        </Typography>
                                        <Typography variant="caption" color="textSecondary">Days Completed</Typography>
                                    </Box>
                                </Grid>
                                <Grid item xs={6}>
                                    <Box sx={{ textAlign: 'center', p: 1, bgcolor: '#f0fff4', borderRadius: 2 }}>
                                        <Typography variant="h4" sx={{ color: '#2e7d32' }} fontWeight="bold">
                                            {sr ? sr.target - sr.total_forecast_logs : '--'}
                                        </Typography>
                                        <Typography variant="caption" color="textSecondary">Forecasts Remaining</Typography>
                                    </Box>
                                </Grid>
                            </Grid>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {/* ── KPI Cards ── */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #1976d2' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                Brier Score
                            </Typography>
                            <Typography variant="h3" component="div" color="primary">
                                {metrics?.brier_score !== undefined ? metrics.brier_score.toFixed(4) : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Lower is better (Range: 0-1)
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #2e7d32' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                RMSE
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#2e7d32' }}>
                                {metrics?.rmse !== undefined ? metrics.rmse.toFixed(4) : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Root Mean Square Error
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #ed6c02' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                Expected Calibration Error
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#ed6c02' }}>
                                {metrics?.calibration_error !== undefined ? metrics.calibration_error.toFixed(4) : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Reliability of probabilities
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #9c27b0' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                Total Evaluated Periods
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#9c27b0' }}>
                                {metrics?.total_evaluated !== undefined ? metrics.total_evaluated : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Logs past valid_until date
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* ── Confusion Matrix Cards ── */}
            <Typography variant="h6" sx={{ mb: 2 }}>
                Confusion Matrix
            </Typography>
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #2e7d32' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                True Positives
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#2e7d32' }}>
                                {metrics?.confusion_matrix?.tp !== undefined ? metrics.confusion_matrix.tp : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Correctly predicted triggers
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #d32f2f' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                False Positives
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#d32f2f' }}>
                                {metrics?.confusion_matrix?.fp !== undefined ? metrics.confusion_matrix.fp : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                False alarms
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #1976d2' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                True Negatives
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#1976d2' }}>
                                {metrics?.confusion_matrix?.tn !== undefined ? metrics.confusion_matrix.tn : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Correctly predicted no-trigger
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #ed6c02' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                False Negatives
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#ed6c02' }}>
                                {metrics?.confusion_matrix?.fn !== undefined ? metrics.confusion_matrix.fn : '--'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Missed triggers
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* ── Evaluated Forecast Snapshots ── */}
            <Card elevation={3} sx={{ mb: 4 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Evaluated Forecast Snapshots
                    </Typography>
                    <TableContainer component={Paper} elevation={0} variant="outlined">
                        <Table>
                            <TableHead>
                                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                                    <TableCell><strong>Issued At</strong></TableCell>
                                    <TableCell><strong>Predicted Prob</strong></TableCell>
                                    <TableCell><strong>Actual Outcome</strong></TableCell>
                                    <TableCell><strong>Brier Score (Event)</strong></TableCell>
                                    <TableCell><strong>Status</strong></TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {metrics?.events && metrics.events.length > 0 ? (
                                    metrics.events.map((event) => (
                                        <TableRow key={event.id}>
                                            <TableCell>{new Date(event.issued_at).toLocaleString()}</TableCell>
                                            <TableCell>{(event.predicted_prob * 100).toFixed(1)}%</TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={event.actual_outcome === 1 ? 'Triggered' : 'No Trigger'}
                                                    color={event.actual_outcome === 1 ? 'error' : 'success'}
                                                    size="small"
                                                />
                                            </TableCell>
                                            <TableCell>{event.brier_score.toFixed(4)}</TableCell>
                                            <TableCell>
                                                <Chip label="Evaluated" color="info" size="small" variant="outlined" />
                                            </TableCell>
                                        </TableRow>
                                    ))
                                ) : (
                                    <TableRow>
                                        <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                                            <Typography color="textSecondary">No evaluated forecast logs available yet.</Typography>
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            {/* ── Execution History ── */}
            <Card elevation={3}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Pipeline Execution History (last 30 runs)
                    </Typography>
                    <TableContainer component={Paper} elevation={0} variant="outlined" sx={{ maxHeight: 400 }}>
                        <Table size="small" stickyHeader>
                            <TableHead>
                                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                                    <TableCell><strong>Date / Time (EAT)</strong></TableCell>
                                    <TableCell><strong>Status</strong></TableCell>
                                    <TableCell><strong>Duration</strong></TableCell>
                                    <TableCell><strong>Forecasts</strong></TableCell>
                                    <TableCell><strong>Records Stored</strong></TableCell>
                                    <TableCell><strong>Sources OK / Failed</strong></TableCell>
                                    <TableCell><strong>Execution ID</strong></TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {executionLog?.executions && executionLog.executions.length > 0 ? (
                                    executionLog.executions.map((ex) => {
                                        const date = ex.started_at
                                            ? new Date(ex.started_at).toLocaleString('en-GB', {
                                                  timeZone: 'Africa/Dar_es_Salaam',
                                                  day: '2-digit',
                                                  month: 'short',
                                                  year: 'numeric',
                                                  hour: '2-digit',
                                                  minute: '2-digit',
                                              })
                                            : '--';
                                        const isOk = ex.status === 'completed';
                                        return (
                                            <TableRow key={ex.id} hover>
                                                <TableCell>{date}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        icon={isOk ? <CheckCircleIcon /> : <ErrorIcon />}
                                                        label={isOk ? 'SUCCESS' : ex.status.toUpperCase()}
                                                        color={isOk ? 'success' : 'error'}
                                                        size="small"
                                                        variant="outlined"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    {ex.duration_seconds != null ? `${ex.duration_seconds}s` : '--'}
                                                </TableCell>
                                                <TableCell>{ex.forecasts_generated}</TableCell>
                                                <TableCell>{ex.records_stored}</TableCell>
                                                <TableCell>
                                                    <Typography variant="caption" sx={{ color: '#2e7d32' }}>
                                                        ✓ {ex.sources_succeeded.join(', ') || '—'}
                                                    </Typography>
                                                    {ex.sources_failed.length > 0 && (
                                                        <Typography variant="caption" sx={{ color: '#ed6c02', display: 'block' }}>
                                                            ⚠ {ex.sources_failed.join(', ')}
                                                        </Typography>
                                                    )}
                                                </TableCell>
                                                <TableCell>
                                                    <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                                                        {ex.id.slice(0, 8)}…
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })
                                ) : (
                                    <TableRow>
                                        <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                                            <Typography color="textSecondary">No pipeline executions recorded yet.</Typography>
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>
        </Box>
    );
}
