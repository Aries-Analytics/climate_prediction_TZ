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

interface TriggerEvent {
  id: number
  date: string
  triggerType: string
  confidence: number
  severity: number
}

export default function ForecastDashboard() {
  const [forecasts, setForecasts] = useState<Forecast[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [historicalTriggers, setHistoricalTriggers] = useState<TriggerEvent[]>([])
  const [selectedTriggerType, setSelectedTriggerType] = useState<string>('all')
  const [selectedHorizon, setSelectedHorizon] = useState<string>('all')
  const [showHistorical, setShowHistorical] = useState<boolean>(true)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const triggerTypes = ['drought', 'flood', 'crop_failure']
  const horizons = [3, 4, 5, 6]

  useEffect(() => {
    fetchForecasts()
    fetchRecommendations()
    fetchHistoricalTriggers()
  }, [])

  const fetchForecasts = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/forecasts/latest`, {
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

  const fetchHistoricalTriggers = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/triggers`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 100 }
      })
      setHistoricalTriggers(response.data)
    } catch (err) {
      // Silently handle - historical data may not be available
      setHistoricalTriggers([])
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

  const getHorizonColor = (horizon: number) => {
    const colors: Record<number, string> = {
      3: '#4caf50',
      4: '#8bc34a',
      5: '#ffc107',
      6: '#ff9800'
    }
    return colors[horizon] || '#9e9e9e'
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

  // Prepare timeline chart data
  const timelineData = triggerTypes.map(triggerType => {
    const typeForecasts = filteredForecasts.filter(f => f.triggerType === triggerType)
    
    return horizons.map(horizon => {
      const horizonForecasts = typeForecasts.filter(f => f.horizonMonths === horizon)
      
      return {
        x: horizonForecasts.map(f => f.targetDate),
        y: horizonForecasts.map(f => f.probability),
        error_y: {
          type: 'data',
          symmetric: false,
          array: horizonForecasts.map(f => f.confidenceUpper - f.probability),
          arrayminus: horizonForecasts.map(f => f.probability - f.confidenceLower),
          color: 'rgba(0,0,0,0.2)',
          thickness: 1,
          width: 3
        },
        type: 'scatter' as const,
        mode: 'lines+markers',
        name: `${triggerType} (${horizon}mo)`,
        line: {
          color: getTriggerTypeColor(triggerType),
          width: 2,
          dash: horizon === 3 ? 'solid' : horizon === 4 ? 'dash' : horizon === 5 ? 'dot' : 'dashdot'
        },
        marker: {
          size: 8,
          color: getTriggerTypeColor(triggerType),
          line: {
            color: '#fff',
            width: 1
          }
        },
        hovertemplate: '<b>%{fullData.name}</b><br>' +
                       'Date: %{x}<br>' +
                       'Probability: %{y:.2%}<br>' +
                       'CI: [%{customdata[0]:.2%}, %{customdata[1]:.2%}]<br>' +
                       '<extra></extra>',
        customdata: horizonForecasts.map(f => [f.confidenceLower, f.confidenceUpper])
      }
    })
  }).flat()

  // Add historical trigger events as markers
  const historicalData = showHistorical ? triggerTypes.map(triggerType => {
    const typeTriggers = historicalTriggers.filter(t => 
      t.triggerType === triggerType && 
      (selectedTriggerType === 'all' || t.triggerType === selectedTriggerType)
    )
    
    return {
      x: typeTriggers.map(t => t.date),
      y: typeTriggers.map(() => 1.0), // Place at top of chart
      type: 'scatter' as const,
      mode: 'markers',
      name: `${triggerType} (actual)`,
      marker: {
        symbol: 'x',
        size: 12,
        color: getTriggerTypeColor(triggerType),
        line: {
          color: '#000',
          width: 2
        }
      },
      hovertemplate: '<b>Actual Trigger Event</b><br>' +
                     'Type: %{fullData.name}<br>' +
                     'Date: %{x}<br>' +
                     '<extra></extra>',
      showlegend: true
    }
  }) : []

  const allChartData = [...timelineData, ...historicalData]

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
            variant={showHistorical ? 'contained' : 'outlined'}
            onClick={() => setShowHistorical(!showHistorical)}
            size="small"
          >
            {showHistorical ? 'Hide' : 'Show'} Historical Events
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

        {/* Forecast Timeline Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Forecast Probability Timeline
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Hover over points for detailed information. Error bars show confidence intervals.
              </Typography>
              <Chart
                data={allChartData}
                layout={{
                  height: 500,
                  xaxis: {
                    title: 'Target Date',
                    type: 'date'
                  },
                  yaxis: {
                    title: 'Trigger Probability',
                    tickformat: '.0%',
                    range: [0, 1]
                  },
                  hovermode: 'closest',
                  legend: {
                    orientation: 'h',
                    y: -0.2
                  },
                  shapes: [
                    {
                      type: 'line',
                      x0: 0,
                      x1: 1,
                      xref: 'paper',
                      y0: 0.3,
                      y1: 0.3,
                      line: {
                        color: 'red',
                        width: 2,
                        dash: 'dash'
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
                        size: 10,
                        color: 'red'
                      }
                    }
                  ]
                }}
                config={{
                  responsive: true
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
                            Target: {new Date(forecast.targetDate).toLocaleDateString()}
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
