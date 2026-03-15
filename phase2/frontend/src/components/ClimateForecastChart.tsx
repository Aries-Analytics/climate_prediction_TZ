import { useMemo } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { Box, Typography } from '@mui/material';
import { format, parseISO } from 'date-fns';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface ForecastData {
    targetDate: string;
    triggerType: string;
    expectedDeficit?: number;
    probability: number;
}

interface Props {
    forecasts: ForecastData[];
    title?: string;
}

export default function ClimateForecastChart({ forecasts }: Props) {

    // Transform forecast data to monthly deficit visualization
    const chartData = useMemo(() => {
        if (!forecasts || forecasts.length === 0) {
            return { labels: [], datasets: [] };
        }

        // Group by month and aggregate drought forecasts
        const byMonth = forecasts
            .filter(f => f.triggerType === 'drought')
            .reduce((acc, f) => {
                const monthKey = format(parseISO(f.targetDate), 'MMM yyyy');
                if (!acc[monthKey] || f.probability > acc[monthKey].probability) {
                    acc[monthKey] = f;
                }
                return acc;
            }, {} as Record<string, ForecastData>);

        const sortedMonths = Object.keys(byMonth).sort((a, b) =>
            new Date(parseISO(byMonth[a].targetDate)).getTime() -
            new Date(parseISO(byMonth[b].targetDate)).getTime()
        );

        const deficitValues = sortedMonths.map(month => byMonth[month].expectedDeficit || 0);
        const probabilities = sortedMonths.map(month => byMonth[month].probability * 100);

        return {
            labels: sortedMonths,
            datasets: [
                {
                    label: 'Expected Rainfall Deficit (mm)',
                    data: deficitValues,
                    backgroundColor: deficitValues.map(val =>
                        val > 50 ? 'rgba(211, 47, 47, 0.7)' :  // Critical (red)
                            val > 30 ? 'rgba(237, 108, 2, 0.7)' :  // High (orange)
                                'rgba(255, 193, 7, 0.7)'                // Medium (yellow)
                    ),
                    borderColor: deficitValues.map(val =>
                        val > 50 ? 'rgb(211, 47, 47)' :
                            val > 30 ? 'rgb(237, 108, 2)' :
                                'rgb(255, 193, 7)'
                    ),
                    borderWidth: 2,
                },
                {
                    label: 'Drought Probability (%)',
                    data: probabilities,
                    type: 'line' as const,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 3,
                    tension: 0.3,
                    yAxisID: 'y1',
                }
            ]
        };
    }, [forecasts]);

    if (!forecasts || forecasts.length === 0) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
                <Typography color="text.secondary">No drought forecast data available</Typography>
            </Box>
        );
    }

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    afterLabel: (context: any) => {
                        if (context.dataset.label === 'Expected Rainfall Deficit (mm)') {
                            const value = context.parsed.y;
                            if (value > 50) return '⚠️ CRITICAL DEFICIT';
                            if (value > 30) return '⚠️ HIGH DEFICIT';
                            return 'Moderate Deficit';
                        }
                        return '';
                    }
                }
            }
        },
        scales: {
            y: {
                type: 'linear' as const,
                display: true,
                position: 'left' as const,
                title: {
                    display: true,
                    text: 'Rainfall Deficit (mm below normal)'
                },
                beginAtZero: true,
            },
            y1: {
                type: 'linear' as const,
                display: true,
                position: 'right' as const,
                title: {
                    display: true,
                    text: 'Drought Probability (%)'
                },
                min: 0,
                max: 100,
                grid: {
                    drawOnChartArea: false,
                },
            }
        },
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
    };

    return (
        <Box sx={{ height: '400px', width: '100%' }}>
            <Bar options={options} data={chartData as any} />
        </Box>
    );
}
