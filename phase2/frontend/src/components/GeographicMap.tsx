import React, { useMemo, useState, useEffect, useRef } from 'react';
import { MapContainer, GeoJSON, Tooltip as LeafletTooltip } from 'react-leaflet';
import { Card, CardContent, Typography, Box, IconButton, Slider, ToggleButton, ToggleButtonGroup, Paper, Button } from '@mui/material';
import { PlayArrow, Pause, Replay, Layers, AttachMoney, Warning, ShowChart } from '@mui/icons-material';
import 'leaflet/dist/leaflet.css';
import { TriggerEvent } from '../types';
import tanzaniaRegions from '../assets/tanzania-regions.json';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const TZ_CENTER: [number, number] = [-6.3690, 34.8888];
const DEFAULT_ZOOM = 6;

// CITY COORDINATES used for data aggregation mapping
const CITY_COORDINATES: { [key: string]: { lat: number, lon: number, name: string } } = {
    'arusha': { lat: -3.3869, lon: 36.6830, name: 'Arusha' },
    'dar': { lat: -6.7924, lon: 39.2083, name: 'Dar es Salaam' },
    'dodoma': { lat: -6.1630, lon: 35.7516, name: 'Dodoma' },
    'mbeya': { lat: -8.9094, lon: 33.4606, name: 'Mbeya' },
    'mwanza': { lat: -2.5164, lon: 32.9175, name: 'Mwanza' },
    'morogoro': { lat: -6.8211, lon: 37.6595, name: 'Morogoro' }
};

const getCityName = (lat: number, lon: number): string => {
    const tolerance = 0.01;
    for (const city of Object.values(CITY_COORDINATES)) {
        if (Math.abs(city.lat - lat) < tolerance && Math.abs(city.lon - lon) < tolerance) {
            return city.name;
        }
    }
    return `${lat.toFixed(2)}, ${lon.toFixed(2)}`;
};

// PROFESSIONAL CHOROPLETH PALETTE (Sequential Gold -> Red -> Brown)
const CHOROPLETH_SCALE = {
    low: '#FEF0D9',      // Very light orange
    medLow: '#FDCC8A',   // Light orange
    med: '#FC8D59',      // Orange
    medHigh: '#E34A33',  // Red-Orange
    high: '#B30000'      // Deep Red-Brown
};

// Heatmap logic for different metric types
const getMetricColor = (value: number, type: 'payout' | 'frequency' | 'severity'): string => {
    if (value === 0) return '#E0E0E0'; // No Data

    if (type === 'payout') {
        if (value < 10000) return CHOROPLETH_SCALE.low;
        if (value < 30000) return CHOROPLETH_SCALE.medLow;
        if (value < 50000) return CHOROPLETH_SCALE.med;
        if (value < 80000) return CHOROPLETH_SCALE.medHigh;
        return CHOROPLETH_SCALE.high;
    } else if (type === 'frequency') {
        // Frequency is CUMULATIVE count over time.
        // Scale needs to handle longer timelines (e.g. 10-20 years).
        if (value <= 5) return CHOROPLETH_SCALE.low;
        if (value <= 15) return CHOROPLETH_SCALE.medLow;
        if (value <= 30) return CHOROPLETH_SCALE.med;
        if (value <= 50) return CHOROPLETH_SCALE.medHigh;
        return CHOROPLETH_SCALE.high;
    } else { // Severity (0-1 range)
        if (value < 0.2) return CHOROPLETH_SCALE.low;
        if (value < 0.35) return CHOROPLETH_SCALE.medLow;
        if (value < 0.5) return CHOROPLETH_SCALE.med;
        if (value < 0.7) return CHOROPLETH_SCALE.medHigh;
        return CHOROPLETH_SCALE.high;
    }
};

interface GeographicMapProps {
    events?: TriggerEvent[];
}

