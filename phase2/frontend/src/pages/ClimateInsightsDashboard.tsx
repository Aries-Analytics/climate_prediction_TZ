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
  { value: 'temperature', label: 'Temperature (°C)' },
  { value: 'rainfall', label: 'Rainfall (mm)' },
  { value: 'ndvi', label: 'NDVI' },
  { value: 'enso', label: 'ENSO Index' },
  { value: 'iod', label: 'IOD Index' }
]

export default function ClimateInsightsDashboard() {
  const [timeSeries, setTimeSeries] = useState<ClimateTimeSeries[]>([])
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [correlationMatrix, setCorrelationMatrix] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [selectedVariables, setSelectedVariables] = useState<string[]>(['temperature', 'rainfall'])
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

      // Fetch correlation matrix if multiple variables selected
      if (selectedVariables.length > 1) {
        const corrResponse = await axios.get(
          `${API_BASE_URL}/climate/correlations?variables=${selectedVariables.join(',')}`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        setCorrelationMatrix(corrResponse.data)
      }

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

  // Prepare time series chart data
  const timeSeriesChartData = timeSeries.map((series) => ({
    x: series.data.map(d => d.date),
    y: series.data.map(d => d.value),
    name: VARIABLES.find(v => v.value === series.variable)?.label || series.variable,
    type: 'scatter' as const,
    mode: 'lines' as const
  }))

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

  // Prepare correlation heatmap data
  const correlationData = correlationMatrix ? [{
    z: correlationMatrix.matrix,
    x: correlationMatrix.variables,
    y: correlationMatrix.variables,
    type: 'heatmap' as const,
    colorscale: 'RdBu',
    zmid: 0
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
                      renderValue={(selected) => 
                        selected.map(v => VARIABLES.find(var => var.value === v)?.label).join(', ')
                      }
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
                    yaxis: { title: 'Value' },
                    hovermode: 'x unified',
                    showlegend: true
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Correlation Heatmap */}
        {correlationMatrix && selectedVariables.length > 1 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Variable Correlations
                </Typography>
                <Chart
                  data={correlationData}
                  layout={{
                    height: 400,
                    xaxis: { title: '' },
                    yaxis: { title: '' }
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
