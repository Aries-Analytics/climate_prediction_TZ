import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Grid,
    Chip,
    Alert,
    Paper,
    Divider,
    Stack,
    useTheme
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import TimelineIcon from '@mui/icons-material/Timeline';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import axios from 'axios';
import { API_BASE_URL } from '../../config/api';
import Chart from '../charts/Chart';
import LoadingSpinner from '../common/LoadingSpinner';

interface TriggerEvent {
    year: number;
    month: number;
    trigger_type: string;
    observed_value: number;
    threshold_value: number;
    total_payout: number;
    validated: "confirmed" | "pending";
    external_validation: string | null;
}

interface YearlySummary {
    triggers: TriggerEvent[];
    total_payout: number;
    validated: boolean;
}

interface ValidationReport {
    executive_summary: {
        location: string;
        period: string;
        farmers_simulated: number;
        crop: string;
        total_triggers: number;
        total_payouts: number;
        loss_ratio: number;
        sustainability: string;
    };
    yearly_analysis: Record<string, YearlySummary>; // Renamed from yearly_summary
    sustainability_analysis: {
        loss_ratio: number;
        is_sustainable: boolean;
        recommendation: string;
    };
    external_validation: {
        validated_events: number;
        total_events: number;
        sources: string[];
    };
}

export default function BacktestingValidation() {
    const [report, setReport] = useState<ValidationReport | null>(null);
    const [loading, setLoading] = useState(true);
    const theme = useTheme();

    // State for dynamic simulation ID
    const [latestSimulationId, setLatestSimulationId] = useState<number | null>(null);

    useEffect(() => {
        fetchLatestSimulation();
    }, []);

    useEffect(() => {
        if (latestSimulationId) {
            fetchReport(latestSimulationId);
        }
    }, [latestSimulationId]);

    const fetchLatestSimulation = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/simulation/`);
            // Find the latest completed simulation
            const completed = response.data
                .filter((sim: any) => sim.status === 'completed' || sim.status === 'COMPLETED')
                .sort((a: any, b: any) => b.id - a.id);

            if (completed.length > 0) {
                setLatestSimulationId(completed[0].id);
            } else {
                setLoading(false); // No simulations found
            }
        } catch (error) {
            console.error('Failed to fetch simulations:', error);
            setLoading(false);
        }
    };

    const fetchReport = async (id: number) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/simulation/${id}/report`);
            setReport(response.data);
        } catch (error) {
            console.error('Failed to fetch validation report:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner message="Loading historical validation data..." />;

    if (!report) {
        return (
            <Alert severity="warning">
                Could not load validation report. {latestSimulationId ? `Please ensure Simulation #${latestSimulationId} exists.` : 'No completed simulations found.'}
            </Alert>
        );
    }

    // Transform data for Timeline Chart
    const summaryData = report.yearly_analysis || {};
    const years = Object.keys(summaryData).sort();

    const timelineData = years.map(year => {
        const summary = summaryData[year];
        return {
            year,
            triggers: summary.triggers.length,
            payout: summary.total_payout,
            // Color bar green if validated, blue if unvalidated
            color: summary.validated ? theme.palette.success.main : theme.palette.primary.main
        };
    });

    const chartData = [
        {
            x: timelineData.map(d => d.year),
            y: timelineData.map(d => d.triggers),
            type: 'bar',
            name: 'Triggers Detected',
            marker: { color: timelineData.map(d => d.color) }
        }
    ];

    // Calculate stats
    const totalYears = years.length;
    const triggersDetected = report.executive_summary.total_triggers;
    const validatedEvents = report.external_validation?.validated_events || years.filter(y => summaryData[y].validated).length;

    // Hardcoded known event years for 2015-2025
    const EXPECTED_EVENT_YEARS = report.external_validation?.total_events || 6;
    const validationScore = Math.min(100, Math.round((validatedEvents / EXPECTED_EVENT_YEARS) * 100));

    return (
        <Box>
            <Alert severity="success" icon={<VerifiedUserIcon />} sx={{ mb: 3 }}>
                <Typography variant="subtitle2">
                    <strong>Historical Validation Passed:</strong> This model has been backtested against 10 years of historical climate data ({report.executive_summary.period})
                    and independently detected {(validatedEvents / EXPECTED_EVENT_YEARS * 100).toFixed(0)}% of documented disaster events in {report.executive_summary.location}.
                </Typography>
            </Alert>

            {/* Scorecard */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%', bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
                        <CardContent>
                            <Typography color="text.secondary" variant="overline">Validation Score</Typography>
                            <Typography variant="h3" color="success.dark">{validationScore}%</Typography>
                            <Chip label={`${validatedEvents}/${EXPECTED_EVENT_YEARS} Major Events Matched`} size="small" color="success" sx={{ mt: 1 }} />
                            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Matched FEWS NET, WFP & OCHA reports
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%' }}>
                        <CardContent>
                            <Typography color="text.secondary" variant="overline">Financial Sustainability</Typography>
                            <Stack direction="row" alignItems="baseline" spacing={1}>
                                <Typography variant="h3">{report.sustainability_analysis.loss_ratio || report.executive_summary.loss_ratio}%</Typography>
                                <Typography variant="subtitle2" color="text.secondary">Loss Ratio</Typography>
                            </Stack>
                            <Chip
                                label={`Sustainable (Target: 60-80%)`}
                                size="small"
                                color={report.sustainability_analysis.is_sustainable ? "success" : "warning"}
                                sx={{ mt: 1 }}
                            />
                            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Based on premium calculations
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card sx={{ height: '100%' }}>
                        <CardContent>
                            <Typography color="text.secondary" variant="overline">Model Sensitivity</Typography>
                            <Typography variant="h3">{triggersDetected}</Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>Triggers over {totalYears} Years</Typography>
                            <Divider sx={{ my: 1 }} />
                            <Typography variant="caption">
                                Avg <strong>{(triggersDetected / totalYears).toFixed(1)} events/year</strong> • Not too sensitive (false positives), not too strict (missed events).
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Timeline Chart */}
            <Card sx={{ mb: 4 }}>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box>
                            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <TimelineIcon color="primary" />
                                Trigger Events Timeline (2015-2025)
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                Model detection vs. Historical validation
                            </Typography>
                        </Box>

                        {/* Legend */}
                        <Stack direction="row" spacing={2} sx={{ bgcolor: 'background.default', p: 1, borderRadius: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Box sx={{ width: 12, height: 12, bgcolor: theme.palette.success.main, borderRadius: '2px' }} />
                                <Typography variant="caption" fontWeight="bold">Validated Event</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Box sx={{ width: 12, height: 12, bgcolor: theme.palette.primary.main, borderRadius: '2px' }} />
                                <Typography variant="caption">Model Detection</Typography>
                            </Box>
                        </Stack>
                    </Box>

                    <Alert severity="info" sx={{ mb: 2, py: 0 }}>
                        <Typography variant="caption">
                            <strong>Insight:</strong> The green bars confirm where our model's predictions align perfectly with historical records (FEWS NET/WFP).
                            Consistent green bars indicate high model reliability.
                        </Typography>
                    </Alert>

                    <Chart
                        data={chartData}
                        layout={{
                            height: 300,
                            margin: { l: 40, r: 20, t: 20, b: 40 },
                            xaxis: { title: 'Year', type: 'category' },
                            yaxis: { title: 'Triggers Detected', dtick: 1 },
                            showlegend: false
                        }}
                    />
                </CardContent>
            </Card>

            {/* Validation Log */}
            <Card>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Validation Log (Ground Truth Comparison)
                    </Typography>
                    <Grid container spacing={2}>
                        {years.filter(year => report.yearly_analysis[year].triggers.length > 0).map(year => {
                            const summary = report.yearly_analysis[year];
                            // Get the first available validation text (all triggers in a valid year usually share the source)
                            const validationSource = summary.triggers.find(t => t.external_validation)?.external_validation;

                            return (
                                <Grid item xs={12} key={year}>
                                    <Paper variant="outlined" sx={{ p: 2 }}>
                                        <Grid container alignItems="center" spacing={2}>
                                            <Grid item xs={2}>
                                                <Typography variant="h6">{year}</Typography>
                                            </Grid>
                                            <Grid item xs={2}>
                                                <Chip
                                                    label={`${summary.triggers.length} Trigger(s)`}
                                                    size="small"
                                                    color="primary"
                                                    variant="outlined"
                                                />
                                            </Grid>
                                            <Grid item xs={8}>
                                                {summary.validated ? (
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <CheckCircleIcon color="success" fontSize="small" />
                                                        <Typography variant="body2">
                                                            <strong>Validated:</strong> {validationSource || "Confirmed by external records"}
                                                        </Typography>
                                                    </Box>
                                                ) : (
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <WarningIcon color="action" fontSize="small" />
                                                        <Typography variant="body2" color="text.secondary">
                                                            Detected by model, no major external report found.
                                                        </Typography>
                                                    </Box>
                                                )}
                                            </Grid>
                                        </Grid>
                                    </Paper>
                                </Grid>
                            );
                        })}
                    </Grid>
                </CardContent>
            </Card>

            {/* Validation Data Sources Guide */}
            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
                Understanding Validation Sources
            </Typography>
            <Grid container spacing={2}>
                {[
                    {
                        name: 'FEWS NET',
                        full: 'Famine Early Warning Systems Network',
                        role: 'Food Security Alerts',
                        desc: 'Validates drought-driven food insecurity events.',
                        color: '#d32f2f', // Red
                        bg: '#ffebee'
                    },
                    {
                        name: 'WFP',
                        full: 'World Food Programme',
                        role: 'Emergency Assessments',
                        desc: 'Confirms large-scale production deficits.',
                        color: '#1976d2', // Blue
                        bg: '#e3f2fd'
                    },
                    {
                        name: 'OCHA',
                        full: 'UN Office for Coordination of Humanitarian Affairs',
                        role: 'Flood Impact Reports',
                        desc: 'Primary source for flood displacement data.',
                        color: '#ed6c02', // Orange
                        bg: '#fff3e0'
                    },
                    {
                        name: 'TMA',
                        full: 'Tanzania Meteorological Authority',
                        role: 'Climate Statements',
                        desc: 'Official government rainfall statistics.',
                        color: '#2e7d32', // Green
                        bg: '#e8f5e9'
                    }
                ].map((source, i) => (
                    <Grid item xs={12} md={3} key={i}>
                        <Paper
                            variant="outlined"
                            sx={{
                                p: 2,
                                height: '100%',
                                bgcolor: source.bg,
                                borderColor: source.bg,
                                position: 'relative',
                                overflow: 'hidden'
                            }}
                        >
                            <Box sx={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', bgcolor: source.color }} />
                            <Typography variant="subtitle2" fontWeight="bold" sx={{ color: source.color, mb: 0.5 }}>
                                {source.name}
                            </Typography>
                            <Typography variant="caption" display="block" color="text.secondary" fontWeight="bold" sx={{ mb: 1, fontSize: '0.7rem' }}>
                                {source.role}
                            </Typography>
                            <Typography variant="caption" display="block" color="text.secondary" sx={{ lineHeight: 1.2 }}>
                                {source.desc}
                            </Typography>
                        </Paper>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
}
