import { useState, useEffect, useMemo } from 'react';
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
    Tabs,
    Tab,
    Alert,
    Tooltip,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ScienceIcon from '@mui/icons-material/Science';
import GetAppIcon from '@mui/icons-material/GetApp';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ScheduleIcon from '@mui/icons-material/Schedule';
import GavelIcon from '@mui/icons-material/Gavel';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

// ---------------------------------------------------------------------------
// Types — aligned with the zone-aware backend responses
// ---------------------------------------------------------------------------

interface ConfusionMatrix {
    tp: number;
    fp: number;
    tn: number;
    fn: number;
}

interface EventMetric {
    id: string;
    issued_at: string;
    region_id?: string;
    predicted_prob: number;
    actual_outcome: number;
    brier_score: number;
}

interface ZoneMetrics {
    location_id: number;
    zone_name: string;
    brier_score: number;
    rmse: number;
    calibration_error: number;
    total_evaluated: number;
    confusion_matrix: ConfusionMatrix;
    events: EventMetric[];
}

interface EvidenceMetrics {
    brier_score: number;
    rmse: number;
    calibration_error: number;
    total_evaluated: number;
    confusion_matrix: ConfusionMatrix;
    events: EventMetric[];
    zones: Record<string, ZoneMetrics>;
}

interface BasisRiskZone {
    location_id: number;
    zone_name: string;
    proxy_basis_risk_pct: number | null;
    gate_pass: boolean | null;
    total_primary: number;
    corroborated: number;
    uncorroborated: number;
    no_ndvi_data: number;
    excluded_flood: number;
    methodology_note: string;
}

interface BasisRiskData {
    proxy_basis_risk_pct: number | null;
    gate_pass: boolean | null;
    total_primary: number;
    corroborated: number;
    uncorroborated: number;
    no_ndvi_data: number;
    excluded_flood: number;
    methodology_note: string;
    zones: Record<string, BasisRiskZone>;
}

interface ZoneInfo {
    location_id: number;
    name: string;
    latitude: number;
    longitude: number;
}