const GeographicMap: React.FC<GeographicMapProps> = ({ events = [] }) => {
    // State for Animation and Layers
    const [isPlaying, setIsPlaying] = useState(false);
    const [sliderValue, setSliderValue] = useState(0); // Index of the current date slice
    const [activeLayer, setActiveLayer] = useState<'payout' | 'frequency' | 'severity'>('payout');
    const [playbackSpeed, setPlaybackSpeed] = useState<1 | 2>(1);

    // Animation Interval Ref
    const animationRef = useRef<NodeJS.Timeout | null>(null);

    // 1. Process Timeline: Extract unique YYYY-MM dates
    const timeline = useMemo(() => {
        if (!events.length) return [];
        const uniqueDates = new Set(events.map(e => {
            const d = new Date(e.date);
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        }));
        return Array.from(uniqueDates).sort();
    }, [events]);

    // Set initial slider to end (latest data) when data loads
    useEffect(() => {
        if (timeline.length > 0) {
            setSliderValue(timeline.length - 1);
        }
    }, [timeline.length]);

    // 2. Animation Loop
    useEffect(() => {
        if (isPlaying) {
            const intervalMs = 800 / playbackSpeed;
            animationRef.current = setInterval(() => {
                setSliderValue((prev) => {
                    if (prev >= timeline.length - 1) {
                        setIsPlaying(false); // Stop at end
                        return prev;
                    }
                    return prev + 1;
                });
            }, intervalMs);
        } else {
            if (animationRef.current) clearInterval(animationRef.current);
        }
        return () => { if (animationRef.current) clearInterval(animationRef.current); };
    }, [isPlaying, timeline.length, playbackSpeed]);

    const handlePlayPause = () => {
        if (sliderValue >= timeline.length - 1) {
            setSliderValue(0); // Restart if at end
        }
        setIsPlaying(!isPlaying);
    };

    const handleSpeedToggle = () => {
        setPlaybackSpeed(prev => prev === 1 ? 2 : 1);
    };

    const handleSliderChange = (event: Event, newValue: number | number[]) => {
        setSliderValue(newValue as number);
        setIsPlaying(false); // Pause on manual scrub
    };

    const handleLayerChange = (event: React.MouseEvent<HTMLElement>, newLayer: 'payout' | 'frequency' | 'severity' | null) => {
        if (newLayer !== null) setActiveLayer(newLayer);
    };

    // 3. Filter Events based on Timeline (Cumulative vs Monthly?)
    // Decision: Monthly snapshot is better for animation, but 'Total Payout' implies cumulative.
    // Let's do CUMULATIVE UP TO DATE for Payout, but SNAPSHOT for Frequency/Severity?
    // Actually, for an "Evolution" movie, showing cumulative growth is powerful for Payout.
    // Let's stick to CUMULATIVE for simplicity and impact.
    const filteredEvents = useMemo(() => {
        if (!timeline.length) return [];
        const cutoffDateStr = timeline[sliderValue];
        // Create simple string comparison for YYYY-MM
        return events.filter(e => {
            const d = new Date(e.date);
            const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            return dateStr <= cutoffDateStr;
        });
    }, [events, timeline, sliderValue]);

    // 4. Enrich GeoJSON with Filtered Data
    const enrichedRegions = useMemo(() => {
        const eventsByRegion = new Map<string, typeof events>();

        filteredEvents.forEach((e) => {
            const latRaw = e.locationLat;
            const lonRaw = e.locationLon;
            const lat = typeof latRaw === 'string' ? parseFloat(latRaw) : latRaw;
            const lon = typeof lonRaw === 'string' ? parseFloat(lonRaw) : lonRaw;

            if (typeof lat === 'number' && !isNaN(lat) &&
                typeof lon === 'number' && !isNaN(lon)) {
                const cityName = getCityName(lat, lon);
                if (cityName) {
                    if (!eventsByRegion.has(cityName)) {
                        eventsByRegion.set(cityName, []);
                    }
                    eventsByRegion.get(cityName)!.push(e);
                }
            }
        });

        return {
            ...tanzaniaRegions,
            type: 'FeatureCollection' as const,
            features: tanzaniaRegions.features.map(feature => {
                const regionName = feature.properties.shapeName;
                const regionEvents = eventsByRegion.get(regionName) || [];

                const totalPayout = regionEvents.reduce((sum, e) => {
                    const payout = typeof e.payoutAmount === 'string' ? parseFloat(e.payoutAmount) : (e.payoutAmount || 0);
                    return sum + (isNaN(payout) ? 0 : payout);
                }, 0);

                const maxSeverity = regionEvents.length > 0
                    ? regionEvents.reduce((max, e) => {
                        const severity = typeof e.severity === 'string' ? parseFloat(e.severity) : (e.severity || 0);
                        const val = isNaN(severity) ? 0 : severity;
                        return val > max ? val : max;
                    }, 0)
                    : 0;

                const counts = { drought: 0, flood: 0, crop_failure: 0 };
                regionEvents.forEach(e => {
                    const type = (e.triggerType || '').toLowerCase().replace(' ', '_');
                    if (type.includes('drought')) counts.drought++;
                    else if (type.includes('flood')) counts.flood++;
                    else counts.crop_failure++;
                });

                return {
                    ...feature,
                    properties: {
                        ...feature.properties,
                        totalPayout,
                        triggerCount: regionEvents.length,
                        avgSeverity: maxSeverity, // Keeping key name 'avgSeverity' for compatibility with rest of code, but logic is MAX
                        counts
                    }
                };
            })
        };
    }, [filteredEvents]);

    // 5. Stylist Function
    const regionStyle = (feature: any) => {
        const props = feature?.properties;
        let metricValue = 0;

        if (activeLayer === 'payout') metricValue = props.totalPayout || 0;
        else if (activeLayer === 'frequency') metricValue = props.triggerCount || 0;
        else if (activeLayer === 'severity') metricValue = props.avgSeverity || 0; // This is now MAX severity

        return {
            fillColor: getMetricColor(metricValue, activeLayer),
            fillOpacity: 0.8,
            color: '#666',
            weight: 1,
            opacity: 1
        };
    };

    // 6. Tooltip Function
    const onEachRegion = (feature: any, layer: L.Layer) => {
        const props = feature.properties;
        const totalPayout = props.totalPayout || 0;
        const triggerCount = props.triggerCount || 0;
        const maxSeverity = (props.avgSeverity * 100).toFixed(1); // avgSeverity is actually MAX
        const c = props.counts || { drought: 0, flood: 0, crop_failure: 0 };

        // Determine main metric based on Active Layer
        let metricRow = '';
        if (activeLayer === 'payout') {
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>💰 Payout:</span>
                    <strong>$${totalPayout.toLocaleString()}</strong>
                </div>`;
        } else if (activeLayer === 'frequency') {
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>📊 Events:</span>
                    <strong>${triggerCount}</strong>
                </div>`;
        } else { // severity
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>⚠️ Peak Sev:</span>
                    <strong>${maxSeverity}%</strong>
                </div>`;
        }

        layer.bindTooltip(`
            <div style="font-family: sans-serif; min-width: 160px;">
                <div style="background: #333; color: white; padding: 6px 10px; border-radius: 4px 4px 0 0; text-align: center;">
                    <strong>${props.shapeName}</strong>
                </div>
                <div style="padding: 10px; border: 1px solid #ccc; border-top: none; background: white; border-radius: 0 0 4px 4px;">
                    
                    <div style="margin-bottom: 8px; color: #333;">
                        ${metricRow}
                    </div>

                    <div style="border-top: 1px solid #eee; margin: 6px 0;"></div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px; color: #555;">
                         <span style="display: flex; align-items: center; gap: 4px;"><span style="color: #D2691E;">●</span> Drought:</span> <strong>${c.drought}</strong>
                        <span style="display: flex; align-items: center; gap: 4px;"><span style="color: #2196F3;">●</span> Flood:</span> <strong>${c.flood}</strong>
                        <span style="display: flex; align-items: center; gap: 4px;"><span style="color: #FF9800;">●</span> Crop:</span> <strong>${c.crop_failure}</strong>
                    </div>
                </div>
            </div>
        `, {
            direction: 'auto',
            permanent: false,
            className: 'region-tooltip-custom',
            opacity: 0.95
        });
    };

    return (
        <Card sx={{ height: '100%', minHeight: 600, display: 'flex', flexDirection: 'column', position: 'relative' }}>
            {/* MAP CONTAINER */}
            <Box sx={{ flexGrow: 1, position: 'relative', zIndex: 1 }}>
                <MapContainer
                    center={TZ_CENTER}
                    zoom={DEFAULT_ZOOM}
                    scrollWheelZoom={false} // DISABLE SCROLL ZOOM
                    doubleClickZoom={false} // DISABLE DOUBLE CLICK ZOOM
                    dragging={true} // Allow panning if needed, or set to false for strictly fixed
                    minZoom={5}
                    maxZoom={7}
                    style={{ height: '100%', width: '100%', backgroundColor: '#B8D5E5' }}
                    // IMPORTANT: 'backgroundColor' fixes the white flash during loading
                    zoomControl={false} // Move zoom control if needed, but default is top-left
                >
                    <GeoJSON
                        key={`geo-${activeLayer}-${sliderValue}`} // Force re-render on state change
                        data={enrichedRegions as any}
                        style={regionStyle}
                        onEachFeature={onEachRegion}
                    />
                </MapContainer>

                {/* OVERLAY CONTROLS (Top Right) - Layer Switcher */}
                <Paper
                    elevation={3}
                    sx={{
                        position: 'absolute',
                        top: 20,
                        right: 20,
                        zIndex: 1000,
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        borderRadius: 2,
                        p: 0.5
                    }}
                >
                    <ToggleButtonGroup
                        value={activeLayer}
                        exclusive
                        onChange={handleLayerChange}
                        orientation="vertical"
                        size="small"
                        aria-label="map layer"
                    >
                        <ToggleButton value="payout" aria-label="payout" title="Financial Impact ($)">
                            <AttachMoney fontSize="small" color={activeLayer === 'payout' ? 'primary' : 'inherit'} />
                        </ToggleButton>
                        <ToggleButton value="frequency" aria-label="frequency" title="Event Frequency (Count)">
                            <ShowChart fontSize="small" color={activeLayer === 'frequency' ? 'primary' : 'inherit'} />
                        </ToggleButton>
                        <ToggleButton value="severity" aria-label="severity" title="Peak Severity (%)">
                            <Warning fontSize="small" color={activeLayer === 'severity' ? 'primary' : 'inherit'} />
                        </ToggleButton>
                    </ToggleButtonGroup>
                </Paper>

                {/* OVERLAY LEGEND (Bottom Right - Above Slider) */}
                <Box sx={{
                    position: 'absolute',
                    bottom: 20, // Adjusted for layout
                    right: 20,
                    zIndex: 1000,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    padding: '10px',
                    borderRadius: '4px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                    minWidth: 150
                }}>
                    <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
                        {activeLayer === 'payout' ? 'Cumulative Payout' :
                            activeLayer === 'frequency' ? 'Event Frequency' : 'Peak Severity'}
                    </Typography>
                    {/* Dynamic Legend Items based on Active Layer */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {/* No Data Entry */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <div style={{ width: 16, height: 12, backgroundColor: '#E0E0E0', border: '1px solid #ccc' }} />
                            <Typography variant="caption">No Data</Typography>
                        </div>

                        {(() => {
                            // Define Legend Items dynamically based on activeLayer
                            // This matches the logic in getMetricColor
                            if (activeLayer === 'payout') {
                                return [
                                    { color: CHOROPLETH_SCALE.low, label: '< $10k' },
                                    { color: CHOROPLETH_SCALE.medLow, label: '$10k - $30k' },
                                    { color: CHOROPLETH_SCALE.med, label: '$30k - $50k' },
                                    { color: CHOROPLETH_SCALE.medHigh, label: '$50k - $80k' },
                                    { color: CHOROPLETH_SCALE.high, label: '> $80k' }
                                ];
                            } else if (activeLayer === 'frequency') {
                                return [
                                    { color: CHOROPLETH_SCALE.low, label: '≤ 5 Events' },
                                    { color: CHOROPLETH_SCALE.medLow, label: '6 - 15 Events' },
                                    { color: CHOROPLETH_SCALE.med, label: '16 - 30 Events' },
                                    { color: CHOROPLETH_SCALE.medHigh, label: '31 - 50 Events' },
                                    { color: CHOROPLETH_SCALE.high, label: '> 50 Events' }
                                ];
                            } else {
                                // Adjusted Severity Scale for Sensitivity
                                return [
                                    { color: CHOROPLETH_SCALE.low, label: '< 20% Sev' },
                                    { color: CHOROPLETH_SCALE.medLow, label: '20% - 35%' },
                                    { color: CHOROPLETH_SCALE.med, label: '35% - 50%' },
                                    { color: CHOROPLETH_SCALE.medHigh, label: '50% - 70%' },
                                    { color: CHOROPLETH_SCALE.high, label: '> 70% Sev' }
                                ];
                            }
                        })().map(item => (
                            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <div style={{ width: 16, height: 12, backgroundColor: item.color, border: '1px solid #ccc' }} />
                                <Typography variant="caption">{item.label}</Typography>
                            </div>
                        ))}
                    </div>
                </Box>
            </Box>

            {/* ANIMATION CONTROLS (Bottom Panel) */}
            <Paper
                elevation={6}
                sx={{
                    p: 2,
                    zIndex: 10,
                    borderTop: '1px solid #e0e0e0',
                    bgcolor: 'background.paper'
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <IconButton onClick={handlePlayPause} color="primary" size="large">
                        {isPlaying ? <Pause /> : (sliderValue >= timeline.length - 1 ? <Replay /> : <PlayArrow />)}
                    </IconButton>

                    <Button
                        variant={playbackSpeed === 2 ? "contained" : "outlined"}
                        size="small"
                        onClick={handleSpeedToggle}
                        sx={{ minWidth: '40px', px: 1, height: 30 }}
                    >
                        {playbackSpeed}x
                    </Button>

                    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, fontWeight: 'bold' }}>
                            TIMELINE: {timeline[sliderValue] || 'Loading...'}
                        </Typography>
                        <Slider
                            value={sliderValue}
                            min={0}
                            max={Math.max(0, timeline.length - 1)}
                            onChange={handleSliderChange}
                            valueLabelDisplay="auto"
                            valueLabelFormat={(idx) => timeline[idx]}
                            disabled={!timeline.length}
                            sx={{
                                '& .MuiSlider-thumb': {
                                    transition: 'left 0.1s', // Smooth transition
                                }
                            }}
                        />
                    </Box>

                    <Box sx={{ minWidth: 100, textAlign: 'right' }}>
                        <Typography variant="body2" color="primary" fontWeight="bold">
                            {activeLayer.toUpperCase()}
                        </Typography>
                    </Box>
                </Box>
            </Paper>
        </Card >
    );
};

export default GeographicMap;
