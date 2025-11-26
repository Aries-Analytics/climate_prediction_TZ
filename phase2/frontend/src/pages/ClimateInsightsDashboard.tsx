import { useState, useEffect } from 'react'
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
  TextField
} from '@mui/material'
import axios from 'axios'
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
  const [timeSeries, setTimeSeries] = useState<ClimateTimeSeries[]>([])
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [correlationMatrix, setCorrelationMatrix] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [selectedVariables, setSelectedVariables] = useState<string[]>(['temperature', 'rainfall', 'ndvi', 'enso', 'iod'])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    fetchClimateData()
  }, [selectedVariables, startDate, endDate])

  const fetchClimateData = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      
      // Fetch time series for each selected variable
      const timeSeriesPromises = selectedVariables.map(async (variable) => {
        const params = new URLSearchParams()
        if (startDate) params.append('start_date', startDate)
        if (endDate) params.append('end_date', endDate)
        
        const response = await axios.get(
          `${API_BASE_URL}/climate/timeseries?variable=${variable}&${params}`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        return response.data
      })

      const timeSeriesData = await Promise.all(timeSeriesPromises)
      setTimeSeries(timeSeriesData)

      // Fetch anomalies
      if (selectedVariables.length > 0) {
        const anomalyResponse = await axios.get(
          `${API_BASE_URL}/climate/anomalies?variable=${selectedVariables[0]}`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        setAnomalies(anomalyResponse.data)
      }

      // Always fetch correlation matrix for all 5 variables (independent of time series selection)
      const allVariables = ['temperature', 'rainfall', 'ndvi', 'enso', 'iod']
      const corrParams = new URLSearchParams()
      allVariables.forEach(v => corrParams.append('variables', v))
      const corrResponse = await axios.get(
        `${API_BASE_URL}/climate/correlations?${corrParams.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      console.log('Correlation response:', corrResponse.data)
      setCorrelationMatrix(corrResponse.data)

      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch climate data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVariableChange = (event: SelectChangeEvent<typeof selectedVariables>) => {
    const value = event.target.value
    setSelectedVariables(typeof value === 'string' ? value.split(',') : value)
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

  // Normalize data for better visualization (0-1 scale)
  const normalizeData = (data: number[]) => {
    const min = Math.min(...data)
    const max = Math.max(...data)
    return data.map(v => (v - min) / (max - min))
  }

  // Prepare time series chart data with dual axes
  const timeSeriesChartData = timeSeries.map((series, index) => {
    const varInfo = VARIABLES.find(v => v.value === series.variable)
    const isSecondaryAxis = ['ndvi', 'enso', 'iod'].includes(series.variable)
    
    return {
      x: series.data.map(d => d.date),
      y: series.data.map(d => d.value),
      name: varInfo?.label || series.variable,
      type: 'scatter' as const,
      mode: 'lines' as const,
      yaxis: isSecondaryAxis ? 'y2' : 'y',
      hovertemplate: `<b>${varInfo?.label}</b><br>` +
                     `Date: %{x}<br>` +
                     `Value: %{y:.2f}<br>` +
                     `<i>${varInfo?.tooltip}</i><extra></extra>`,
      line: {
        width: 2
      }
    }
  })

  // Prepare anomaly markers
  const anomalyMarkers = anomalies.length > 0 ? {
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

  // Prepare correlation heatmap data with better formatting
  const correlationData = correlationMatrix ? [{
    z: correlationMatrix.matrix,
    x: correlationMatrix.variables.map((v: string) => {
      const varInfo = VARIABLES.find(varItem => varItem.value === v)
      return varInfo?.label.split(' ')[0] || v  // Use short labels
    }),
    y: correlationMatrix.variables.map((v: string) => {
      const varInfo = VARIABLES.find(varItem => varItem.value === v)
      return varInfo?.label.split(' ')[0] || v  // Use short labels
    }),
    type: 'heatmap' as const,
    colorscale: [
      [0, '#d73027'],      // Strong negative (red)
      [0.25, '#fc8d59'],   // Moderate negative (orange)
      [0.5, '#ffffbf'],    // No correlation (yellow)
      [0.75, '#91bfdb'],   // Moderate positive (light blue)
      [1, '#4575b4']       // Strong positive (dark blue)
    ],
    zmid: 0,
    zmin: -1,
    zmax: 1,
    text: correlationMatrix.matrix.map((row: number[]) => 
      row.map((val: number) => {
        const absVal = Math.abs(val)
        let strength = ''
        if (absVal > 0.7) strength = 'Strong'
        else if (absVal > 0.4) strength = 'Moderate'
        else if (absVal > 0.2) strength = 'Weak'
        else strength = 'None'
        return `${val.toFixed(2)}\n${strength}`
      })
    ),
    texttemplate: '%{text}',
    textfont: { 
      size: 11,
      color: correlationMatrix.matrix.map((row: number[]) => 
        row.map((val: number) => Math.abs(val) > 0.5 ? 'white' : 'black')
      )
    },
    hovertemplate: '<b>%{y} vs %{x}</b><br>' +
                   'Correlation: %{z:.3f}<br>' +
                   '<i>Interpretation:</i><br>' +
                   '• |r| > 0.7 = Strong relationship<br>' +
                   '• |r| 0.4-0.7 = Moderate relationship<br>' +
                   '• |r| 0.2-0.4 = Weak relationship<br>' +
                   '• |r| < 0.2 = No relationship<br>' +
                   '• Positive = variables move together<br>' +
                   '• Negative = variables move opposite<extra></extra>',
    colorbar: {
      title: {
        text: 'Correlation<br>Strength',
        side: 'right'
      },
      tickvals: [-1, -0.7, -0.4, 0, 0.4, 0.7, 1],
      ticktext: [
        '-1.0<br><b>Strong -</b>', 
        '-0.7<br>Moderate -', 
        '-0.4<br>Weak -',
        '0<br><b>None</b>', 
        '0.4<br>Weak +',
        '0.7<br>Moderate +',
        '1.0<br><b>Strong +</b>'
      ],
      thickness: 20,
      len: 0.9
    }
  }] : []

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Climate Insights Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Analyze climate trends, anomalies, and correlations
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12}>
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
                <Grid item xs={12} md={4}>
                  <TextField
                    label="Start Date"
                    type="date"
                    fullWidth
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
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
        {timeSeriesChartData.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Climate Time Series
                </Typography>
                <Chart
                  data={anomalyMarkers ? [...timeSeriesChartData, anomalyMarkers] : timeSeriesChartData}
                  layout={{
                    height: 500,
                    xaxis: { title: 'Date' },
                    yaxis: { 
                      title: 'Temperature (°C) / Rainfall (mm)',
                      side: 'left'
                    },
                    yaxis2: {
                      title: 'NDVI / ENSO / IOD Index',
                      overlaying: 'y',
                      side: 'right',
                      showgrid: false
                    },
                    hovermode: 'x unified',
                    showlegend: true,
                    autosize: true,
                    legend: {
                      orientation: 'h',
                      y: -0.2
                    }
                  }}
                  config={{
                    responsive: true
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Correlation Heatmap - Always shows all 5 variables */}
        {correlationMatrix && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Variable Correlations
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  This heatmap shows how climate variables relate to each other. 
                  <strong> Positive correlations</strong> (blue) mean variables increase together. 
                  <strong> Negative correlations</strong> (red) mean when one increases, the other decreases.
                  Values closer to ±1.0 indicate stronger relationships. Diagonal values are always 1.0 (perfect self-correlation).
                </Typography>
                <Chart
                  data={correlationData}
                  layout={{
                    height: 600,
                    xaxis: { 
                      title: '',
                      tickangle: -45,
                      side: 'bottom',
                      tickfont: { size: 12 }
                    },
                    yaxis: { 
                      title: '',
                      autorange: 'reversed',
                      tickfont: { size: 12 }
                    },
                    autosize: true,
                    margin: { l: 120, r: 180, t: 50, b: 120 }
                  }}
                  config={{
                    responsive: true,
                    displayModeBar: true
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Anomaly Summary */}
        {anomalies.length > 0 && (
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
        )}

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
      </Grid>
    </Box>
  )
}