interface ShadowRunProgress {
    total_forecast_logs: number;
    target: number;
    pct_complete: number;
    start_date: string;
    end_date: string;
    zones: ZoneInfo[];
    forecasts_per_day: number;
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

interface GateDetail {
    brier_score: { value: number | null; threshold: number; pass: boolean };
    basis_risk: { value: number | null; threshold: number; pass: boolean | null; label: string };
    verdict: string;
    zone_name?: string;
    location_id?: number;
}

interface FinalReport {
    generated_at: string;
    go_live_gates: {
        overall_verdict: string;
        zones: Record<string, GateDetail>;
    } & GateDetail;
    aggregate_metrics: EvidenceMetrics;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BRIER_GATE = 0.25;
const BASIS_RISK_GATE = 30.0;

function gateColor(pass: boolean | null): 'success' | 'error' | 'warning' {
    if (pass === true) return 'success';
    if (pass === false) return 'error';
    return 'warning';
}

function verdictChip(verdict: string) {
    const color = verdict === 'GO' ? 'success' : verdict.startsWith('NO-GO') ? 'error' : 'warning';
    return <Chip label={verdict} color={color} sx={{ fontWeight: 700 }} />;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EvidencePackDashboard() {
    const [metrics, setMetrics] = useState<EvidenceMetrics | null>(null);
    const [basisRisk, setBasisRisk] = useState<BasisRiskData | null>(null);
    const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
    const [executionLog, setExecutionLog] = useState<ExecutionLog | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [zoneTab, setZoneTab] = useState<string>('all');

    const apiUrl = import.meta.env.VITE_API_BASE_URL || '/api';

    // Derive zone list from the API response — never hardcoded
    const zoneList: ZoneInfo[] = useMemo(
        () => executionLog?.shadow_run?.zones ?? [],
        [executionLog],
    );

    // The metrics/basis-risk slice for the currently selected tab
    const activeMetrics: ZoneMetrics | EvidenceMetrics | null = useMemo(() => {
        if (!metrics) return null;
        if (zoneTab === 'all') return metrics;
        return metrics.zones?.[zoneTab] ?? null;
    }, [metrics, zoneTab]);

    const activeBasis: BasisRiskZone | BasisRiskData | null = useMemo(() => {
        if (!basisRisk) return null;
        if (zoneTab === 'all') return basisRisk;
        return basisRisk.zones?.[zoneTab] ?? null;
    }, [basisRisk, zoneTab]);

    // Events filtered by zone
    const activeEvents: EventMetric[] = useMemo(() => {
        if (!activeMetrics) return [];
        return activeMetrics.events ?? [];
    }, [activeMetrics]);

    // ── Data fetching ──

    const fetchAll = async () => {
        setLoading(true);
        setError(null);
        try {
            const [metricsRes, logRes, basisRes, reportRes] = await Promise.all([
                fetch(`${apiUrl}/v1/evidence-pack/metrics`),
                fetch(`${apiUrl}/v1/evidence-pack/execution-log`),
                fetch(`${apiUrl}/v1/evidence-pack/basis-risk`),
                fetch(`${apiUrl}/v1/evidence-pack/final-report`),
            ]);

            if (!metricsRes.ok) throw new Error('Failed to fetch evidence metrics');
            if (!logRes.ok) throw new Error('Failed to fetch execution log');

            const [metricsData, logData] = await Promise.all([
                metricsRes.json(),
                logRes.json(),
            ]);
            setMetrics(metricsData);
            setExecutionLog(logData);

            // Basis risk — may have no data yet (still returns 200)
            if (basisRes.ok) setBasisRisk(await basisRes.json());

            // Final report — 404 until shadow run completes
            if (reportRes.ok) setFinalReport(await reportRes.json());
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'An error occurred while fetching data');
        } finally {
            setLoading(false);
        }
    };

    const triggerEvaluation = async () => {
        try {
            await fetch(`${apiUrl}/v1/evidence-pack/evaluate`, { method: 'POST' });
            fetchAll();
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
        fetchAll();
    }, []);

    if (loading && !metrics) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    const sr = executionLog?.shadow_run;

    // ── Render helpers ──

    const renderKPICards = (m: ZoneMetrics | EvidenceMetrics | null) => {
        if (!m) return null;
        const brierPass = m.brier_score < BRIER_GATE;
        return (
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: `4px solid ${brierPass ? '#2e7d32' : '#d32f2f'}` }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                Brier Score
                            </Typography>
                            <Tooltip title={`Gate: < ${BRIER_GATE}`}>
                                <Typography variant="h3" component="div" sx={{ color: brierPass ? '#2e7d32' : '#d32f2f' }}>
                                    {m.brier_score.toFixed(4)}
                                </Typography>
                            </Tooltip>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Gate: {'<'} {BRIER_GATE} · {brierPass ? 'PASS' : 'FAIL'}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card elevation={3} sx={{ height: '100%', borderTop: '4px solid #1976d2' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                                RMSE
                            </Typography>
                            <Typography variant="h3" component="div" color="primary">
                                {m.rmse.toFixed(4)}
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
                                {m.calibration_error.toFixed(4)}
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
                                Total Evaluated
                            </Typography>
                            <Typography variant="h3" component="div" sx={{ color: '#9c27b0' }}>
                                {m.total_evaluated}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                Logs past valid_until date
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        );
    };

    const renderConfusionMatrix = (cm: ConfusionMatrix | undefined) => {
        if (!cm) return null;
        const items = [
            { label: 'True Positives', key: 'tp', color: '#2e7d32', desc: 'Correctly predicted triggers' },
            { label: 'False Positives', key: 'fp', color: '#d32f2f', desc: 'False alarms' },
            { label: 'True Negatives', key: 'tn', color: '#1976d2', desc: 'Correctly predicted no-trigger' },
            { label: 'False Negatives', key: 'fn', color: '#ed6c02', desc: 'Missed triggers' },
        ] as const;
        return (
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {items.map(({ label, key, color, desc }) => (
                    <Grid item xs={12} sm={6} md={3} key={key}>
                        <Card elevation={3} sx={{ height: '100%', borderTop: `4px solid ${color}` }}>
                            <CardContent>
                                <Typography color="textSecondary" gutterBottom variant="subtitle2">{label}</Typography>
                                <Typography variant="h3" component="div" sx={{ color }}>{cm[key]}</Typography>
                                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>{desc}</Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        );
    };

    const renderBasisRisk = (br: BasisRiskZone | BasisRiskData | null) => {
        if (!br) return null;
        const pct = br.proxy_basis_risk_pct;
        const pass = br.gate_pass;
        return (
            <Card elevation={3} sx={{ mb: 4, borderTop: `4px solid ${pass === true ? '#2e7d32' : pass === false ? '#d32f2f' : '#ed6c02'}` }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <WarningAmberIcon color={gateColor(pass)} />
                        NDVI Proxy Basis Risk
                    </Typography>
                    <Grid container spacing={3}>
                        <Grid item xs={12} sm={4}>
                            <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
                                <Typography variant="h3" sx={{ color: pass === true ? '#2e7d32' : pass === false ? '#d32f2f' : '#ed6c02' }}>
                                    {pct !== null ? `${pct}%` : '--'}
                                </Typography>
                                <Typography variant="body2" color="textSecondary">
                                    Gate: {'<'} {BASIS_RISK_GATE}% · {pass === true ? 'PASS' : pass === false ? 'FAIL' : 'PENDING'}
                                </Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={8}>
                            <Grid container spacing={1}>
                                {[
                                    { label: 'Primary Triggers', value: br.total_primary },
                                    { label: 'Corroborated', value: br.corroborated },
                                    { label: 'Uncorroborated', value: br.uncorroborated },
                                    { label: 'No NDVI Data', value: br.no_ndvi_data },
                                    { label: 'Flood Excluded', value: br.excluded_flood },
                                ].map(({ label, value }) => (
                                    <Grid item xs={6} sm={4} key={label}>
                                        <Typography variant="caption" color="textSecondary">{label}</Typography>
                                        <Typography variant="h6">{value}</Typography>
                                    </Grid>
                                ))}
                            </Grid>
                            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                                {br.methodology_note}
                            </Typography>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        );
    };

    const renderGoNoGoGates = () => {
        if (!finalReport) return null;
        const gates = finalReport.go_live_gates;
        const zoneGates = gates.zones ?? {};
        return (
            <Card elevation={3} sx={{ mb: 4, borderTop: '4px solid #1976d2' }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <GavelIcon color="primary" />
                        GO / NO-GO Gates
                    </Typography>

                    {/* Overall verdict */}
                    <Box sx={{ mb: 3, p: 2, bgcolor: '#f0f4ff', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="subtitle1" fontWeight="bold">Overall Verdict:</Typography>
                        {verdictChip(gates.overall_verdict)}
                    </Box>

                    {/* Per-zone verdicts */}
                    <Grid container spacing={2}>
                        {Object.entries(zoneGates).map(([zoneId, gate]) => (
                            <Grid item xs={12} sm={6} key={zoneId}>
                                <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 2 }}>
                                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                        {gate.zone_name ?? `Zone ${zoneId}`}
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                                        {verdictChip(gate.verdict)}
                                    </Box>
                                    <Typography variant="caption" color="textSecondary">
                                        Brier: {gate.brier_score?.value?.toFixed(4) ?? '--'} (
                                        <Chip
                                            label={gate.brier_score?.pass ? 'PASS' : 'FAIL'}
                                            color={gate.brier_score?.pass ? 'success' : 'error'}
                                            size="small"
                                            variant="outlined"
                                            sx={{ height: 18, fontSize: '0.65rem' }}
                                        />) · Basis Risk: {gate.basis_risk?.value !== null ? `${gate.basis_risk.value}%` : '--'} (
                                        <Chip
                                            label={gate.basis_risk?.pass === true ? 'PASS' : gate.basis_risk?.pass === false ? 'FAIL' : 'PENDING'}
                                            color={gateColor(gate.basis_risk?.pass ?? null)}
                                            size="small"
                                            variant="outlined"
                                            sx={{ height: 18, fontSize: '0.65rem' }}
                                        />)
                                    </Typography>
                                </Box>
                            </Grid>
                        ))}
                    </Grid>
                </CardContent>
            </Card>
        );
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* ── Header ── */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScienceIcon fontSize="large" color="primary" />
                    Shadow-Run Evidence Pack
                </Typography>
                <Box>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchAll} sx={{ mr: 1 }}>
                        Refresh
                    </Button>
                    <Button variant="contained" color="primary" onClick={triggerEvaluation}>
                        Run Evaluation
                    </Button>
                    <Button variant="contained" color="success" startIcon={<GetAppIcon />} onClick={downloadEvidencePack} sx={{ ml: 1 }}>
                        Download Evidence Pack
                    </Button>
                </Box>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

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
                                    {sr?.total_forecast_logs ?? '--'} / {sr?.target ?? '--'} ({sr?.pct_complete ?? 0}%)
                                </Typography>
                            </Box>
                            <LinearProgress variant="determinate" value={sr?.pct_complete ?? 0} sx={{ height: 12, borderRadius: 6 }} />
                            <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                                {sr?.start_date ?? '--'} → {sr?.end_date ?? '--'} · {sr?.forecasts_per_day ?? '--'} forecasts/day
                            </Typography>
                            {zoneList.length > 0 && (
                                <Box sx={{ mt: 1, p: 1.5, bgcolor: '#e3f2fd', borderRadius: 1, border: '1px solid #90caf9' }}>
                                    <Typography variant="caption" color="textSecondary">
                                        <strong>{zoneList.length}-zone configuration:</strong>{' '}
                                        {zoneList.map(z => `${z.name} (id=${z.location_id})`).join(' + ')}.
                                        {' '}Each zone generates {sr ? sr.forecasts_per_day / zoneList.length : '--'} forecasts/day
                                        (3 triggers x 4 horizons) = {sr?.forecasts_per_day ?? '--'} total.
                                    </Typography>
                                </Box>
                            )}
                        </Grid>
                        <Grid item xs={12} md={5}>
                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <Box sx={{ textAlign: 'center', p: 1, bgcolor: '#f0f4ff', borderRadius: 2 }}>
                                        <Typography variant="h4" color="primary" fontWeight="bold">
                                            {sr ? Math.round(sr.total_forecast_logs / sr.forecasts_per_day) : '--'}
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

            {/* ── GO/NO-GO Gates (only after shadow run completes) ── */}
            {renderGoNoGoGates()}

            {/* ── Zone Tabs ── */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs
                    value={zoneTab}
                    onChange={(_e, v) => setZoneTab(v)}
                    textColor="primary"
                    indicatorColor="primary"
                >
                    <Tab label="All Zones (Aggregate)" value="all" />
                    {zoneList.map(z => (
                        <Tab key={z.location_id} label={z.name} value={String(z.location_id)} />
                    ))}
                </Tabs>
            </Box>

            {/* ── KPI Cards ── */}
            {renderKPICards(activeMetrics)}

            {/* ── Basis Risk ── */}
            {renderBasisRisk(activeBasis)}

            {/* ── Confusion Matrix ── */}
            <Typography variant="h6" sx={{ mb: 2 }}>Confusion Matrix</Typography>
            {renderConfusionMatrix(activeMetrics?.confusion_matrix)}

            {/* ── Evaluated Forecast Snapshots ── */}
            <Card elevation={3} sx={{ mb: 4 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Evaluated Forecast Snapshots
                        {zoneTab !== 'all' && (
                            <Chip label={zoneList.find(z => String(z.location_id) === zoneTab)?.name ?? zoneTab} size="small" sx={{ ml: 1 }} />
                        )}
                    </Typography>
                    <TableContainer component={Paper} elevation={0} variant="outlined">
                        <Table>
                            <TableHead>
                                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                                    <TableCell><strong>Issued At</strong></TableCell>
                                    {zoneTab === 'all' && <TableCell><strong>Zone</strong></TableCell>}
                                    <TableCell><strong>Predicted Prob</strong></TableCell>
                                    <TableCell><strong>Actual Outcome</strong></TableCell>
                                    <TableCell><strong>Brier Score</strong></TableCell>
                                    <TableCell><strong>Status</strong></TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {activeEvents.length > 0 ? (
                                    activeEvents.map((event) => {
                                        const zoneName = zoneList.find(z => String(z.location_id) === event.region_id)?.name;
                                        return (
                                            <TableRow key={event.id}>
                                                <TableCell>{new Date(event.issued_at).toLocaleString()}</TableCell>
                                                {zoneTab === 'all' && (
                                                    <TableCell>
                                                        <Chip label={zoneName ?? event.region_id ?? '--'} size="small" variant="outlined" />
                                                    </TableCell>
                                                )}
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
                                        );
                                    })
                                ) : (
                                    <TableRow>
                                        <TableCell colSpan={zoneTab === 'all' ? 6 : 5} align="center" sx={{ py: 3 }}>
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
                                                        {ex.sources_succeeded.join(', ') || '--'}
                                                    </Typography>
                                                    {ex.sources_failed.length > 0 && (
                                                        <Typography variant="caption" sx={{ color: '#ed6c02', display: 'block' }}>
                                                            {ex.sources_failed.join(', ')}
                                                        </Typography>
                                                    )}
                                                </TableCell>
                                                <TableCell>
                                                    <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                                                        {ex.id.slice(0, 8)}...
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
