import { useMemo } from 'react'
import { Card, CardContent, Typography, Box } from '@mui/material'
import Chart from './charts/Chart'

interface FinancialProjection {
    month: string
    monthName: string
    droughtPayout: number
    floodPayout: number
    cropPayout: number
    total: number
    cumulative: number
}

interface HighestRiskForecast {
    targetDate: string
    triggerType: string
    probability: number
    expectedDeficit?: number
}

interface FinancialForecastChartProps {
    projections: FinancialProjection[]
    totalExposure: number
    reserves: number
    loading?: boolean
    highestRiskForecast?: HighestRiskForecast
}

export default function FinancialForecastChart({
    projections,
    totalExposure,
    reserves,
    loading,
    highestRiskForecast
}: FinancialForecastChartProps) {

    // ===== PAYOUT CALCULATION MODEL =====
    // Model: Per-Farmer Fixed Payout (Parametric Insurance Standard)
    // Source: MOROGORO_RICE_PILOT_SPECIFICATION.md (lines 46-52)
    // 
    // Formula: Affected Farmers × Rate per Trigger
    //   - Affected Farmers = Total Farmers × Probability
    //   - Rate per Trigger = Fixed amount per farmer (documented)
    //
    // Example (52.6% drought):
    //   - Affected: 1,000 × 0.526 = 526 farmers
    //   - Rate: $60 per farmer (drought)
    //   - Payout: 526 × $60 = $31,560
    //
    // Rationale:
    //   - Aligns with ACRE Africa, Jubilee Insurance Tanzania models
    //   - TIRA compliant (transparent, fixed rates)
    //   - Simple for farmers to understand

    const PAYOUT_RATES = {
        drought: 60,
        flood: 75,
        crop_failure: 90
    };

    const PILOT_FARMERS = 1000; // Kilombero Basin pilot total (Ifakara TC 400 + Mlimba DC 600)

    const getTriggerLabel = (triggerType: string) => {
        const labels: Record<string, string> = {
            drought: 'Drought Risk',
            flood: 'Flood Risk',
            crop_failure: 'Crop Failure Risk'
        };
        return labels[triggerType] || triggerType;
    };

    const calculateExpectedPayout = (triggerType: string, probability: number): number => {
        const affectedFarmers = PILOT_FARMERS * probability;
        const payoutPerFarmer = PAYOUT_RATES[triggerType as keyof typeof PAYOUT_RATES] || 0;
        return Math.round(affectedFarmers * payoutPerFarmer);
    };

    const chartData = useMemo(() => {
        if (!projections || projections.length === 0) return null

        return {
            data: [
                {
                    x: projections.map(p => p.monthName),
                    y: projections.map(p => p.droughtPayout),
                    name: 'Drought',
                    type: 'bar',
                    marker: { color: '#ef4444' } // Red for drought (critical)
                },
                {
                    x: projections.map(p => p.monthName),
                    y: projections.map(p => p.floodPayout),
                    name: 'Flood',
                    type: 'bar',
                    marker: { color: '#2196f3' }
                },
                {
                    x: projections.map(p => p.monthName),
                    y: projections.map(p => p.cropPayout),
                    name: 'Crop Failure',
                    type: 'bar',
                    marker: { color: '#f97316' } // Orange for crop failure (high severity)
                },
                {
                    x: projections.map(p => p.monthName),
                    y: projections.map(p => p.cumulative),
                    name: 'Cumulative Total',
                    type: 'scatter',
                    mode: 'lines+markers',
                    yaxis: 'y2',
                    line: { color: '#9c27b0', width: 3 },
                    marker: { size: 8 }
                }
            ],
            layout: {
                barmode: 'stack',
                autosize: true,
                margin: { t: 60, b: 80, l: 80, r: 80 },  // Increased margins to prevent overlap
                xaxis: {
                    title: 'Month',
                    showgrid: false
                },
                yaxis: {
                    title: 'Monthly Payout (USD)',
                    showgrid: true,
                    gridcolor: '#e0e0e0',
                    tickprefix: '$'
                },
                yaxis2: {
                    title: 'Cumulative Total (USD)',
                    overlaying: 'y',
                    side: 'right',
                    showgrid: false,
                    tickprefix: '$'
                },
                hovermode: 'x unified',
                legend: {
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: 1.05,  // Moved legend above chart
                    xanchor: 'center',
                    x: 0.5
                },
                shapes: reserves ? [{
                    type: 'line',
                    yref: 'y2',
                    y0: reserves,
                    y1: reserves,
                    xref: 'paper',
                    x0: 0,
                    x1: 1,
                    line: {
                        color: '#4caf50',
                        width: 2,
                        dash: 'dash'
                    }
                }] : [],
                annotations: reserves ? [{
                    yref: 'y2',
                    y: reserves,
                    xref: 'paper',
                    x: 0.98,
                    text: `Reserves: $${reserves.toLocaleString()}`,
                    showarrow: false,
                    bgcolor: '#4caf50',
                    font: { color: 'white', size: 11 },
                    borderpad: 4
                }] : [],
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Roboto, sans-serif' }
            },
            config: {
                responsive: true,
                displayModeBar: false  // Hide modebar for cleaner look
            }
        }
    }, [projections, reserves])

    if (loading || !chartData) {
        return (
            <Card>
                <CardContent>
                    <Typography variant="body2" color="text.secondary">Loading financial forecast...</Typography>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardContent>
                <Box sx={{ mb: 2, position: 'relative' }}>
                    <Typography variant="body2" color="text.secondary">
                        Expected monthly payouts — primary tier only (horizon ≤ 4mo, ≥75% probability). Advisory tier (5-6mo) is early warning only.
                    </Typography>


                </Box>

                <Chart
                    data={chartData.data}
                    layout={chartData.layout}
                    config={chartData.config}
                />

                {/* Annotation for highest risk month - Below chart for visibility */}
                {highestRiskForecast && (
                    <Box sx={{
                        mt: 2,
                        bgcolor: 'rgba(255,243,224,0.98)',
                        p: 2,
                        borderLeft: '4px solid #d32f2f',
                        borderRadius: 1,
                        boxShadow: 2
                    }}>
                        <Typography variant="caption" fontWeight={700} color="#d32f2f" display="block" gutterBottom>
                            {new Date(highestRiskForecast.targetDate).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}: {getTriggerLabel(highestRiskForecast.triggerType)}
                        </Typography>
                        <Box component="ul" sx={{ m: 0, pl: 2, fontSize: '0.7rem', color: 'text.secondary' }}>
                            <li>{(highestRiskForecast.probability * 100).toFixed(1)}% probability (primary tier ≥75% — payout eligible)</li>
                            {highestRiskForecast.expectedDeficit && (
                                <li>Expected deficit: {Math.abs(highestRiskForecast.expectedDeficit).toFixed(0)}mm</li>
                            )}
                            <li>{Math.round(PILOT_FARMERS * highestRiskForecast.probability).toLocaleString()} farmers affected ({(highestRiskForecast.probability * 100).toFixed(1)}% of {PILOT_FARMERS.toLocaleString()})</li>
                            <li>Est. payout: ${calculateExpectedPayout(highestRiskForecast.triggerType, highestRiskForecast.probability).toLocaleString()} (${PAYOUT_RATES[highestRiskForecast.triggerType as keyof typeof PAYOUT_RATES]}/farmer)</li>
                        </Box>
                    </Box>
                )}

                {/* Summary Box with conditional color */}
                <Box sx={{
                    mt: 2,
                    p: 2,
                    bgcolor: totalExposure > reserves ? '#ffebee' : totalExposure > reserves * 0.8 ? '#fff3e0' : '#e8f5e9',
                    borderRadius: 1,
                    borderLeft: `4px solid ${totalExposure > reserves ? '#f44336' : totalExposure > reserves * 0.8 ? '#ff9800' : '#4caf50'}`
                }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        6-Month Total Exposure: ${totalExposure.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                        Current Reserves: ${reserves.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                        Buffer: {reserves > 0 ? ((reserves - totalExposure) / reserves * 100).toFixed(1) : 0}% remaining
                    </Typography>
                    {totalExposure > reserves && (
                        <Typography variant="caption" sx={{ color: '#d32f2f', fontWeight: 'bold', display: 'block', mt: 1 }}>
                            ⚠️ Warning: Total exposure exceeds current reserves by ${(totalExposure - reserves).toLocaleString()}
                        </Typography>
                    )}
                </Box>
            </CardContent>
        </Card>
    )
}
