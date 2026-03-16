import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
  SelectChangeEvent,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import axios from '../config/axiosInstance'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Chart from '../components/charts/Chart'
import { ClimateTimeSeries, Anomaly } from '../types'

const VARIABLES = [
  { value: 'temperature', label: 'Temperature (°C)', tooltip: 'Average monthly temperature' },
  { value: 'rainfall', label: 'Rainfall (mm)', tooltip: 'Total monthly rainfall' },
  { value: 'ndvi', label: 'NDVI', tooltip: 'Normalized Difference Vegetation Index - measures vegetation health (0=no vegetation, 1=dense vegetation)' },
  { value: 'enso', label: 'ENSO Index', tooltip: 'El Niño-Southern Oscillation index - In East Africa: +ve=El Niño (wetter/more rain), -ve=La Niña (drier/less rain)' },
  { value: 'iod', label: 'IOD Index', tooltip: 'Indian Ocean Dipole index - influences East African rainfall (+ve=wetter/more rain/floods, -ve=drier/less rain/droughts)' }
]

export default function ClimateInsightsDashboard() {
  // Data States
  const [timeSeries, setTimeSeries] = useState<ClimateTimeSeries[]>([])
  const [allTimeSeries, setAllTimeSeries] = useState<ClimateTimeSeries[]>([])
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [correlationMatrix, setCorrelationMatrix] = useState<any>(null)

  // UI States
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedVariables, setSelectedVariables] = useState<string[]>(['temperature', 'rainfall', 'ndvi'])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const fetchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Climate Data Effect — debounced so rapid date input changes don't fire multiple requests
  useEffect(() => {
    if (fetchDebounceRef.current) clearTimeout(fetchDebounceRef.current)
    fetchDebounceRef.current = setTimeout(() => {
      fetchClimateData()
    }, 400)
    return () => {
      if (fetchDebounceRef.current) clearTimeout(fetchDebounceRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate])

  const fetchClimateData = async () => {
    // ... existing fetch logic ...
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')

      // Fetch time series for ALL variables (not just selected)
      const allVariables = ['temperature', 'rainfall', 'ndvi', 'enso', 'iod']
      const timeSeriesPromises = allVariables.map(async (variable) => {
        const params = new URLSearchParams()
        if (startDate) params.append('start_date', startDate)
        if (endDate) params.append('end_date', endDate)

        const response = await axios.get(
          `${API_BASE_URL}/climate/timeseries?variable=${variable}&${params}`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        return response.data
      })

      // Run timeseries, anomalies, and correlations all in parallel
      const corrParams = new URLSearchParams()
      allVariables.forEach(v => corrParams.append('variables', v))
      const headers = { Authorization: `Bearer ${token}` }

      const [timeSeriesData, anomalyResponse, corrResponse] = await Promise.all([
        Promise.all(timeSeriesPromises),
        selectedVariables.length > 0
          ? axios.get(`${API_BASE_URL}/climate/anomalies?variable=${selectedVariables[0]}`, { headers }).then(r => r.data).catch(() => [])
          : Promise.resolve([]),
        (!startDate && !endDate)
          ? axios.get(`${API_BASE_URL}/climate/correlations?${corrParams.toString()}`, { headers }).then(r => r.data).catch(() => null)
          : Promise.resolve(null),
      ])

      setAllTimeSeries(timeSeriesData)
      setTimeSeries(timeSeriesData.filter(ts => selectedVariables.includes(ts.variable)))
      setAnomalies(anomalyResponse)
      if (corrResponse) setCorrelationMatrix(corrResponse)

      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch climate data')
    } finally {
      setIsLoading(false)
    }
  }

  // ... (handleVariableChange, useEffect for selectedVariables, handleRelayout) ...
  const handleVariableChange = (event: SelectChangeEvent<typeof selectedVariables>) => {
    const value = event.target.value
    setSelectedVariables(typeof value === 'string' ? value.split(',') : value)
  }

  // Filter displayed data when selectedVariables changes (client-side, instant)
  useEffect(() => {
    if (allTimeSeries.length > 0) {
      setTimeSeries(allTimeSeries.filter(ts => selectedVariables.includes(ts.variable)))
    }
  }, [selectedVariables, allTimeSeries])

  // Handler to capture when user changes the time range via range selector buttons
  const handleRelayout = (_event: any) => {
    // ... existing handler ...
  }


  if (isLoading) {
    return <LoadingSpinner message="Loading climate data..." />
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  // Helper function to convert hex color to RGB for transparency
  const hexToRgb = (hex: string): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result
      ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
      : '0, 0, 0'
  }

  // Prepare time series chart data with median + range bands
  const timeSeriesChartData = timeSeries.flatMap((series) => {
    // ... existing flatMap logic ...
    const varInfo = VARIABLES.find(v => v.value === series.variable)
    const isSecondaryAxis = ['ndvi', 'enso', 'iod'].includes(series.variable)

    // Color map for variables
    const colorMap: Record<string, string> = {
      'temperature': '#ff6b6b',
      'rainfall': '#4dabf7',
      'ndvi': '#51cf66',
      'enso': '#ff6b9d',
      'iod': '#845ef7'
    }

    const dates = series.data.map(d => d.date)
    const medianValues = series.data.map(d => d.median)
    const minValues = series.data.map(d => d.min)
    const maxValues = series.data.map(d => d.max)
    const color = colorMap[series.variable] || '#888888'

    // Base historical traces (Upper, Median, Lower)
    const traces = [
      // Upper bound (invisible line, creates top of shaded area)
      {
        x: dates,
        y: maxValues,
        name: `${varInfo?.label} (Max)`,
        type: 'scatter' as const,
        mode: 'lines' as const,
        line: { width: 0 },
        fillcolor: `rgba(${hexToRgb(color)}, 0.15)`,
        showlegend: false,
        yaxis: isSecondaryAxis ? 'y2' : 'y',
        hoverinfo: 'skip' as const
      },
      // Median line (visible, main line)
      {
        x: dates,
        y: medianValues,
        name: varInfo?.label || series.variable,
        type: 'scatter' as const,
        mode: 'lines' as const,
        yaxis: isSecondaryAxis ? 'y2' : 'y',
        line: {
          width: 2,
          color: color,
          shape: 'spline' as const
        },
        fill: 'tonexty' as const,  // Fill to previous trace (max)
        fillcolor: `rgba(${hexToRgb(color)}, 0.15)`,
        hovertemplate:
          `<b>${varInfo?.label}</b><br>` +
          `Date: %{x}<br>` +
          `Median: %{y:.2f}<br>` +
          (
            ['enso', 'iod'].includes(series.variable)
              ? `Range: N/A (Global Index)`
              : `Range: %{customdata[0]:.2f} - %{customdata[1]:.2f}`
          ) +
          `<extra></extra>`,
        customdata: series.data.map(d => [d.min, d.max])
      },
      // Lower bound (invisible line, creates bottom of shaded area)
      {
        x: dates,
        y: minValues,
        name: `${varInfo?.label} (Min)`,
        type: 'scatter' as const,
        mode: 'lines' as const,
        line: { width: 0 },
        showlegend: false,
        yaxis: isSecondaryAxis ? 'y2' : 'y',
        hoverinfo: 'skip' as const
      }
    ];

    return traces;
  })

  // Forecast traces removed - forecasts now only in Early Warning Dashboard
  const finalChartData: any[] = [...timeSeriesChartData];



  // Prepare anomaly markers
  const anomalyMarkers = anomalies.length > 0 ? {
    // ... existing anomaly logic ...
    x: anomalies.map(a => a.date),
    y: anomalies.map(a => a.value),
    name: 'Anomalies',
    type: 'scatter' as const,
    mode: 'markers' as const,
    marker: {
      color: 'red',
      size: 10,
      symbol: 'x'
    }
  } : null

  if (anomalyMarkers) finalChartData.push(anomalyMarkers);

  // ... (correlationData prep) ...
  const correlationData = correlationMatrix ? [{
    z: correlationMatrix.matrix,
    x: correlationMatrix.variables.map((v: string) => VARIABLES.find(vm => vm.value === v)?.label || v),
    y: correlationMatrix.variables.map((v: string) => VARIABLES.find(vm => vm.value === v)?.label || v),
    type: 'heatmap' as const,
    colorscale: 'RdBu',
    zmid: 0,
    zmin: -1,
    zmax: 1,
    text: correlationMatrix.matrix.map((row: any[]) => row.map((val: any) => val.toFixed(2))),
    texttemplate: '%{text}', // Show values on the heatmap cells
    textfont: { color: 'white' }, // Will contrast well with dark red/blue
    hovertemplate: '<b>%{x}</b> & <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>',
    showscale: true,
    colorbar: {
      title: 'Correlation',
      titleside: 'right'
    }
  }] : []


  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Climate Insights Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analyze historical climate trends, patterns, and correlations.
          </Typography>
        </div>
      </Box>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
          {/* ... existing controls ... */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Selection
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Variables</InputLabel>
                    <Select
                      multiple
                      value={selectedVariables}
                      onChange={handleVariableChange}
                      input={<OutlinedInput label="Variables" />}
                      renderValue={(selected) => {
                        return selected.map(v => VARIABLES.find(varItem => varItem.value === v)?.label).join(', ');
                      }}
                    >
                      {VARIABLES.map((variable) => (
                        <MenuItem key={variable.value} value={variable.value}>
                          <Checkbox checked={selectedVariables.indexOf(variable.value) > -1} />
                          <ListItemText primary={variable.label} />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6} md={4}>
                  <TextField
                    label="Start Date"
                    type="date"
                    fullWidth
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={6} md={4}>
                  <TextField
                    label="End Date"
                    type="date"
                    fullWidth
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Time Series Chart */}
        {finalChartData.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="h6" gutterBottom>Climate Time Series (Historical Data)</Typography>
                </Box>

                <Chart
                  data={finalChartData}
                  layout={{
                    height: 650,
                    xaxis: {
                      title: { text: 'Date', font: { size: 14, family: 'Arial, sans-serif' } },
                      type: 'date',
                      gridcolor: '#e0e0e0',
                      showgrid: true,
                      fixedrange: true,
                      rangeslider: { visible: false }
                    },
                    yaxis: {
                      title: {
                        text: 'Rainfall (mm) / Temperature (°C)',
                        font: { size: 14, family: 'Arial, sans-serif' }
                      },
                      gridcolor: '#e0e0e0',
                      showgrid: true,
                      fixedrange: true,
                      rangemode: 'tozero'
                    },
                    yaxis2: {
                      title: {
                        text: 'NDVI / Climate Indices',
                        font: { size: 14, family: 'Arial, sans-serif' }
                      },
                      overlaying: 'y',
                      side: 'right',
                      showgrid: false,
                      fixedrange: true
                      // Removed rangemode:'tozero' - ENSO/IOD indices can have negative values
                    },
                    hovermode: 'x unified',
                    showlegend: true,
                    legend: {
                      orientation: 'h',
                      yanchor: 'bottom',
                      y: 1.05,
                      xanchor: 'right',
                      x: 1
                    },
                    plot_bgcolor: '#fafafa',
                    paper_bgcolor: 'white',
                    margin: { l: 70, r: 70, t: 100, b: 60 },
                    dragmode: false
                  }}
                  config={{
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                    toImageButtonOptions: {
                      format: 'png',
                      filename: 'climate_timeseries',
                      height: 800,
                      width: 1200
                    }
                  }}
                  onRelayout={handleRelayout}
                />
              </CardContent>
            </Card>
          </Grid >
        )}

        {/* EDA Section - Educational Information */}

        <Grid item xs={12}>
          <Card sx={{ bgcolor: 'info.50' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Typography variant="h6">
                  Understanding Climate Data Sources
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                This section provides educational context about each climate variable and how to interpret the trends above.
              </Typography>

              {/* Temperature */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      🌡️ Temperature (°C)
                    </Typography>
                    <Chip label="NASA POWER" size="small" color="primary" variant="outlined" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" paragraph>
                    <strong>Data Source:</strong> NASA POWER (Prediction Of Worldwide Energy Resources) provides satellite-derived temperature measurements.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>What it measures:</strong> Average monthly temperature in degrees Celsius for Tanzania's agricultural regions.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>Trend Interpretation:</strong>
                  </Typography>
                  <ul style={{ marginTop: 0 }}>
                    <li><Typography variant="body2">Rising temperatures can increase evapotranspiration, leading to water stress for crops</Typography></li>
                    <li><Typography variant="body2">Temperature extremes (very hot or cold) can damage crops and reduce yields</Typography></li>
                    <li><Typography variant="body2">Seasonal patterns show warmer temperatures during dry seasons (June-October)</Typography></li>
                    <li><Typography variant="body2">Long-term warming trends may indicate climate change impacts on agriculture</Typography></li>
                  </ul>
                  <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                    💡 For insurance: Extreme heat events can trigger crop failure claims
                  </Typography>
                </AccordionDetails>
              </Accordion>

              {/* Rainfall */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      🌧️ Rainfall (mm)
                    </Typography>
                    <Chip label="CHIRPS" size="small" color="primary" variant="outlined" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" paragraph>
                    <strong>Data Source:</strong> CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) combines satellite imagery with ground station data.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>What it measures:</strong> Total monthly rainfall in millimeters, crucial for agricultural planning and drought/flood prediction.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>Trend Interpretation:</strong>
                  </Typography>
                  <ul style={{ marginTop: 0 }}>
                    <li><Typography variant="body2">Tanzania has two rainy seasons: "Long rains" (March-May) and "Short rains" (October-December)</Typography></li>
                    <li><Typography variant="body2">Rainfall below 50mm/month during growing season indicates drought risk</Typography></li>
                    <li><Typography variant="body2">Rainfall above 200mm/month can cause flooding and waterlogging</Typography></li>
                    <li><Typography variant="body2">High variability between years indicates climate uncertainty</Typography></li>
                  </ul>
                  <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                    💡 For insurance: Both drought (too little rain) and flood (too much rain) trigger payouts
                  </Typography>
                </AccordionDetails>
              </Accordion>

              {/* NDVI */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      🌿 NDVI (Vegetation Index)
                    </Typography>
                    <Chip label="MODIS Terra" size="small" color="success" variant="outlined" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" paragraph>
                    <strong>Data Source:</strong> MODIS (Moderate Resolution Imaging Spectroradiometer) on NASA's Terra satellite measures vegetation health from space.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>What it measures:</strong> Normalized Difference Vegetation Index (NDVI) ranges from -1 to +1, where higher values indicate healthier, denser vegetation.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>Trend Interpretation:</strong>
                  </Typography>
                  <ul style={{ marginTop: 0 }}>
                    <li><Typography variant="body2">NDVI &gt; 0.6: Dense, healthy vegetation (good crop conditions)</Typography></li>
                    <li><Typography variant="body2">NDVI 0.2-0.6: Moderate vegetation (typical agricultural land)</Typography></li>
                    <li><Typography variant="body2">NDVI &lt; 0.2: Sparse vegetation or bare soil (drought stress or crop failure)</Typography></li>
                    <li><Typography variant="body2">NDVI follows rainfall patterns with a 1-2 month lag (vegetation response time)</Typography></li>
                    <li><Typography variant="body2">Declining NDVI during growing season is an early warning of crop stress</Typography></li>
                  </ul>
                  <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                    💡 For insurance: NDVI is a direct indicator of crop health and potential yield losses
                  </Typography>
                </AccordionDetails>
              </Accordion>

              {/* ENSO */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      🌊 ENSO Index (El Niño-Southern Oscillation)
                    </Typography>
                    <Chip label="NOAA" size="small" color="warning" variant="outlined" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" paragraph>
                    <strong>Data Source:</strong> NOAA (National Oceanic and Atmospheric Administration) monitors sea surface temperatures in the Pacific Ocean.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>What it measures:</strong> The Oceanic Niño Index (ONI) tracks El Niño and La Niña events, which influence global weather patterns.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>Trend Interpretation for East Africa:</strong>
                  </Typography>
                  <ul style={{ marginTop: 0 }}>
                    <li><Typography variant="body2"><strong>Positive values (+0.5 or higher):</strong> El Niño conditions → Typically brings MORE rainfall to East Africa → Increased flood risk</Typography></li>
                    <li><Typography variant="body2"><strong>Negative values (-0.5 or lower):</strong> La Niña conditions → Typically brings LESS rainfall to East Africa → Increased drought risk</Typography></li>
                    <li><Typography variant="body2"><strong>Near zero (-0.5 to +0.5):</strong> Neutral conditions → Normal rainfall patterns</Typography></li>
                    <li><Typography variant="body2">ENSO events typically last 9-12 months and can be predicted 3-6 months in advance</Typography></li>
                    <li><Typography variant="body2">Strong El Niño events (ONI &gt; +1.5) have historically caused severe flooding in Tanzania</Typography></li>
                  </ul>
                  <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                    💡 For insurance: ENSO forecasts help predict seasonal rainfall and trigger probabilities months in advance
                  </Typography>
                </AccordionDetails>
              </Accordion>

              {/* IOD */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      🌊 IOD Index (Indian Ocean Dipole)
                    </Typography>
                    <Chip label="NOAA" size="small" color="warning" variant="outlined" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" paragraph>
                    <strong>Data Source:</strong> NOAA monitors sea surface temperature differences between the western and eastern Indian Ocean.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>What it measures:</strong> The Dipole Mode Index (DMI) tracks temperature differences that drive rainfall patterns in East Africa.
                  </Typography>
                  <Typography variant="body2" paragraph>
                    <strong>Trend Interpretation for East Africa:</strong>
                  </Typography>
                  <ul style={{ marginTop: 0 }}>
                    <li><Typography variant="body2"><strong>Positive IOD (+0.4 or higher):</strong> Warmer water near Africa → MORE rainfall in East Africa → Flood risk during October-December</Typography></li>
                    <li><Typography variant="body2"><strong>Negative IOD (-0.4 or lower):</strong> Cooler water near Africa → LESS rainfall in East Africa → Drought risk during October-December</Typography></li>
                    <li><Typography variant="body2"><strong>Near zero (-0.4 to +0.4):</strong> Neutral conditions → Normal rainfall patterns</Typography></li>
                    <li><Typography variant="body2">IOD primarily affects the "Short rains" season (October-December) in Tanzania</Typography></li>
                    <li><Typography variant="body2">Positive IOD events can combine with El Niño to cause extreme flooding</Typography></li>
                  </ul>
                  <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                    💡 For insurance: IOD is particularly important for predicting short rains season outcomes
                  </Typography>
                </AccordionDetails>
              </Accordion>

              {/* Statistical Distributions */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  📊 Statistical Distributions (2000-2025)
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Understanding the distribution of climate variables helps identify extremes and assess risk.
                </Typography>

                <Grid container spacing={2}>
                  {/* Temperature Distribution */}
                  {allTimeSeries.find(s => s.variable === 'temperature') && (
                    <Grid item xs={12} md={6}>
                      <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Temperature Distribution
                        </Typography>
                        <Alert severity="info" sx={{ mb: 2, bgcolor: '#e3f2fd' }}>
                          <Typography variant="body2">
                            <strong>Interpretation:</strong> The box shows where 50% of values fall (Q1-Q3).
                            The line inside is the median. Dots are outliers (extreme months).
                            A wider box means more temperature variability across the year.
                          </Typography>
                        </Alert>
                        <Chart
                          data={[{
                            y: allTimeSeries.find(s => s.variable === 'temperature')?.data.map(d => d.median) || [],
                            type: 'box' as const,
                            name: 'Temperature',
                            marker: {
                              color: 'rgba(255, 107, 107, 0.7)',
                              line: { color: 'rgb(255, 107, 107)', width: 2 },
                              outliercolor: 'rgba(219, 64, 82, 1)'
                            },
                            boxmean: 'sd',
                            boxpoints: 'outliers',
                            fillcolor: 'rgba(255, 107, 107, 0.15)',
                            line: { width: 2 },
                          }]}
                          layout={{
                            height: 350,
                            yaxis: {
                              title: { text: 'Temperature (°C)', font: { size: 14 } },
                              gridcolor: '#e0e0e0',
                              gridwidth: 1,
                              fixedrange: true
                            },
                            plot_bgcolor: '#fafafa',
                            paper_bgcolor: 'white',
                            showlegend: false,
                            margin: { l: 70, r: 40, t: 40, b: 50 },
                            dragmode: false
                          }}
                          config={{ responsive: true, scrollZoom: false }}
                        />
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                          Box plot shows median, quartiles, and outliers. Wider boxes indicate higher variability.
                        </Typography>
                      </Box>
                    </Grid>
                  )}

                  {/* Rainfall Distribution */}
                  {allTimeSeries.find(s => s.variable === 'rainfall') && (
                    <Grid item xs={12} md={6}>
                      <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Rainfall Distribution
                        </Typography>
                        <Alert severity="info" sx={{ mb: 2, bgcolor: '#e3f2fd' }}>
                          <Typography variant="body2">
                            <strong>Interpretation:</strong> The box shows the middle 50% of rainfall values.
                            Outliers (dots above) indicate exceptionally wet months that may trigger flood payouts.
                            Few/no outliers below suggest consistent minimum rainfall.
                          </Typography>
                        </Alert>
                        <Chart
                          data={[{
                            y: allTimeSeries.find(s => s.variable === 'rainfall')?.data.map(d => d.median) || [],
                            type: 'box' as const,
                            name: 'Rainfall',
                            marker: {
                              color: 'rgba(77, 171, 247, 0.7)',
                              line: { color: 'rgb(77, 171, 247)', width: 2 },
                              outliercolor: 'rgba(34, 139, 230, 1)'
                            },
                            boxmean: 'sd',
                            boxpoints: 'outliers',
                            fillcolor: 'rgba(77, 171, 247, 0.15)',
                            line: { width: 2 },
                          }]}
                          layout={{
                            height: 350,
                            yaxis: {
                              title: { text: 'Rainfall (mm)', font: { size: 14 } },
                              gridcolor: '#e0e0e0',
                              gridwidth: 1,
                              fixedrange: true
                            },
                            plot_bgcolor: '#fafafa',
                            paper_bgcolor: 'white',
                            showlegend: false,
                            margin: { l: 70, r: 40, t: 40, b: 50 },
                            dragmode: false
                          }}
                          config={{ responsive: true, scrollZoom: false }}
                        />
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                          High variability in rainfall is typical for East Africa. Outliers represent extreme wet/dry months.
                        </Typography>
                      </Box>
                    </Grid>
                  )}

                  {/* Monthly Averages - Seasonal Pattern */}
                  {allTimeSeries.find(s => s.variable === 'temperature') && allTimeSeries.find(s => s.variable === 'rainfall') && (
                    <Grid item xs={12}>
                      <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          Seasonal Patterns (Monthly Averages)
                        </Typography>
                        <Chart
                          data={[
                            {
                              x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                              y: (() => {
                                const tempData = allTimeSeries.find(s => s.variable === 'temperature')?.data || []
                                const monthlyAvg = Array(12).fill(0).map((_, month) => {
                                  const monthData = tempData.filter(d => new Date(d.date).getMonth() === month)
                                  return monthData.length > 0
                                    ? monthData.reduce((sum, d) => sum + d.median, 0) / monthData.length
                                    : 0
                                })
                                return monthlyAvg
                              })(),
                              name: 'Temperature',
                              type: 'scatter' as const,
                              mode: 'lines+markers' as const,
                              yaxis: 'y',
                              line: { color: '#ff6b6b', width: 3 },
                              marker: { size: 10, color: '#ff6b6b', symbol: 'circle' },
                              hovertemplate: '<b>Temperature</b><br>%{x}: %{y:.1f}°C<extra></extra>'
                            },
                            {
                              x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                              y: (() => {
                                const rainData = allTimeSeries.find(s => s.variable === 'rainfall')?.data || []
                                const monthlyAvg = Array(12).fill(0).map((_, month) => {
                                  const monthData = rainData.filter(d => new Date(d.date).getMonth() === month)
                                  return monthData.length > 0
                                    ? monthData.reduce((sum, d) => sum + d.median, 0) / monthData.length
                                    : 0
                                })
                                return monthlyAvg
                              })(),
                              name: 'Rainfall',
                              type: 'bar' as const,
                              yaxis: 'y2',
                              marker: {
                                color: 'rgba(77, 171, 247, 0.65)',
                                line: { color: 'rgb(77, 171, 247)', width: 1.5 }
                              },
                              width: 0.6,
                              hovertemplate: '<b>Rainfall</b><br>%{x}: %{y:.0f} mm<extra></extra>'
                            }
                          ]}
                          layout={{
                            height: 400,
                            xaxis: { title: 'Month', titlefont: { size: 14 }, fixedrange: true },
                            yaxis: {
                              title: 'Temperature (°C)',
                              side: 'left',
                              titlefont: { color: '#ff6b6b', size: 14 },
                              tickfont: { color: '#ff6b6b' },
                              gridcolor: '#e0e0e0',
                              fixedrange: true
                            },
                            yaxis2: {
                              title: 'Rainfall (mm)',
                              overlaying: 'y',
                              side: 'right',
                              titlefont: { color: '#4dabf7', size: 14 },
                              tickfont: { color: '#4dabf7' },
                              gridcolor: 'transparent',
                              fixedrange: true
                            },
                            shapes: [
                              {
                                type: 'rect',
                                xref: 'x',
                                yref: 'paper',
                                x0: 2, x1: 4,
                                y0: 0, y1: 1,
                                fillcolor: 'rgba(77, 171, 247, 0.08)',
                                line: { width: 0 },
                                layer: 'below'
                              },
                              {
                                type: 'rect',
                                xref: 'x',
                                yref: 'paper',
                                x0: 9, x1: 11,
                                y0: 0, y1: 1,
                                fillcolor: 'rgba(77, 171, 247, 0.08)',
                                line: { width: 0 },
                                layer: 'below'
                              }
                            ],
                            annotations: [
                              {
                                text: 'Long Rains',
                                xref: 'x',
                                yref: 'paper',
                                x: 3,
                                y: 1.08,
                                showarrow: false,
                                font: { size: 11, color: '#4dabf7' }
                              },
                              {
                                text: 'Short Rains',
                                xref: 'x',
                                yref: 'paper',
                                x: 10,
                                y: 1.08,
                                showarrow: false,
                                font: { size: 11, color: '#4dabf7' }
                              }
                            ],
                            plot_bgcolor: '#fafafa',
                            paper_bgcolor: 'white',
                            showlegend: true,
                            legend: { orientation: 'h', y: -0.2 },
                            margin: { l: 70, r: 70, t: 50, b: 70 }
                          }}
                          config={{ responsive: true, scrollZoom: false }}
                        />
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                          <strong>Long rains (Mar-May)</strong> and <strong>Short rains (Oct-Dec)</strong> are visible as rainfall peaks.
                          Temperature is highest during dry seasons (Jun-Oct).
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              </Box>

              {/* Key Insights */}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  🔍 Key Insights for Climate Risk Assessment:
                </Typography>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" paragraph>
                      <strong>1. Rainfall-NDVI Relationship:</strong> NDVI typically lags rainfall by 1-2 months. Low rainfall followed by declining NDVI indicates crop stress.
                    </Typography>
                    <Typography variant="body2" paragraph>
                      <strong>2. Temperature-Rainfall Balance:</strong> High temperatures with low rainfall create severe drought conditions. Moderate temperatures with adequate rainfall are ideal for crops.
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" paragraph>
                      <strong>3. Ocean Indices as Predictors:</strong> ENSO and IOD provide 3-6 month advance warning of rainfall anomalies, enabling proactive risk management.
                    </Typography>
                    <Typography variant="body2" paragraph>
                      <strong>4. Seasonal Patterns:</strong> Tanzania's bimodal rainfall pattern (two rainy seasons) means risks vary throughout the year. Long rains (March-May) are typically more reliable than short rains (October-December).
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Correlation Heatmap - Always shows all 5 variables */}
        {
          correlationMatrix && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Variable Correlations
                  </Typography>
                  <Alert severity="info" sx={{ mb: 2, bgcolor: '#e3f2fd', borderLeft: '4px solid #2196F3' }}>
                    <Typography variant="body2" paragraph>
                      This heatmap shows how climate variables relate to each other. Values closer to <strong>±1.0</strong> indicate stronger relationships.
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ width: 12, height: 12, bgcolor: '#2196f3' }} /> {/* Blue */}
                          <Typography variant="caption"><strong>Positive (Blue):</strong> Variables increase together</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ width: 12, height: 12, bgcolor: '#f44336' }} /> {/* Red */}
                          <Typography variant="caption"><strong>Negative (Red):</strong> Inverse relationship</Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Typography variant="caption"><strong>Diagonal:</strong> Always 1.0 (Self-correlation)</Typography>
                      </Grid>
                    </Grid>
                  </Alert>
                  <Chart
                    data={correlationData}
                    layout={{
                      height: 600,
                      xaxis: {
                        title: '',
                        tickangle: -45,
                        side: 'bottom',
                        tickfont: { size: 12 },
                        fixedrange: true
                      },
                      yaxis: {
                        title: '',
                        autorange: 'reversed',
                        tickfont: { size: 12 },
                        fixedrange: true
                      },
                      autosize: true,
                      margin: { l: 120, r: 180, t: 50, b: 120 }
                    }}
                    config={{
                      responsive: true,
                      displayModeBar: true,
                      scrollZoom: false
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>
          )
        }

        {/* Anomaly Summary */}
        {
          anomalies.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Detected Anomalies
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {anomalies.length} anomalies detected in the selected period
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {anomalies.slice(0, 10).map((anomaly, index) => (
                      <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                        <Typography variant="body2">
                          <strong>{new Date(anomaly.date).toLocaleDateString()}</strong>
                          {' - '}
                          {anomaly.variable}: {anomaly.value.toFixed(2)}
                          {' ('}deviation: {anomaly.deviation.toFixed(2)}{')'}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )
        }

        {/* Statistics Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                Data Points
              </Typography>
              <Typography variant="h4">
                {timeSeries.reduce((sum, series) => sum + series.data.length, 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Across {selectedVariables.length} variable(s)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                Anomalies Detected
              </Typography>
              <Typography variant="h4" color="warning.main">
                {anomalies.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Significant deviations from normal
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                Date Range
              </Typography>
              <Typography variant="h6">
                {timeSeries[0]?.data[0]?.date ?
                  new Date(timeSeries[0].data[0].date).toLocaleDateString() : 'N/A'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                to {timeSeries[0]?.data[timeSeries[0].data.length - 1]?.date ?
                  new Date(timeSeries[0].data[timeSeries[0].data.length - 1].date).toLocaleDateString() : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Advanced Analytics Section */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 2 }}>
            📈 Advanced Climate Analytics
          </Typography>
        </Grid>

        {/* Rolling Window Metrics */}
        {
          allTimeSeries.find(s => s.variable === 'temperature') && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    12-Month Rolling Average (Trend Detection)
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Smoothed trends help identify climate shifts and long-term patterns beyond seasonal variation.
                  </Typography>
                  <Alert severity="info" sx={{ mb: 2, bgcolor: '#e3f2fd' }}>
                    <Typography variant="body2">
                      <strong>What to look for:</strong> Upward/downward slopes indicate warming/cooling trends.
                      Flat periods show stable climate. Sudden changes suggest regime shifts that may affect trigger frequencies.
                    </Typography>
                  </Alert>
                  <Chart
                    data={(() => {
                      const calculateRollingAvg = (data: any[], window: number) => {
                        return data.map((_, idx) => {
                          if (idx < window - 1) return null
                          const windowData = data.slice(idx - window + 1, idx + 1)
                          return windowData.reduce((sum, d) => sum + d.median, 0) / window
                        })
                      }

                      const tempData = allTimeSeries.find(s => s.variable === 'temperature')?.data || []
                      const rainData = allTimeSeries.find(s => s.variable === 'rainfall')?.data || []

                      return [
                        {
                          x: tempData.map(d => d.date),
                          y: calculateRollingAvg(tempData, 12),
                          name: 'Temperature (12-mo avg)',
                          type: 'scatter' as const,
                          mode: 'lines' as const,
                          line: { color: '#ff6b6b', width: 3, shape: 'spline' as const },
                          yaxis: 'y',
                          hovertemplate: '<b>Temperature</b><br>%{x}<br>12-mo avg: %{y:.1f}°C<extra></extra>'
                        },
                        {
                          x: rainData.map(d => d.date),
                          y: calculateRollingAvg(rainData, 12),
                          name: 'Rainfall (12-mo avg)',
                          type: 'scatter' as const,
                          mode: 'lines' as const,
                          line: { color: '#4dabf7', width: 3, shape: 'spline' as const },
                          yaxis: 'y2',
                          hovertemplate: '<b>Rainfall</b><br>%{x}<br>12-mo avg: %{y:.0f} mm<extra></extra>'
                        }
                      ]
                    })()}
                    layout={{
                      height: 400,
                      xaxis: {
                        title: { text: 'Date', font: { size: 13 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      yaxis: {
                        title: { text: 'Temperature (°C)', font: { size: 13 } },
                        gridcolor: '#e0e0e0',
                        zeroline: false,
                        fixedrange: true
                      },
                      yaxis2: {
                        title: { text: 'Rainfall (mm)', font: { size: 13 } },
                        overlaying: 'y',
                        side: 'right',
                        showgrid: false,
                        fixedrange: true
                      },
                      showlegend: true,
                      legend: {
                        x: 0.5,
                        y: 1.1,
                        xanchor: 'center',
                        orientation: 'h' as const
                      },
                      plot_bgcolor: '#fafafa',
                      margin: { l: 70, r: 70, t: 40, b: 60 }
                    }}
                    config={{ responsive: true, scrollZoom: false }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    💡 Rolling averages remove monthly noise to reveal medium-term trends and climate regime shifts.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )
        }

        {/* Extreme Events Distribution */}
        {
          allTimeSeries.find(s => s.variable === 'temperature') && allTimeSeries.find(s => s.variable === 'rainfall') && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Extreme Temperature Events
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Distribution of temperature extremes helps assess tail risk for heat/cold triggers.
                  </Typography>
                  <Alert severity="warning" sx={{ mb: 2, bgcolor: '#fff3e0' }}>
                    <Typography variant="body2">
                      <strong>Insurance Application:</strong> The right tail (high values) shows heat stress frequency.
                      If triggers are set at 95th percentile, expect ~5% of months to trigger. Adjust thresholds accordingly.
                    </Typography>
                  </Alert>
                  <Chart
                    data={[{
                      x: allTimeSeries.find(s => s.variable === 'temperature')?.data.map(d => d.max) || [],
                      type: 'histogram' as const,
                      name: 'Max Temperature',
                      marker: {
                        color: 'rgba(255, 107, 107, 0.6)',
                        line: { color: '#e03131', width: 1.5 }
                      },
                      nbinsx: 25,
                      hovertemplate: 'Temperature: %{x:.1f}°C<br>Count: %{y}<extra></extra>'
                    }]}
                    layout={{
                      height: 350,
                      xaxis: {
                        title: { text: 'Maximum Temperature (°C)', font: { size: 13 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      yaxis: {
                        title: { text: 'Frequency', font: { size: 13 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      showlegend: false,
                      plot_bgcolor: '#fafafa',
                      margin: { l: 60, r: 40, t: 40, b: 60 }
                    }}
                    config={{ responsive: true, scrollZoom: false }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    💡 Right tail shows extreme heat events - critical for heat stress trigger thresholds.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )
        }

        {
          allTimeSeries.find(s => s.variable === 'rainfall') && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Extreme Rainfall Events
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Distribution of rainfall extremes for flood and drought risk assessment.
                  </Typography>
                  <Alert severity="warning" sx={{ mb: 2, bgcolor: '#fff3e0' }}>
                    <Typography variant="body2">
                      <strong>Insurance Application:</strong> Right tail = flood risk (high rainfall), left side = drought risk (low rainfall).
                      Use this to calibrate trigger thresholds for different risk levels (e.g., 1-in-10-year vs 1-in-20-year events).
                    </Typography>
                  </Alert>
                  <Chart
                    data={[{
                      x: allTimeSeries.find(s => s.variable === 'rainfall')?.data.map(d => d.max) || [],
                      type: 'histogram' as const,
                      name: 'Max Rainfall',
                      marker: {
                        color: 'rgba(77, 171, 247, 0.6)',
                        line: { color: '#228be6', width: 1.5 }
                      },
                      nbinsx: 25,
                      hovertemplate: 'Rainfall: %{x:.0f} mm<br>Count: %{y}<extra></extra>'
                    }]}
                    layout={{
                      height: 350,
                      xaxis: {
                        title: { text: 'Maximum Rainfall (mm)', font: { size: 13 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      yaxis: {
                        title: { text: 'Frequency', font: { size: 13 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      showlegend: false,
                      plot_bgcolor: '#fafafa',
                      margin: { l: 60, r: 40, t: 40, b: 60 }
                    }}
                    config={{ responsive: true, scrollZoom: false }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    💡 Right tail shows flood events, left tail shows drought conditions.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )
        }

        {/* Variable Relationships - Scatter Plot */}
        {
          allTimeSeries.find(s => s.variable === 'temperature') && allTimeSeries.find(s => s.variable === 'rainfall') && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Temperature-Rainfall Relationship
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Exploring how temperature and rainfall relate helps identify compound climate events.
                  </Typography>
                  <Alert severity="success" sx={{ mb: 2, bgcolor: '#e8f5e9' }}>
                    <Typography variant="body2">
                      <strong>Key Patterns:</strong> Bottom-right corner (hot + dry) = drought conditions.
                      Top-left (cool + wet) = flood risk. Isolated points far from clusters indicate unusual compound events
                      that may need special trigger consideration.
                    </Typography>
                  </Alert>
                  <Chart
                    data={[{
                      x: allTimeSeries.find(s => s.variable === 'temperature')?.data.map(d => d.median) || [],
                      y: allTimeSeries.find(s => s.variable === 'rainfall')?.data.map(d => d.median) || [],
                      type: 'scatter' as const,
                      mode: 'markers' as const,
                      marker: {
                        size: 8,
                        color: timeSeries.find(s => s.variable === 'temperature')?.data.map((_, idx) => idx) || [],
                        colorscale: 'Viridis',
                        opacity: 0.6,
                        line: { color: 'white', width: 0.5 },
                        showscale: true,
                        colorbar: {
                          title: 'Time<br>(older→newer)',
                          titleside: 'right'
                        }
                      },
                      text: allTimeSeries.find(s => s.variable === 'temperature')?.data.map(d => d.date) || [],
                      hovertemplate: '<b>%{text}</b><br>Temp: %{x:.1f}°C<br>Rainfall: %{y:.0f} mm<extra></extra>'
                    }]}
                    layout={{
                      height: 450,
                      xaxis: {
                        title: { text: 'Temperature (°C)', font: { size: 14 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      yaxis: {
                        title: { text: 'Rainfall (mm)', font: { size: 14 } },
                        gridcolor: '#e0e0e0',
                        fixedrange: true
                      },
                      showlegend: false,
                      plot_bgcolor: '#fafafa',
                      margin: { l: 70, r: 100, t: 40, b: 60 }
                    }}
                    config={{ responsive: true, scrollZoom: false }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    💡 Clusters reveal typical climate states. Outliers show extreme combinations (e.g., hot + dry = drought risk).
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )
        }

      </Grid >
    </Box >
  )
}
