import React, { useMemo, useState, useEffect, useRef } from 'react';
import { MapContainer, GeoJSON } from 'react-leaflet';
import { Card, Typography, Box, IconButton, Slider, ToggleButton, ToggleButtonGroup, Paper, Button, GlobalStyles, Alert } from '@mui/material';
import { PlayArrow, Pause, Replay, AttachMoney, Warning, ShowChart } from '@mui/icons-material';
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

// TRIGGER SEVERITY PALETTE
const TRIGGER_SCALE = {
    safe: '#4caf50',     // Green
    warning: '#ff9800',  // Orange
    critical: '#f44336'  // Red
};

// Heatmap logic for different metric types
// Heatmap logic for different metric types
const getMetricColor = (value: number, type: 'payout' | 'frequency' | 'severity' | 'trigger'): string => {
    if (value === 0 && type !== 'trigger') return '#E0E0E0'; // No Data

    if (type === 'trigger') {
        // Value represents deviation severity: 1=Safe, 2=Warning, 3=Critical
        if (value === 3) return TRIGGER_SCALE.critical;
        if (value === 2) return TRIGGER_SCALE.warning;
        return TRIGGER_SCALE.safe; // value 1 or 0
    }

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


interface LocationRiskData {
    locationId: number
    locationName: string
    latitude: number
    longitude: number
    droughtProbability: number
    floodProbability: number
    cropFailureProbability: number
    overallRiskIndex: number
    riskLevel: string
    estimatedPayout?: number // Added for map visualization
}

interface GeographicMapProps {
    mode?: 'historical' | 'forecast' | 'trigger'
    events?: TriggerEvent[]
    locations?: LocationRiskData[]
    triggers?: any[]
    onLocationClick?: (locationId: number) => void
    showLegend?: boolean
}

const GeographicMap: React.FC<GeographicMapProps> = ({
    mode = 'historical',
    events = [],
    locations = [],
    triggers = [],
    onLocationClick: _onLocationClick,
    showLegend: _showLegend = false
}) => {
    // State for Animation and Layers
    const [isPlaying, setIsPlaying] = useState(false);
    const [sliderValue, setSliderValue] = useState(0); // Index of the current date slice
    // Default to 'payout' always (now that we found the missing data)
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

    const handleSliderChange = (_event: Event, newValue: number | number[]) => {
        setSliderValue(newValue as number);
        setIsPlaying(false); // Pause on manual scrub
    };

    const handleLayerChange = (_event: React.MouseEvent<HTMLElement>, newLayer: 'payout' | 'frequency' | 'severity' | null) => {
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

    // 4. Enrich GeoJSON with Filtered Data (Historical or Forecast mode)
    const enrichedRegions = useMemo(() => {
        // TRIGGER MODE: Use active trigger alerts
        if (mode === 'trigger' && triggers.length > 0) {
            const regionStats: { [key: string]: any } = {};
            const normalize = (name: string) => name?.toLowerCase().replace(' region', '').trim();

            triggers.forEach(t => {
                if (!t.location_name) return;
                const regionName = normalize(t.location_name);

                // Determine severity
                let status = 'safe';
                let severityVal = 1;

                if (t.alert_type.includes('CRITICAL') || t.alert_type.includes('DEFICIT')) {
                    status = 'critical';
                    severityVal = 3;
                } else if (t.deviation !== 0) {
                    status = 'warning';
                    severityVal = 2;
                }

                // Store highest severity for the region
                if (!regionStats[regionName] || severityVal > regionStats[regionName].val) {
                    regionStats[regionName] = {
                        val: severityVal,
                        status: status,
                        deviation: t.deviation,
                        threshold: t.threshold_value,
                        type: t.alert_type
                    };
                }
            });

            return {
                ...tanzaniaRegions,
                type: 'FeatureCollection' as const,
                features: tanzaniaRegions.features.map(feature => {
                    const regionName = normalize(feature.properties.shapeName || (feature.properties as any).name || (feature.properties as any).Name || "");
                    const stats = regionStats[regionName];

                    return {
                        ...feature,
                        properties: {
                            ...feature.properties,
                            triggerSeverity: stats ? stats.val : 0, // 0 = no trigger
                            triggerStatus: stats ? stats.status : 'safe',
                            triggerDeviation: stats ? stats.deviation : 0,
                            triggerThreshold: stats ? stats.threshold : 0,
                            triggerType: stats ? stats.type : null,
                            // Zero out other metrics to prevent bleed
                            totalPayout: 0,
                            triggerCount: 0,
                            avgSeverity: 0,
                            counts: { drought: 0, flood: 0, crop_failure: 0 }
                        }
                    };
                })
            };
        }

        // FORECAST MODE: Use location risk probabilities
        if (mode === 'forecast' && locations.length > 0) {
            console.log('GeographicMap: Processing forecast locations:', locations);
            console.log('GeographicMap: Location names from API:', locations.map(l => l.locationName)); // DEBUG: show actual names // DEBUG
            // Map city names to GeoJSON region names
            // API returns city names, but GeoJSON uses administrative region names
            const cityToRegionMap: { [key: string]: string } = {
                'Arusha': 'Arusha',  // City is in Arusha region
                'Dar es Salaam': 'Dar-es-Salaam',  // Match GeoJSON format used in some datasets
                // Handle various potential backend spellings for Dar
                'Dar': 'Dar-es-Salaam',
                'DaresSalaam': 'Dar-es-Salaam',
                'Dodoma': 'Dodoma',  // City is in Dodoma region
                'Mbeya': 'Mbeya',    // City is in Mbeya region
                'Mwanza': 'Mwanza',  // City is in Mwanza region
                'Morogoro': 'Morogoro',  // City is in Morogoro region
                'Kagera': 'Kagera',
                'Kilimanjaro': 'Kilimanjaro',
                'Zanzibar': 'Kaskazini Unguja' // Best guess if Zanzibar comes up, though unlikely
            };

            // Normalize helper - handles null/undefined
            const normalize = (str: string | undefined | null): string => {
                if (!str) return '';
                return str.toLowerCase().replace(/[^a-z0-9]/g, '');
            };

            const locationsByRegion = new Map<string, LocationRiskData>();

            locations.forEach(loc => {
                if (!loc.locationName) return; // Skip if no location name

                const normalizedName = normalize(loc.locationName);
                if (normalizedName) {
                    locationsByRegion.set(normalizedName, loc);
                }

                // Also map mapped names if any
                const mapped = cityToRegionMap[loc.locationName];
                if (mapped) {
                    const normalizedMapped = normalize(mapped);
                    if (normalizedMapped) {
                        locationsByRegion.set(normalizedMapped, loc);
                    }
                }
            });

            return {
                ...tanzaniaRegions,
                type: 'FeatureCollection' as const,
                features: tanzaniaRegions.features.map(feature => {
                    const regionNameRaw = feature.properties.shapeName || (feature.properties as any).name || (feature.properties as any).Name || "";
                    const regionName = normalize(regionNameRaw);

                    // Try exact match on normalized names
                    let locationData = locationsByRegion.get(regionName);

                    // Fallback: Partial match (if one contains the other)
                    if (!locationData) {
                        for (const [key, val] of locationsByRegion.entries()) {
                            if (regionName.includes(key) || key.includes(regionName)) {
                                locationData = val;
                                break;
                            }
                        }
                    }

                    if (locationData) {
                        console.log(`GeographicMap: Matched region: ${regionNameRaw}`, locationData); // DEBUG
                        return {
                            ...feature,
                            properties: {
                                ...feature.properties,
                                avgSeverity: locationData.overallRiskIndex, // Use overall risk as severity
                                counts: {
                                    drought: Math.round(locationData.droughtProbability * 100),
                                    flood: Math.round(locationData.floodProbability * 100),
                                    crop_failure: Math.round(locationData.cropFailureProbability * 100)
                                },
                                locationId: locationData.locationId,
                                totalPayout: locationData.estimatedPayout || 0,
                                triggerCount: Math.round((locationData.overallRiskIndex || 0) * 50) // Scale risk (0-1) to freq range (0-50)
                            }
                        };
                    } else {
                        // console.log(`GeographicMap: No match for region: ${regionName}`); // Optional DEBUG
                    }

                    // No data for this region
                    return {
                        ...feature,
                        properties: {
                            ...feature.properties,
                            totalPayout: 0,
                            triggerCount: 0,
                            avgSeverity: 0,
                            counts: { drought: 0, flood: 0, crop_failure: 0 }
                        }
                    };
                })
            };
        }

        // HISTORICAL MODE: Use filtered events (existing logic)
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
    }, [filteredEvents, mode, locations, triggers]);

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

    // 6. Tooltip and Click Function
    const onEachRegion = (feature: any, layer: L.Layer) => {
        const props = feature.properties;
        const totalPayout = props.totalPayout || 0;
        const triggerCount = props.triggerCount || 0;
        const maxSeverity = (props.avgSeverity * 100).toFixed(1);
        const c = props.counts || { drought: 0, flood: 0, crop_failure: 0 };

        // Disable click interaction (map is locked)
        // Interactive must be true for tooltips to work
        if (layer instanceof L.Path) {
            layer.options.interactive = true;
        }

        // Determine main metric based on Active Layer
        let metricRow = '';
        if (props.triggerSeverity > 0) { // Trigger Mode Check
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>⚠️ Status:</span>
                    <strong style="color: ${props.triggerStatus === 'critical' ? '#d32f2f' : '#ed6c02'}">${props.triggerStatus?.toUpperCase()}</strong>
                </div>
                 <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>📉 Deviation:</span>
                    <strong>${props.triggerDeviation?.toFixed(1) || 0}mm</strong>
                </div>`;
        } else if (activeLayer === 'payout') {
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>💰 ${mode === 'forecast' ? 'Est. Payout' : 'Payout'}:</span>
                    <strong>$${totalPayout.toLocaleString()}</strong>
                </div>`;
        } else if (activeLayer === 'frequency') {
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>📊 ${mode === 'forecast' ? 'Risk Index' : 'Event Count'}:</span>
                    <strong>${mode === 'forecast' ? (props.avgSeverity * 100).toFixed(0) + '%' : triggerCount}</strong>
                </div>`;
        } else { // severity
            metricRow = `
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span>⚠️ ${mode === 'forecast' ? 'Overall Risk' : 'Peak Severity'}:</span>
                    <strong>${maxSeverity}%</strong>
                </div>`;
        }

        const breakdownLabels = mode === 'forecast'
            ? ['Drought Prob', 'Flood Prob', 'Crop Failure Prob']
            : ['Drought', 'Flood', 'Crop'];

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

                    <div style="display: grid; grid-template-columns: 1fr; gap: 4px; font-size: 11px; color: #555;">
                         <div style="display: flex; justify-content: space-between;">
                            <span style="display: flex; align-items: center; gap: 4px;"><span style="color: #D2691E;">●</span> ${breakdownLabels[0]}:</span> 
                            <strong>${mode === 'forecast' ? c.drought + '%' : c.drought}</strong>
                         </div>
                         <div style="display: flex; justify-content: space-between;">
                            <span style="display: flex; align-items: center; gap: 4px;"><span style="color: #2196F3;">●</span> ${breakdownLabels[1]}:</span> 
                            <strong>${mode === 'forecast' ? c.flood + '%' : c.flood}</strong>
                         </div>
                         <div style="display: flex; justify-content: space-between;">
                            <span style="display: flex; align-items: center; gap: 4px;"><span style="color: #FF9800;">●</span> ${breakdownLabels[2]}:</span> 
                            <strong>${mode === 'forecast' ? c.crop_failure + '%' : c.crop_failure}</strong>
                         </div>
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
            {/* Add temporal context for forecast mode */}
            {mode === 'forecast' && (
                <Box sx={{ px: 0, pt: 0, pb: 0 }}>
                    <Alert severity="info" sx={{ mb: 1, py: 0.5 }}>
                        <Typography variant="body2">
                            <strong>{activeLayer === 'payout' ? 'Financial Impact:' : 'Risk Probability:'}</strong>
                            {activeLayer === 'payout'
                                ? ' Color intensity shows estimated insurance payouts. Darker regions = higher financial exposure.'
                                : ' Color intensity shows predicted risk levels. Darker regions = higher probability of trigger events.'}
                        </Typography>
                    </Alert>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        📅 <strong>Forecast Period:</strong> Next 6 months ({new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} - {new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })})
                    </Typography>
                </Box>
            )}
            {/* MAP CONTAINER */}
            {/* GLOBAL STYLE TO HIDE LEAFLET POPUPS */}
            <GlobalStyles styles={{
                '.leaflet-popup': { display: 'none !important' },
                '.leaflet-popup-pane': { display: 'none !important' },
                '.leaflet-marker-icon': { cursor: 'default !important', outline: 'none !important' },
                '.leaflet-interactive': { cursor: 'default !important', outline: 'none !important' },
                'path.leaflet-interactive:focus': { outline: 'none !important' } // Specifically target focus state
            }} />

            {/* MAP CONTAINER */}
            <Box sx={{ flexGrow: 1, position: 'relative', zIndex: 1 }}>
                <MapContainer
                    center={TZ_CENTER}
                    zoom={DEFAULT_ZOOM}
                    scrollWheelZoom={false}
                    doubleClickZoom={false}
                    dragging={false}
                    touchZoom={false}
                    keyboard={false}
                    zoomSnap={0}
                    zoomDelta={0}
                    trackResize={false}
                    boxZoom={false}
                    minZoom={DEFAULT_ZOOM}
                    maxZoom={DEFAULT_ZOOM}
                    style={{ height: '600px', width: '100%', backgroundColor: '#B8D5E5' }}
                    zoomControl={false}
                >
                    <GeoJSON
                        key={`geo - ${activeLayer} -${sliderValue} `} // Force re-render on state change
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
                        <ToggleButton value="frequency" aria-label="frequency" title={mode === 'forecast' ? 'Risk Probability (%)' : 'Event Frequency (Count)'}>
                            <ShowChart fontSize="small" color={activeLayer === 'frequency' ? 'primary' : 'inherit'} />
                        </ToggleButton>
                        {/* Hide severity toggle for forecasts - redundant with frequency */}
                        {mode === 'historical' && (
                            <ToggleButton value="severity" aria-label="severity" title="Peak Severity (%)">
                                <Warning fontSize="small" color={activeLayer === 'severity' ? 'primary' : 'inherit'} />
                            </ToggleButton>
                        )}
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
                        {activeLayer === 'payout' ? (mode === 'forecast' ? 'Est. Payout' : 'Cumulative Payout') :
                            activeLayer === 'frequency' ? (mode === 'forecast' ? 'Risk Index' : 'Event Frequency') :
                                (mode === 'forecast' ? 'Overall Risk %' : 'Peak Severity')}
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
                                // Frequency scale differs between historical and forecast
                                if (mode === 'forecast') {
                                    // For forecasts: Risk Probability percentages
                                    return [
                                        { color: CHOROPLETH_SCALE.low, label: '< 20% Risk' },
                                        { color: CHOROPLETH_SCALE.medLow, label: '20% - 40%' },
                                        { color: CHOROPLETH_SCALE.med, label: '40% - 60%' },
                                        { color: CHOROPLETH_SCALE.medHigh, label: '60% - 80%' },
                                        { color: CHOROPLETH_SCALE.high, label: '> 80% Risk' }
                                    ];
                                } else {
                                    // For historical: Event counts
                                    return [
                                        { color: CHOROPLETH_SCALE.low, label: '≤ 5 Events' },
                                        { color: CHOROPLETH_SCALE.medLow, label: '6 - 15 Events' },
                                        { color: CHOROPLETH_SCALE.med, label: '16 - 30 Events' },
                                        { color: CHOROPLETH_SCALE.medHigh, label: '31 - 50 Events' },
                                        { color: CHOROPLETH_SCALE.high, label: '> 50 Events' }
                                    ];
                                }
                            } else if (mode === 'trigger') {
                                // Trigger Status Legend
                                return [
                                    { color: TRIGGER_SCALE.safe, label: 'Normal' },
                                    { color: TRIGGER_SCALE.warning, label: 'Warning' },
                                    { color: TRIGGER_SCALE.critical, label: 'Trigger Met' }
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

            {/* ANIMATION CONTROLS (Bottom Panel) - Only for historical mode */}
            {mode === 'historical' && (
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
            )}
        </Card >
    );
};

export default GeographicMap;
// force reload
