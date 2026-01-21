import React from 'react';
import { useTheme } from '@mui/material/styles';

interface SparklineProps {
    data: number[];
    width?: number;
    height?: number;
    color?: string;
}

const Sparkline: React.FC<SparklineProps> = ({
    data,
    width = 100,
    height = 30,
    color
}) => {
    const theme = useTheme();
    const strokeColor = color || theme.palette.primary.main;

    if (!data || data.length < 2) return null;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1; // Avoid division by zero

    // Calculate points
    const points = data.map((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const normalizedVal = (val - min) / range;
        const y = height - (normalizedVal * height); // Invert Y (SVG 0 is top)
        return `${x},${y}`;
    });

    return (
        <svg width={width} height={height} style={{ overflow: 'visible' }}>
            <polyline
                points={points.join(' ')}
                fill="none"
                stroke={strokeColor}
                strokeWidth="2"
            />
            {/* End dot */}
            <circle
                cx={width}
                cy={points[points.length - 1].split(',')[1]}
                r="3"
                fill={strokeColor}
            />
        </svg>
    );
};

export default Sparkline;
