import React from 'react';
import Plot from 'react-plotly.js';
import { useTheme } from '@mui/material/styles';

interface GaugeChartProps {
    value: number;
    threshold: number;
    title: string;
    min?: number;
    max?: number;
    units?: string;
}

const GaugeChart: React.FC<GaugeChartProps> = ({
    value,
    threshold,
    title,
    min = 0,
    max = 100,
    units = 'mm'
}) => {
    const theme = useTheme();

    // Determine color based on threshold (assuming lower is worse for now, logic can be flipped)
    // For drought: Value < Threshold is BAD (Red)
    // But let's make it generic: deviation is passed usually?
    // Let's assume standard gauge: 
    // Red zone = Critical (below threshold for deficit, above for excess)
    // For now, let's just show the value relative to the threshold marker.

    return (
        <Plot
            data={[
                {
                    type: "indicator",
                    mode: "gauge+number+delta",
                    value: value,
                    title: { text: title, font: { size: 14 } },
                    delta: { reference: threshold, increasing: { color: "green" } },
                    gauge: {
                        axis: { range: [min, max], tickwidth: 1, tickcolor: "darkblue" },
                        bar: { color: value < threshold ? "#d32f2f" : "#2e7d32" }, // Red if below threshold (Drought assumption)
                        bgcolor: "white",
                        borderwidth: 2,
                        bordercolor: "gray",
                        steps: [
                            { range: [min, threshold], color: "rgba(255, 0, 0, 0.1)" }, // Danger zone visualization
                            { range: [threshold, max], color: "rgba(0, 128, 0, 0.1)" }
                        ],
                        threshold: {
                            line: { color: "red", width: 4 },
                            thickness: 0.75,
                            value: threshold
                        }
                    }
                }
            ]}
            layout={{
                width: 250,
                height: 200,
                margin: { t: 25, b: 25, l: 25, r: 25 },
                paper_bgcolor: "rgba(0,0,0,0)",
                font: { family: theme.typography.fontFamily }
            }}
            config={{ displayModeBar: false, staticPlot: true }}
        />
    );
};

export default GaugeChart;
