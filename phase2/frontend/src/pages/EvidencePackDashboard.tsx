import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import AssessmentIcon from '@mui/material/Icon';
import RefreshIcon from '@mui/icons-material/Refresh';
import ScienceIcon from '@mui/icons-material/Science';
import GetAppIcon from '@mui/icons-material/GetApp';

// Mock types for the API response
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

export default function EvidencePackDashboard() {
    const [metrics, setMetrics] = useState<EvidenceMetrics | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchMetrics = async () => {
        setLoading(true);
        setError(null);
        try {
            const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
            const response = await fetch(`${apiUrl}/v1/evidence-pack/metrics`);
            if (!response.ok) {
                throw new Error('Failed to fetch evidence metrics');
            }
            const data = await response.json();
            setMetrics(data);
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'An error occurred while fetching metrics');
        } finally {
            setLoading(false);
        }
    };

    const triggerEvaluation = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
            await fetch(`${apiUrl}/v1/evidence-pack/evaluate`, { method: 'POST' });
            fetchMetrics();
        } catch (err) {
            console.error('Trigger eval failed', err);
        }
    };

    const downloadEvidencePack = async () => {
        try {
            const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
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

            {/* KPI Cards */}
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

            {/* Confusion Matrix Cards */}
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

            {/* Events Table */}
            <Card elevation={3}>
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
        </Box>
    );
}
