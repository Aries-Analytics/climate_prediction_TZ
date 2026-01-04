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
  Chip,
  SelectChangeEvent,
  Button,
  Stack
} from '@mui/material'
import { Download as DownloadIcon, Warning as WarningIcon } from '@mui/icons-material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import Chart from '../components/charts/Chart'
import { prepareForecastTraces } from '../utils/forecastChartUtils'

interface Forecast {
  id: number
  forecastDate: string
  targetDate: string
  horizonMonths: number
  triggerType: string
  probability: number
  confidenceLower: number
  confidenceUpper: number
  modelVersion: string
  createdAt: string
}

interface Recommendation {
  id: number
  forecastId: number
  recommendationText: string
  priority: string
  actionTimeline: string
  createdAt: string
  triggerType?: string  // Added to track which trigger type this recommendation is for
}

interface ForecastWithRecommendations extends Forecast {
  recommendations?: Recommendation[]
}



export default function ForecastDashboard() {
  const [forecasts, setForecasts] = useState<Forecast[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [selectedTriggerType, setSelectedTriggerType] = useState<string>('all')
  const [selectedHorizon, setSelectedHorizon] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const triggerTypes = ['drought', 'flood', 'crop_failure']
  const horizons = [3, 4, 5, 6]

  useEffect(() => {
    fetchForecasts()
    fetchRecommendations()
  }, [])

  const fetchForecasts = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      // Fetch ALL forecasts (not just latest) to show timeline
      const response = await axios.get(`${API_BASE_URL}/forecasts`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setForecasts(response.data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch forecasts')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchRecommendations = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/forecasts/recommendations`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { min_probability: 0.3 }
      })
      
      console.log('Recommendations API response:', response.data)
      console.log('Number of forecasts with recommendations:', response.data.length)
      
      // Extract recommendations from nested structure
      // API returns ForecastWithRecommendations[] (forecasts with nested recommendations)
      const allRecommendations: Recommendation[] = []
      response.data.forEach((forecast: ForecastWithRecommendations) => {
        console.log(`Forecast ${forecast.id} has ${forecast.recommendations?.length || 0} recommendations`)
        if (forecast.recommendations && forecast.recommendations.length > 0) {
          // Add trigger type to each recommendation for consistent coloring
          const recsWithTriggerType = forecast.recommendations.map(rec => ({
            ...rec,
            triggerType: forecast.triggerType
          }))
          allRecommendations.push(...recsWithTriggerType)
        }
      })
      
      console.log('Total recommendations extracted:', allRecommendations.length)
      console.log('Recommendations:', allRecommendations)
      
      setRecommendations(allRecommendations)
    } catch (err) {
      console.error('Failed to fetch recommendations:', err)
      // Silently handle - recommendations may not be available
      setRecommendations([])
    }
  }

  const handleGenerateForecasts = async () => {
    try {
      setIsGenerating(true)
      setError(null)
      setSuccessMessage(null)
      
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/forecasts/generate`,
        { horizons: [3, 4, 5, 6] },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      setSuccessMessage(`Successfully generated ${response.data.length} new forecasts`)
      
      // Refresh data
      await fetchForecasts()
      await fetchRecommendations()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate forecasts')
    } finally {
      setIsGenerating(false)
    }
  }



  const handleTriggerTypeChange = (event: SelectChangeEvent) => {
    setSelectedTriggerType(event.target.value)
  }

  const handleHorizonChange = (event: SelectChangeEvent) => {
    setSelectedHorizon(event.target.value)
  }

  const handleExportCSV = () => {
    const filteredForecasts = getFilteredForecasts()
    
    // Create CSV content
    const headers = ['Forecast Date', 'Target Date', 'Horizon (Months)', 'Trigger Type', 'Probability', 'Confidence Lower', 'Confidence Upper', 'Model Version']
    const rows = filteredForecasts.map(f => [
      f.forecastDate,
      f.targetDate,
      f.horizonMonths,
      f.triggerType,
      f.probability.toFixed(4),
      f.confidenceLower.toFixed(4),
      f.confidenceUpper.toFixed(4),
      f.modelVersion
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `forecasts_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const getFilteredForecasts = () => {
    return forecasts.filter(f => {
      const typeMatch = selectedTriggerType === 'all' || f.triggerType === selectedTriggerType
      const horizonMatch = selectedHorizon === 'all' || f.horizonMonths === parseInt(selectedHorizon)
      return typeMatch && horizonMatch
    })
  }

  const getPriorityColor = (priority: string): 'error' | 'warning' | 'info' => {
    if (priority === 'high') return 'error'
    if (priority === 'medium') return 'warning'
    return 'info'
  }

  const getTriggerTypeColor = (triggerType: string) => {
    const colors: Record<string, string> = {
      drought: '#ff9800',
      flood: '#2196f3',
      crop_failure: '#f44336'
    }
    return colors[triggerType] || '#9e9e9e'
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading forecasts..." />
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (forecasts.length === 0) {
    return (
      <EmptyState
        message="No forecasts available"
        description="Forecasts will appear here once they are generated"
      />
    )
  }

  const filteredForecasts = getFilteredForecasts()

  // Prepare clean forecast-only timeline data
  const timelineData = prepareForecastTraces(filteredForecasts)
  
  // Calculate date range for focused view (today + 12 months)
  const today = new Date()
  const futureDate = new Date(today)
  futureDate.setMonth(futureDate.getMonth() + 12)

  // High-risk forecasts (probability > 0.3)
  const highRiskForecasts = filteredForecasts.filter(f => f.probability > 0.3)

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Early Warning System
          </Typography>
          <Typography variant="body2" color="text.secondary">
            3-6 month forecast predictions for climate-related insurance triggers
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGenerateForecasts}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate New Forecasts'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportCSV}
          >
            Export CSV
          </Button>
        </Stack>
      </Box>

      {successMessage && (
        <Alert severity="success" onClose={() => setSuccessMessage(null)} sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      {highRiskForecasts.length > 0 && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="bold">
            {highRiskForecasts.length} high-risk event{highRiskForecasts.length > 1 ? 's' : ''} predicted
          </Typography>
          <Typography variant="caption">
            Forecasts with probability &gt; 30% require attention
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Filters */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <FormControl fullWidth>
                <InputLabel>Trigger Type</InputLabel>
                <Select
                  value={selectedTriggerType}
                  label="Trigger Type"
                  onChange={handleTriggerTypeChange}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  {triggerTypes.map(type => (
                    <MenuItem key={type} value={type}>
                      {type.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <FormControl fullWidth>
                <InputLabel>Forecast Horizon</InputLabel>
                <Select
                  value={selectedHorizon}
                  label="Forecast Horizon"
                  onChange={handleHorizonChange}
                >
                  <MenuItem value="all">All Horizons</MenuItem>
                  {horizons.map(h => (
                    <MenuItem key={h} value={h.toString()}>
                      {h} Months Ahead
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Visual Legend Guide */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: 'info.50' }}>
            <CardContent>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                📊 Chart Guide
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <Typography variant="caption" fontWeight="bold" display="block">Line Colors:</Typography>
                  <Typography variant="caption" display="block">🟠 Orange = Drought</Typography>
                  <Typography variant="caption" display="block">🔵 Blue = Flood</Typography>
                  <Typography variant="caption" display="block">🔴 Red = Crop Failure</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="caption" fontWeight="bold" display="block">Line Styles:</Typography>
                  <Typography variant="caption" display="block">━━━ Solid = 3 months ahead</Typography>
                  <Typography variant="caption" display="block">╌╌╌ Dash = 4 months ahead</Typography>
                  <Typography variant="caption" display="block">··· Dot = 5 months ahead</Typography>
                  <Typography variant="caption" display="block">━·━ Dash-Dot = 6 months ahead</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="caption" fontWeight="bold" display="block">Error Bars:</Typography>
                  <Typography variant="caption" display="block">Vertical bars show 95% confidence interval</Typography>
                  <Typography variant="caption" display="block">Wider bars = more uncertainty</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="caption" fontWeight="bold" display="block">Risk Threshold:</Typography>
                  <Typography variant="caption" display="block">Red dashed line at 30%</Typography>
                  <Typography variant="caption" display="block">Above = High risk, action needed</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Forecast Timeline Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Forecast Probability Timeline - Next 6 Months
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Showing predicted trigger probabilities for the next 3-6 months. Click legend items to show/hide specific forecasts.
              </Typography>
              <Chart
                data={timelineData}
                layout={{
                  height: 500,
                  xaxis: {
                    title: 'Target Date (Forecast Horizon)',
                    type: 'date',
                    range: [today.toISOString().split('T')[0], futureDate.toISOString().split('T')[0]],
                    fixedrange: false,
                    gridcolor: '#e0e0e0',
                    showgrid: true
                  },
                  yaxis: {
                    title: 'Trigger Probability',
                    tickformat: '.0%',
                    range: [0, 1],
                    fixedrange: false,
                    gridcolor: '#e0e0e0',
                    showgrid: true,
                    zeroline: true,
                    zerolinecolor: '#999',
                    zerolinewidth: 1
                  },
                  hovermode: 'closest',
                  showlegend: true,
                  legend: {
                    orientation: 'v',
                    y: 1,
                    x: 1.02,
                    xanchor: 'left',
                    yanchor: 'top',
                    bgcolor: 'rgba(255,255,255,0.95)',
                    bordercolor: '#ccc',
                    borderwidth: 1,
                    itemclick: 'toggle',
                    itemdoubleclick: false,
                    font: {
                      size: 11
                    }
                  },
                  margin: { l: 80, r: 200, t: 40, b: 80 },
                  shapes: [
                    {
                      type: 'line',
                      x0: 0,
                      x1: 1,
                      xref: 'paper',
                      y0: 0.3,
                      y1: 0.3,
                      line: {
                        color: '#d32f2f',
                        width: 2,
                        dash: 'dash'
                      }
                    },
                    {
                      type: 'line',
                      x0: today.toISOString().split('T')[0],
                      x1: today.toISOString().split('T')[0],
                      xref: 'x',
                      y0: 0,
                      y1: 1,
                      yref: 'y',
                      line: {
                        color: '#666',
                        width: 2,
                        dash: 'solid'
                      }
                    }
                  ],
                  annotations: [
                    {
                      x: 0.02,
                      y: 0.32,
                      xref: 'paper',
                      yref: 'y',
                      text: 'High Risk Threshold (30%)',
                      showarrow: false,
                      font: {
                        size: 11,
                        color: '#d32f2f',
                        family: 'Arial, sans-serif'
                      },
                      bgcolor: 'rgba(255,255,255,0.8)',
                      borderpad: 4
                    },
                    {
                      x: today.toISOString().split('T')[0],
                      y: 1.02,
                      xref: 'x',
                      yref: 'y',
                      text: '📍 Today',
                      showarrow: true,
                      arrowhead: 2,
                      arrowsize: 1,
                      arrowwidth: 2,
                      arrowcolor: '#666',
                      ax: 0,
                      ay: -30,
                      font: {
                        size: 11,
                        color: '#666',
                        family: 'Arial, sans-serif'
                      },
                      bgcolor: 'rgba(255,255,255,0.9)',
                      borderpad: 4
                    }
                  ]
                }}
                config={{
                  responsive: true,
                  displayModeBar: true,
                  displaylogo: false,
                  modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
                  editable: false,
                  scrollZoom: false
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* High-Risk Forecasts Summary */}
        {highRiskForecasts.length > 0 && (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  High-Risk Forecasts (Probability &gt; 30%)
                </Typography>
                <Grid container spacing={2}>
                  {highRiskForecasts.slice(0, 6).map(forecast => (
                    <Grid item xs={12} sm={6} md={4} key={forecast.id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                            <Chip
                              label={forecast.triggerType.replace('_', ' ').toUpperCase()}
                              size="small"
                              sx={{ bgcolor: getTriggerTypeColor(forecast.triggerType), color: '#fff' }}
                            />
                            <Chip
                              label={`${forecast.horizonMonths}mo`}
                              size="small"
                              variant="outlined"
                            />
                          </Stack>
                          <Typography variant="h5" color="error" gutterBottom>
                            {(forecast.probability * 100).toFixed(1)}%
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Target: {forecast.targetDate ? new Date(forecast.targetDate).toLocaleDateString() : 'N/A'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block">
                            CI: [{(forecast.confidenceLower * 100).toFixed(1)}%, {(forecast.confidenceUpper * 100).toFixed(1)}%]
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Recommendations Panel */}
        {recommendations.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recommended Actions
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                  Actionable recommendations based on high-risk forecasts
                </Typography>
                <Stack spacing={2}>
                  {recommendations.map(rec => (
                    <Alert
                      key={rec.id}
                      severity={getPriorityColor(rec.priority)}
                      sx={{ 
                        alignItems: 'flex-start',
                        borderLeft: `4px solid ${getTriggerTypeColor(rec.triggerType || '')}`,
                        '& .MuiAlert-icon': {
                          color: getTriggerTypeColor(rec.triggerType || '')
                        }
                      }}
                    >
                      <Typography variant="body2" fontWeight="bold" gutterBottom>
                        {rec.recommendationText}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Timeline: {rec.actionTimeline}
                      </Typography>
                    </Alert>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}
