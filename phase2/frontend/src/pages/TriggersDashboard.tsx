import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Tooltip,
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
  Chip,
  SelectChangeEvent
} from '@mui/material'
import { InfoOutlined, ShowChart } from '@mui/icons-material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import DataTable from '../components/common/DataTable'
import Chart from '../components/charts/Chart'
import GeographicMap from '../components/GeographicMap'
// direct import for small gauges to avoid Chart's min-height
import Plot from 'react-plotly.js'
import { TriggerEvent, TriggerForecast } from '../types'

export default function TriggersDashboard() {
  const [triggers, setTriggers] = useState<TriggerEvent[]>([])
  const [forecasts, setForecasts] = useState([])
  const [statistics, setStatistics] = useState<any>({})
  const [locations, setLocations] = useState<Array<{ id: number, name: string, latitude: number, longitude: number }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [triggerType, setTriggerType] = useState<string>('all')

  useEffect(() => {
    fetchLocations()
    fetchTriggers()
    fetchForecasts()
    fetchStatistics()
  }, [])

  const fetchLocations = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/locations`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setLocations(response.data)
    } catch (err) {
      console.error('Failed to fetch locations:', err)
    }
  }

  const fetchTriggers = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      const params = new URLSearchParams()
      params.append('limit', '1000')  // Fetch all triggers for accurate rate calculation
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

  const fetchStatistics = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/triggers/statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      // Convert snake_case response to camelCase for frontend
      setStatistics({
        totalCount: response.data.total_count,
        totalPayout: response.data.total_payout,
        totalPeriods: response.data.total_periods,
        rates: response.data.rates || {}
      })
    } catch (err) {
      console.error('Failed to fetch statistics:', err)
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
      label: 'Payout (USD)',
      format: (v: number) => {
        if (v == null) return 'N/A'
        return formatCurrency(v)
      }
    }
  ]

  // Color mapping - Scientific Standards
  // Drought: Brown (U.S. Drought Monitor standard)
  // Flood: Blue (FEMA flood map standard)
  // Crop Failure: Orange (Colorblind-safe, agricultural stress)
  const getEventColor = (triggerType: string): string => {
    const colorMap: Record<string, string> = {
      drought: '#D2691E',      // Chocolate Brown - U.S. Drought Monitor
      flood: '#2196F3',        // Material Blue - FEMA standard
      crop_failure: '#FF9800'  // Material Orange - Colorblind safe
    }
    return colorMap[triggerType] || '#2196F3'
  }

  // Helper to format currency in USD
  const formatCurrency = (value: number) => {
    return '$' + Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
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
      `Payout: ${formatCurrency(trigger.payoutAmount)}<br>` +
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

  // Use rates from statistics endpoint (server-side calculation, scales with any data size)
  const droughtRate = statistics?.rates?.drought ?? 0
  const floodRate = statistics?.rates?.flood ?? 0
  const cropFailureRate = statistics?.rates?.crop_failure ?? 0
  const totalTriggers = statistics?.totalCount ?? triggers.length

  // Helper to ensure numeric values
  const safeValue = (val: any) => {
    const num = parseFloat(val);
    return isNaN(num) ? 0 : num;
  };

  const totalPayout = triggers.reduce((sum, t) => sum + safeValue(t.payoutAmount), 0);
  const avgSeverity = triggers.length > 0
    ? (triggers.reduce((sum, t) => sum + safeValue(t.severity), 0) / triggers.length) * 100
    : 0;

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Trigger Events Dashboard
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Historical trigger events, forecasts, and early warnings
          </Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={handleExport}
            disabled={triggers.length === 0}
            startIcon={<ShowChart sx={{ transform: 'rotate(90deg)' }} />}
          >
            Export Data
          </Button>
        </Box>
      </Box>



      {/* Key Metrics Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Total Financial Exposure
              </Typography>
              <Typography variant="h3" color="primary" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(totalPayout)}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, mb: 1 }}>
                Cumulative potential payouts
              </Typography>
              <Box sx={{
                mt: 2,
                p: 1.5,
                bgcolor: '#e3f2fd',
                borderRadius: 1,
                borderLeft: '4px solid #2196f3'
              }}>
                <Typography variant="body2" color="primary.dark" sx={{ lineHeight: 1.6 }}>
                  <strong>Goal:</strong> Maintain &lt;75% Loss Ratio. High values indicate downside risk.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Trigger Frequency
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {triggers.length}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, mb: 1 }}>
                Total trigger events recorded
              </Typography>
              <Box sx={{
                mt: 2,
                p: 1.5,
                bgcolor: '#fff3e0',
                borderRadius: 1,
                borderLeft: '4px solid #ff9800'
              }}>
                <Typography variant="body2" color="warning.dark" sx={{ lineHeight: 1.6 }}>
                  <strong>Monitor Drift:</strong> &gt;23/yr baseline. &gt;40/yr suggests need for recalibration.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Avg. Event Severity
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {avgSeverity.toFixed(1)}%
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, mb: 1 }}>
                Average magnitude of events
              </Typography>
              <Box sx={{
                mt: 2,
                p: 1.5,
                bgcolor: '#e8f5e9',
                borderRadius: 1,
                borderLeft: '4px solid #4caf50'
              }}>
                <Typography variant="body2" color="success.dark" sx={{ lineHeight: 1.6 }}>
                  <strong>Basis Risk:</strong> High severity (&gt;85%) confirms valid disasters vs operational noise.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Business Logic Context - Educational Information */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card sx={{ bgcolor: 'info.50' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <InfoOutlined color="info" />
                <Typography variant="h6">
                  Understanding Parametric Metrics
                </Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    💰 Total Financial Exposure
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • <strong>Target:</strong> Maintain &lt;75% Loss Ratio<br />
                    • <strong>Status:</strong> Measures potential payout liabilities<br />
                    • <strong>Risk:</strong> High exposure relative to premiums indicates downside financial risk.
                  </Typography>
                  <Chip label="Sustainability Target: 75%" size="small" color="primary" sx={{ mt: 1 }} variant="outlined" />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    📈 Trigger Frequency (Model Drift)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • <strong>Baseline:</strong> ~23.5 events/year (Historical)<br />
                    • <strong>Warning:</strong> &gt;40 events/year suggests drift<br />
                    • <strong>Action:</strong> Rapid increase requires annual recalibration of thresholds.
                  </Typography>
                  <Chip label="Drift Threshold: >40/yr" size="small" color="warning" sx={{ mt: 1 }} variant="outlined" />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" fontWeight="bold" gutterBottom>
                    🎯 Avg. Severity (Basis Risk)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • <strong>Low (50-60%):</strong> Potential "False Positives" (Noise)<br />
                    • <strong>High (&gt;85%):</strong> Confirmed "True Positives" (Disaster)<br />
                    • <strong>Goal:</strong> High severity ensures payouts match actual farmer losses.
                  </Typography>
                  <Chip label="Valid Trigger: >60%" size="small" color="success" sx={{ mt: 1 }} variant="outlined" />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Advanced Visualizations Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Trigger Type Breakdown - NEW */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Trigger Type Breakdown</Typography>
              <Alert severity="info" sx={{ mb: 2, py: 0 }}>
                <Typography variant="caption">
                  <strong>Portfolio Composition:</strong> Shows which perils drive total financial exposure.
                </Typography>
              </Alert>
              <Box sx={{ height: 300 }}>
                <Plot
                  data={[
                    {
                      type: 'pie',
                      values: [
                        triggers.filter(t => t.triggerType === 'drought').reduce((sum, t) => sum + safeValue(t.payoutAmount), 0),
                        triggers.filter(t => t.triggerType === 'flood').reduce((sum, t) => sum + safeValue(t.payoutAmount), 0),
                        triggers.filter(t => t.triggerType === 'crop_failure').reduce((sum, t) => sum + safeValue(t.payoutAmount), 0)
                      ],
                      labels: ['Drought', 'Flood', 'Crop Failure'],
                      marker: {
                        colors: ['#D2691E', '#2196F3', '#FF9800'],
                        line: { color: 'white', width: 2 }
                      },
                      textinfo: 'label+percent',
                      textposition: 'inside',
                      hovertemplate: '<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>',
                      hole: 0.4
                    }
                  ]}
                  layout={{
                    autosize: true,
                    margin: { t: 20, b: 20, l: 20, r: 20 },
                    showlegend: true,
                    legend: { orientation: 'h', y: -0.1 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    font: { family: 'Roboto, sans-serif' }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                  config={{ displayModeBar: false }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Severity Distribution</Typography>
              <Alert
                severity="info"
                sx={{
                  mb: 2,
                  bgcolor: '#e3f2fd',
                  borderLeft: '4px solid #2196f3',
                  '& .MuiAlert-icon': { color: '#1976d2' }
                }}
              >
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                  <strong>Visual Check:</strong> A "fat tail" on the right (&gt;80%) indicates high-impact events. Left-skewed distributions suggest minor operational stresses.
                </Typography>
              </Alert>
              <Box sx={{ height: 300 }}>
                <Plot
                  data={[{
                    type: "histogram",
                    x: triggers.map(t => safeValue(t.severity) * 100),
                    marker: {
                      color: '#FF9800',
                      line: { color: '#FFFFFF', width: 1.5 }
                    },
                    opacity: 0.8,
                    xbins: { start: 0, end: 100, size: 10 }
                  }]}
                  layout={{
                    autosize: true,
                    margin: { t: 20, b: 40, l: 40, r: 20 },
                    xaxis: {
                      title: 'Severity (%)',
                      showgrid: false
                    },
                    yaxis: {
                      title: 'Frequency',
                      showgrid: true,
                      gridcolor: '#f0f0f0'
                    },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { family: 'Roboto, sans-serif' }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                  config={{ displayModeBar: false }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Financial Sustainability Tracker - Full Width Row */}
        <Grid item xs={12} md={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Financial Sustainability Tracker (Loss Ratio)</Typography>
              <Alert
                severity="warning"
                sx={{
                  mb: 2,
                  bgcolor: '#fff3e0',
                  borderLeft: '4px solid #ff9800',
                  '& .MuiAlert-icon': { color: '#f57c00' }
                }}
              >
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                  <strong>Sustainability Check:</strong> Blue line (Payouts) crossing the Red line (Premiums) indicates a Loss Ratio &gt; 100% (Unprofitable).
                </Typography>
              </Alert>
              <Box sx={{ height: 300 }}>
                {(() => {
                  // Sort triggers by date
                  const sortedTriggers = [...triggers].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

                  // Calculate Cumulative Payout
                  const dates = sortedTriggers.map(t => t.date);
                  const cumulativePayout = sortedTriggers.reduce((acc: number[], t) => {
                    const last = acc.length > 0 ? acc[acc.length - 1] : 0;
                    acc.push(last + safeValue(t.payoutAmount));
                    return acc;
                  }, []);

                  // SIMULATED PREMIUM MODEL (Linear accumulation for visual comparison)
                  // Assuming premiums are collected steadily to match avg expected loss * 1.3 (target 75% LR)
                  const totalActualPayout = cumulativePayout[cumulativePayout.length - 1] || 0;
                  const targetPremium = totalActualPayout * 1.3; // Target 75% Loss Ratio

                  // Create a linear premium line from start to end
                  const premiums = dates.map((_, i) => (targetPremium / dates.length) * (i + 1));

                  return (
                    <Plot
                      data={[
                        {
                          type: "scatter",
                          mode: 'lines',
                          name: 'Cumulative Payouts',
                          x: dates,
                          y: cumulativePayout,
                          fill: 'tozeroy',
                          line: { color: '#2196F3', width: 3, shape: 'hv' }, // Step chart often better for payouts
                          marker: { size: 4, color: '#1976D2' }
                        },
                        {
                          type: "scatter",
                          mode: 'lines',
                          name: 'Collected Premiums (Est)',
                          x: dates,
                          y: premiums,
                          line: { color: '#D32F2F', width: 2, dash: 'dash' },
                          marker: { size: 0 }
                        }
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 20, b: 40, l: 60, r: 20 },
                        xaxis: {
                          title: 'Date',
                          showgrid: false
                        },
                        yaxis: {
                          title: 'Amount (USD)',
                          showgrid: true,
                          gridcolor: '#f0f0f0',
                          tickprefix: '$'
                        },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { family: 'Roboto, sans-serif' },
                        hovermode: 'x unified',
                        legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }
                      }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                      config={{ displayModeBar: false }}
                    />
                  );
                })()}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid >

      {/* Regional Analysis Row - FIXED */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Regional Risk Comparison</Typography>
              <Alert severity="warning" sx={{ mb: 2, py: 0, bgcolor: '#fff3e0', borderLeft: '4px solid #ff9800' }}>
                <Typography variant="caption">
                  <strong>Geographic Diversification:</strong> Identifies high-concentration regions requiring risk mitigation strategies.
                </Typography>
              </Alert>
              <Box sx={{ height: 350 }}>
                {(() => {
                  // DYNAMIC: Use fetched locations from API
                  const getLocationName = (lat: number, lon: number): string => {
                    for (const loc of locations) {
                      if (Math.abs(loc.latitude - lat) < 0.5 && Math.abs(loc.longitude - lon) < 0.5) {
                        return loc.name;
                      }
                    }
                    return `Unknown (${lat.toFixed(1)}°, ${lon.toFixed(1)}°)`;
                  };

                  // Group triggers by location with name mapping
                  const locationClusters = new Map<string, { lat: number; lon: number; payout: number; count: number }>();

                  triggers.forEach(t => {
                    if (!t.locationLat || !t.locationLon) return;

                    // Get location name from fetched API data
                    const locationName = getLocationName(t.locationLat, t.locationLon);

                    if (!locationClusters.has(locationName)) {
                      locationClusters.set(locationName, {
                        lat: t.locationLat,
                        lon: t.locationLon,
                        payout: 0,
                        count: 0
                      });
                    }

                    const cluster = locationClusters.get(locationName)!;
                    cluster.payout += safeValue(t.payoutAmount);
                    cluster.count += 1;
                  });

                  // Convert to sorted array
                  const regionPayouts = Array.from(locationClusters.entries())
                    .map(([name, data]) => ({
                      name,
                      payout: data.payout,
                      count: data.count
                    }))
                    .sort((a, b) => b.payout - a.payout);

                  if (regionPayouts.length === 0) {
                    return <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
                      No location data available
                    </Typography>;
                  }

                  return (
                    <Plot
                      data={[
                        {
                          type: 'bar',
                          orientation: 'h',
                          y: regionPayouts.map(r => r.name),
                          x: regionPayouts.map(r => r.payout),
                          marker: {
                            color: '#009688',  // Solid Teal - distinct from other indicators
                            line: { color: '#00796B', width: 2 }
                          },
                          customdata: regionPayouts.map(r => r.count),
                          hovertemplate: '<b>%{y}</b><br>Total Payout: $%{x:,.0f}<br>Trigger Events: %{customdata}<extra></extra>'
                        }
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 20, b: 60, l: 140, r: 40 },
                        xaxis: {
                          title: 'Total Payout (USD)',
                          showgrid: true,
                          gridcolor: '#f0f0f0',
                          tickprefix: '$',
                          tickformat: ',.0f'
                        },
                        yaxis: {
                          title: '',
                          showgrid: false,
                          tickfont: { size: 13, family: 'Roboto, sans-serif', color: '#333' }
                        },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { family: 'Roboto, sans-serif' }
                      }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                      config={{ displayModeBar: false }}
                    />
                  );
                })()}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid >

      {/* Advanced Analytics Row - Seasonality & Scatter - NEW */}
      < Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Monthly Seasonality Heatmap */}
        < Grid item xs={12} md={6} >
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Monthly Seasonality Heatmap</Typography>
              <Alert severity="info" sx={{ mb: 2, py: 0, bgcolor: '#e3f2fd', borderLeft: '4px solid #2196F3' }}>
                <Typography variant="caption">
                  <strong>Seasonal Patterns:</strong> Reveals when triggers peak to adjust premiums and reserves pre-season.
                </Typography>
              </Alert>
              <Box sx={{ height: 400 }}>
                {(() => {
                  // Create month x location matrix for event frequency
                  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                  const locationNames = Array.from(new Set(
                    triggers.filter(t => t.locationLat && t.locationLon)
                      .map(t => {
                        for (const loc of locations) {
                          if (Math.abs(loc.latitude - t.locationLat!) < 0.5 &&
                            Math.abs(loc.longitude - t.locationLon!) < 0.5) {
                            return loc.name;
                          }
                        }
                        return null;
                      })
                      .filter(Boolean)
                  )).sort() as string[];

                  // Build heatmap data: z[location][month] = event count
                  const heatmapData = locationNames.map(locName => {
                    return months.map((_, monthIdx) => {
                      return triggers.filter(t => {
                        const triggerMonth = new Date(t.date).getMonth();
                        const triggerLoc = locations.find(loc =>
                          t.locationLat && t.locationLon &&
                          Math.abs(loc.latitude - t.locationLat) < 0.5 &&
                          Math.abs(loc.longitude - t.locationLon) < 0.5
                        );
                        return triggerMonth === monthIdx && triggerLoc?.name === locName;
                      }).length;
                    });
                  });

                  return (
                    <Plot
                      data={[
                        {
                          type: 'heatmap',
                          z: heatmapData,
                          x: months,
                          y: locationNames,
                          colorscale: [
                            [0, '#f0f0f0'],
                            [0.2, '#c3e6cb'],
                            [0.4, '#81c784'],
                            [0.6, '#4caf50'],
                            [0.8, '#2e7d32'],
                            [1, '#1b5e20']
                          ],
                          hovertemplate: '<b>%{y}</b><br>%{x}: %{z} events<extra></extra>',
                          showscale: true,
                          colorbar: {
                            title: 'Events',
                            titleside: 'right'
                          }
                        }
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 20, b: 60, l: 120, r: 80 },
                        xaxis: {
                          title: '',
                          showgrid: false
                        },
                        yaxis: {
                          title: '',
                          showgrid: false,
                          tickfont: { size: 12 }
                        },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { family: 'Roboto, sans-serif' }
                      }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                      config={{ displayModeBar: false }}
                    />
                  );
                })()}
              </Box>
            </CardContent>
          </Card>
        </Grid >

        {/* Payout vs Severity Scatter Plot */}
        < Grid item xs={12} md={6} >
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Payout vs Severity Analysis</Typography>
              <Alert severity="warning" sx={{ mb: 2, py: 0, bgcolor: '#fff3e0', borderLeft: '4px solid #ff9800' }}>
                <Typography variant="caption">
                  <strong>Basis Risk Detection:</strong> Outliers (high payout but low severity) suggest model miscalibration.
                </Typography>
              </Alert>
              <Box sx={{ height: 400 }}>
                {(() => {
                  // Group triggers by type for scatter plot
                  const droughtData = triggers.filter(t => t.triggerType === 'drought');
                  const floodData = triggers.filter(t => t.triggerType === 'flood');
                  const cropFailureData = triggers.filter(t => t.triggerType === 'crop_failure');

                  return (
                    <Plot
                      data={[
                        {
                          type: 'scatter',
                          mode: 'markers',
                          name: 'Drought',
                          x: droughtData.map(t => (t.severity || 0) * 100),
                          y: droughtData.map(t => t.payoutAmount),
                          marker: {
                            color: '#D2691E',
                            size: 8,
                            opacity: 0.7,
                            line: { color: '#8B4513', width: 1 }
                          },
                          hovertemplate: '<b>Drought</b><br>Severity: %{x:.1f}%<br>Payout: $%{y:,.0f}<extra></extra>'
                        },
                        {
                          type: 'scatter',
                          mode: 'markers',
                          name: 'Flood',
                          x: floodData.map(t => (t.severity || 0) * 100),
                          y: floodData.map(t => t.payoutAmount),
                          marker: {
                            color: '#2196F3',
                            size: 8,
                            opacity: 0.7,
                            line: { color: '#1976D2', width: 1 }
                          },
                          hovertemplate: '<b>Flood</b><br>Severity: %{x:.1f}%<br>Payout: $%{y:,.0f}<extra></extra>'
                        },
                        {
                          type: 'scatter',
                          mode: 'markers',
                          name: 'Crop Failure',
                          x: cropFailureData.map(t => (t.severity || 0) * 100),
                          y: cropFailureData.map(t => t.payoutAmount),
                          marker: {
                            color: '#FF9800',
                            size: 8,
                            opacity: 0.7,
                            line: { color: '#F57C00', width: 1 }
                          },
                          hovertemplate: '<b>Crop Failure</b><br>Severity: %{x:.1f}%<br>Payout: $%{y:,.0f}<extra></extra>'
                        }
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 20, b: 60, l: 70, r: 40 },
                        xaxis: {
                          title: 'Severity (%)',
                          showgrid: true,
                          gridcolor: '#f0f0f0',
                          range: [0, 100]
                        },
                        yaxis: {
                          title: 'Payout (USD)',
                          showgrid: true,
                          gridcolor: '#f0f0f0',
                          tickprefix: '$'
                        },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { family: 'Roboto, sans-serif' },
                        showlegend: true,
                        legend: { orientation: 'h', y: -0.15 }
                      }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                      config={{ displayModeBar: false }}
                    />
                  );
                })()}
              </Box>
            </CardContent>
          </Card>
        </Grid >
      </Grid >

      {/* Geographic Map */}
      < Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom>
            Geographic Trigger Distribution
          </Typography>
          <GeographicMap events={triggers} />
        </Grid>
      </Grid >

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
        {/* Table Removed as per Phase 3 Strategy - Key insights now provided via charts */}
      </Grid>
    </Box >
  )
}
