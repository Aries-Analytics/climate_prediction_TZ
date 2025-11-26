import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import DataTable from '../components/common/DataTable'
import Chart from '../components/charts/Chart'
import { TriggerEvent, TriggerForecast } from '../types'

export default function TriggersDashboard() {
  const [triggers, setTriggers] = useState<TriggerEvent[]>([])
  const [forecasts, setForecasts] = useState<TriggerForecast[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Filters
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [triggerType, setTriggerType] = useState<string>('all')

  useEffect(() => {
    fetchTriggers()
    fetchForecasts()
  }, [])

  const fetchTriggers = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (triggerType !== 'all') params.append('trigger_type', triggerType)

      const response = await axios.get(`${API_BASE_URL}/triggers?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setTriggers(response.data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch trigger events')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchForecasts = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/triggers/forecast`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setForecasts(response.data)
    } catch (err) {
      console.error('Failed to fetch forecasts:', err)
    }
  }

  const handleApplyFilters = () => {
    fetchTriggers()
  }

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (triggerType !== 'all') params.append('trigger_type', triggerType)

      const response = await axios.get(`${API_BASE_URL}/triggers/export?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `triggers_${new Date().toISOString()}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('Failed to export triggers:', err)
    }
  }

  const handleTriggerTypeChange = (event: SelectChangeEvent) => {
    setTriggerType(event.target.value)
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading trigger events..." />
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  const triggerColumns = [
    { 
      id: 'date', 
      label: 'Date',
      format: (v: string) => new Date(v).toLocaleDateString()
    },
    { id: 'triggerType', label: 'Type' },
    { 
      id: 'confidence', 
      label: 'Confidence',
      format: (v: number) => v != null ? (v * 100).toFixed(1) + '%' : 'N/A'
    },
    { 
      id: 'severity', 
      label: 'Severity',
      format: (v: number) => v != null ? (v * 100).toFixed(1) + '%' : 'N/A'
    },
    { 
      id: 'payoutAmount', 
      label: 'Payout (TZS)',
      format: (v: number) => {
        if (v == null) return 'N/A'
        // Manual comma formatting
        const num = Math.round(v)
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' TZS'
      }
    }
  ]

  // Color mapping for consistent event type colors
  const getEventColor = (triggerType: string): string => {
    const colorMap: Record<string, string> = {
      'drought': '#2196F3',      // Blue
      'flood': '#4CAF50',        // Green
      'crop_failure': '#FF9800'  // Orange
    }
    return colorMap[triggerType] || '#2196F3'
  }

  // Helper to format currency
  const formatCurrency = (value: number) => {
    return Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  }

  // Helper to get trigger description
  const getTriggerDescription = (type: string): string => {
    const descriptions: Record<string, string> = {
      'drought': 'Extended period of low rainfall causing water stress',
      'flood': 'Excessive rainfall causing waterlogging and crop damage',
      'crop_failure': 'Vegetation health decline indicating crop stress'
    }
    return descriptions[type] || type
  }

  // Timeline chart data with rich tooltips
  const timelineData = triggers.reduce((acc: any, trigger) => {
    const type = trigger.triggerType
    if (!acc[type]) {
      const color = getEventColor(type)
      acc[type] = { 
        x: [], 
        y: [], 
        text: [],
        name: type, 
        type: 'scatter', 
        mode: 'markers',
        marker: {
          color: color,
          size: 10,
          line: {
            color: color,
            width: 1
          }
        },
        hovertemplate: '<b>%{text}</b><extra></extra>'
      }
    }
    acc[type].x.push(trigger.date)
    acc[type].y.push(trigger.severity)
    
    // Create rich tooltip text
    const tooltipText = `${type.toUpperCase()} Event<br>` +
                       `Date: ${new Date(trigger.date).toLocaleDateString()}<br>` +
                       `Severity: ${(trigger.severity * 100).toFixed(1)}%<br>` +
                       `Confidence: ${(trigger.confidence * 100).toFixed(1)}%<br>` +
                       `Payout: ${formatCurrency(trigger.payoutAmount)} TZS<br>` +
                       `<i>${getTriggerDescription(type)}</i>`
    acc[type].text.push(tooltipText)
    return acc
  }, {})

  // Forecast chart data
  const forecastData = forecasts.reduce((acc: any, forecast) => {
    const type = forecast.triggerType
    if (!acc[type]) {
      const color = getEventColor(type)
      acc[type] = { 
        x: [], 
        y: [], 
        name: type, 
        type: 'scatter', 
        mode: 'lines+markers',
        marker: {
          color: color,
          size: 8
        },
        line: {
          color: color,
          width: 2
        },
        error_y: {
          type: 'data',
          symmetric: false,
          array: [],
          arrayminus: []
        }
      }
    }
    acc[type].x.push(forecast.targetDate)
    acc[type].y.push(forecast.probability)
    acc[type].error_y.array.push(forecast.confidenceUpper - forecast.probability)
    acc[type].error_y.arrayminus.push(forecast.probability - forecast.confidenceLower)
    return acc
  }, {})

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Trigger Events Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Historical trigger events, forecasts, and early warnings
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Filters */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Filters
              </Typography>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={3}>
                  <TextField
                    label="Start Date"
                    type="date"
                    fullWidth
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField
                    label="End Date"
                    type="date"
                    fullWidth
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Trigger Type</InputLabel>
                    <Select
                      value={triggerType}
                      label="Trigger Type"
                      onChange={handleTriggerTypeChange}
                    >
                      <MenuItem value="all">All Types</MenuItem>
                      <MenuItem value="drought">Drought</MenuItem>
                      <MenuItem value="flood">Flood</MenuItem>
                      <MenuItem value="crop_failure">Crop Failure</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleApplyFilters}
                  >
                    Apply Filters
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Timeline Chart */}
        {triggers.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trigger Events Timeline
                </Typography>
                <Chart
                  data={Object.values(timelineData)}
                  layout={{
                    height: 400,
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Severity', range: [-0.05, 1.05] },
                    hovermode: 'closest',
                    showlegend: true,
                    autosize: true
                  }}
                  config={{
                    displayModeBar: true,
                    responsive: true
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Forecast Chart */}
        {forecasts.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trigger Probability Forecast
                </Typography>
                <Chart
                  data={Object.values(forecastData)}
                  layout={{
                    height: 400,
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Probability', range: [-0.05, 1.05] },
                    hovermode: 'closest',
                    showlegend: true,
                    autosize: true
                  }}
                  config={{
                    displayModeBar: true,
                    responsive: true
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Trigger Events Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Trigger Events
                </Typography>
                <Button
                  variant="outlined"
                  onClick={handleExport}
                  disabled={triggers.length === 0}
                >
                  Export CSV
                </Button>
              </Box>
              {triggers.length > 0 ? (
                <DataTable
                  columns={triggerColumns}
                  rows={triggers}
                  searchable
                />
              ) : (
                <EmptyState
                  message="No trigger events found"
                  description="Try adjusting your filters"
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
