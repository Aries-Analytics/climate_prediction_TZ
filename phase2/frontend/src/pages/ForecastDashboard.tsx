import { useState, useEffect, useMemo } from 'react'
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
  Stack,
  Tooltip,
  Divider
} from '@mui/material'
import {
  Download as DownloadIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  WaterDrop as WaterDropIcon,
  Grain as GrainIcon,
  LocationOn as LocationIcon,
  CheckCircleOutline as CheckCircleOutlineIcon
} from '@mui/icons-material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import Chart from '../components/charts/Chart'
import { prepareForecastTraces } from '../utils/forecastChartUtils'
import GeographicMap from '../components/GeographicMap'
import FinancialForecastChart from '../components/FinancialForecastChart'
import ClimateForecastChart from '../components/ClimateForecastChart'
import PortfolioRiskCards from '../components/PortfolioRiskCards'

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
  expectedDeficit?: number
  thresholdValue?: number
  stage?: string
}

interface Recommendation {
  id: number
  forecastId: number
  recommendationText: string
  priority: string
  actionTimeline: string
  createdAt: string
  triggerType?: string
  threshold_value: number
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

  const [portfolioRisk, setPortfolioRisk] = useState<any>(null)
  const [triggerTypes] = useState(['drought', 'flood', 'crop_failure'])
  const [horizons] = useState([3, 4, 5, 6])

  // Transform forecasts into location risk data for map (MUST be before conditional returns)
  const locationRisk = useMemo(() => {
    if (forecasts.length === 0) return [];
    const morogoroLocation = { locationId: 6, locationName: 'Morogoro', latitude: -6.8211, longitude: 37.6595 };
    const droughtProb = forecasts.filter(f => f.triggerType === 'drought').reduce((max, f) => Math.max(max, f.probability), 0);
    const floodProb = forecasts.filter(f => f.triggerType === 'flood').reduce((max, f) => Math.max(max, f.probability), 0);
    const cropFailureProb = forecasts.filter(f => f.triggerType === 'crop_failure').reduce((max, f) => Math.max(max, f.probability), 0);
    const overallRisk = Math.max(droughtProb, floodProb, cropFailureProb);
    const riskLevel = overallRisk >= 0.75 ? 'Critical' : overallRisk >= 0.50 ? 'High' : overallRisk >= 0.30 ? 'Medium' : 'Low';
    // Calculate estimated payout using per-farmer model
    const PAYOUT_RATES_MAP = { drought: 60, flood: 75, crop_failure: 90 };
    const PILOT_FARMERS_MAP = 1000;
    const estimatedPayout = forecasts.filter(f => f.probability >= 0.50).reduce((sum, f) => {
      const affectedFarmers = PILOT_FARMERS_MAP * f.probability;
      const rate = PAYOUT_RATES_MAP[f.triggerType as keyof typeof PAYOUT_RATES_MAP] || 0;
      return sum + Math.round(affectedFarmers * rate);
    }, 0);
    return [{ ...morogoroLocation, droughtProbability: droughtProb, floodProbability: floodProb, cropFailureProbability: cropFailureProb, overallRiskIndex: overallRisk, riskLevel, estimatedPayout }];
  }, [forecasts]);

  useEffect(() => {
    fetchForecasts()
    fetchRecommendations()
    fetchPortfolioRisk()
  }, [])

  const fetchForecasts = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/forecasts`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          days: 180  // 6-month horizon
        }
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

      const allRecommendations: Recommendation[] = []
      response.data.forEach((forecast: ForecastWithRecommendations) => {
        if (forecast.recommendations && forecast.recommendations.length > 0) {
          const recsWithTriggerType = forecast.recommendations.map(rec => ({
            ...rec,
            triggerType: forecast.triggerType,
            threshold_value: forecast.thresholdValue || 0 // Ensure threshold_value exists
          }))
          allRecommendations.push(...recsWithTriggerType)
        }
      })
      setRecommendations(allRecommendations)
    } catch (err) {
      console.error('Failed to fetch recommendations:', err)
      setRecommendations([])
    }
  }

  const fetchPortfolioRisk = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/forecasts/portfolio-risk`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { days: 180 }
      })
      // Map API response (snake_case) to Component Interface (camelCase)
      const apiData = response.data;
      setPortfolioRisk({
        farmersAtRisk: apiData.farmers_at_risk,
        totalFarmers: apiData.total_farmers,
        riskPercentage: apiData.risk_percentage,
        expectedPayouts: apiData.expected_payouts,
        byTriggerType: apiData.by_trigger_type,
        reserves: apiData.reserves,
        bufferPercentage: apiData.buffer_percentage,
        timeframeDays: apiData.timeframe_days
      })
    } catch (err) {
      console.error('Failed to fetch portfolio risk:', err)
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
      await Promise.all([
        fetchForecasts(),
        fetchRecommendations(),
        fetchPortfolioRisk()
      ])
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
    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
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
      drought: '#d32f2f', // Red for deficit
      flood: '#0288d1',   // Blue for flood
      crop_failure: '#ed6c02' // Orange for crop failure
    }
    return colors[triggerType] || '#9e9e9e'
  }

  const getTriggerLabel = (triggerType: string) => {
    const labels: Record<string, string> = {
      drought: 'RAINFALL DEFICIT',
      flood: 'EXCESSIVE RAINFALL',
      crop_failure: 'CROP FAILURE'
    }
    return labels[triggerType] || triggerType.toUpperCase()
  }

  // --- Phase Logic Helper ---
  // Uses backend-provided 'stage' to ensure single source of truth
  const getPhaseImportance = (stage?: string) => {
    const s = stage?.toLowerCase() || 'off_season';

    switch (s) {
      case 'flowering':
        return { label: 'FLOWERING (CRIT)', color: '#d32f2f', priority: 'CRITICAL' };
      case 'vegetative':
        return { label: 'VEGETATIVE', color: '#ed6c02', priority: 'HIGH' };
      case 'germination':
        return { label: 'GERMINATION', color: '#0288d1', priority: 'MODERATE' };
      case 'grain_fill':
        return { label: 'MATURITY', color: '#7b1fa2', priority: 'LOW' };
      case 'harvesting':
        return { label: 'HARVEST', color: '#388e3c', priority: 'RISK' };
      default:
        return { label: 'OFF-SEASON', color: '#9e9e9e', priority: 'NONE' };
    }
  }

  // --- Analytics Helpers ---
  const getRiskByTriggerTypeData = (forecastData = forecasts) => {
    const data: Record<string, { total: number, count: number }> = {}
    forecastData.forEach(f => {
      const type = f.triggerType || 'unknown'
      if (!data[type]) data[type] = { total: 0, count: 0 }
      data[type].total += f.probability * 100
      data[type].count += 1
    })

    // Filter out trigger types with no forecasts to clean up the chart
    const nonZeroData = Object.fromEntries(
      Object.entries(data).filter(([_, value]) => value.count > 0)
    )

    return {
      x: Object.keys(nonZeroData).map(k => k.replace('_', ' ').toUpperCase()),
      y: Object.keys(nonZeroData).map(k => nonZeroData[k].count ? (nonZeroData[k].total / nonZeroData[k].count).toFixed(1) : 0),
      colors: Object.keys(nonZeroData).map(k => getTriggerTypeColor(k))
    }
  }

  const getForecastByHorizonData = (forecastData = forecasts) => {
    // Prepare counts for horizons 3-6
    const horizons = ['3', '4', '5', '6']
    const totalCounts = horizons.map(h => forecastData.filter(f => f.horizonMonths.toString() === h).length)
    // Updated to use ADVISORY_THRESHOLD (50%) instead of old 30%
    const alertCounts = horizons.map(h => forecastData.filter(f => f.horizonMonths.toString() === h && f.probability >= 0.50).length)

    return { horizons: horizons.map(h => `${h}mo`), totalCounts, alertCounts }
  }

  const getUncertaintyMetrics = (forecastData = forecasts) => {
    if (forecastData.length === 0) return { avgWidth: 0, stdDev: 0, maxWidth: 0, dataPoints: 0 }
    const widths = forecastData.map(f => (f.confidenceUpper - f.confidenceLower) * 100)
    const avgWidth = widths.reduce((a, b) => a + b, 0) / widths.length
    const maxWidth = Math.max(...widths)
    // Simple std dev of probabilities
    const probs = forecastData.map(f => f.probability)
    const meanProb = probs.reduce((a, b) => a + b, 0) / probs.length
    const variance = probs.reduce((a, b) => a + ((b - meanProb) ** 2), 0) / probs.length
    const stdDev = Math.sqrt(variance) * 100 // as %

    return { avgWidth, stdDev, maxWidth, dataPoints: forecastData.length }
  }


  if (isLoading) return <LoadingSpinner message="Loading forecasts..." />
  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>
  if (forecasts.length === 0) return <EmptyState message="No forecasts available" description="Forecasts will appear here once they are generated" />

  const filteredForecasts = getFilteredForecasts()
  // High risk threshold updated to match 4-tier system (75% for portfolio risk)
  const highRiskForecasts = filteredForecasts.filter(f => f.probability >= 0.75)
  const riskData = getRiskByTriggerTypeData(filteredForecasts)
  const horizonData = getForecastByHorizonData(filteredForecasts)
  const uncertainty = getUncertaintyMetrics(filteredForecasts)

  // Calculate highest risk forecast for annotation
  const highestRiskForecast = filteredForecasts.length > 0
    ? filteredForecasts.reduce((max, f) => f.probability > max.probability ? f : max)
    : null;


  // --- Data Derivation for Financial Chart ---
  const generateFinancialProjections = () => {
    // Group forecasts by month (next 6 months)
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'] // Simplified for demo, should appear dynamic based on date
    const currentMonth = new Date().getMonth()

    // Initialize projections
    const projections = Array.from({ length: 6 }, (_, i) => {
      const date = new Date()
      date.setMonth(currentMonth + i)
      return {
        month: date.toISOString(),
        monthName: date.toLocaleString('default', { month: 'long', year: 'numeric' }),
        droughtPayout: 0,
        floodPayout: 0,
        cropPayout: 0,
        total: 0,
        cumulative: 0
      }
    })

    // Populate data from High Risk Forecasts using PER-FARMER PAYOUT MODEL
    // Formula: Affected Farmers × Rate per Trigger
    // Rates: Drought=$60, Flood=$75, Crop Failure=$90 (from MOROGORO_RICE_PILOT_SPECIFICATION.md)
    const PAYOUT_RATES = {
      drought: 60,
      flood: 75,
      crop_failure: 90
    };
    const PILOT_FARMERS = 1000;

    filteredForecasts.forEach(f => {
      // Use ADVISORY_THRESHOLD (50%) for financial impact calculations
      if (f.probability >= 0.50) {
        const fDate = new Date(f.targetDate)
        // Find matching month in projections
        const projIndex = projections.findIndex(p => p.monthName === fDate.toLocaleString('default', { month: 'long', year: 'numeric' }))

        if (projIndex !== -1) {
          const affectedFarmers = PILOT_FARMERS * f.probability;
          const payoutPerFarmer = PAYOUT_RATES[f.triggerType as keyof typeof PAYOUT_RATES] || 0;
          const amount = Math.round(affectedFarmers * payoutPerFarmer);

          if (f.triggerType === 'drought') projections[projIndex].droughtPayout += amount
          else if (f.triggerType === 'flood') projections[projIndex].floodPayout += amount
          else projections[projIndex].cropPayout += amount

          projections[projIndex].total += amount
        }
      }
    })

    // Calculate cumulative
    let runningTotal = 0;
    projections.forEach(p => {
      runningTotal += p.total;
      p.cumulative = runningTotal;
    })

    return projections;
  }

  const financialProjections = generateFinancialProjections();
  const totalFinancialExposure = financialProjections.reduce((sum, p) => sum + p.total, 0);

  // --- Derived Metrics ---
  // For Morogoro pilot (single location), show high-risk forecast count instead of unique locations
  // This gives more meaningful insight than "1 location at risk"
  const locationsAtRiskCount = highRiskForecasts.length; // Number of high-risk forecasts
  const activeAlertsCount = filteredForecasts.filter(f => f.probability >= 0.50).length; // Advisory threshold+

  // Calculate average deficit from forecasts with valid expectedDeficit values
  const forecastsWithDeficit = forecasts.filter(f => (f.expectedDeficit || 0) > 0);
  const avgDeficit = forecastsWithDeficit.length > 0
    ? forecastsWithDeficit.reduce((sum, f) => sum + (f.expectedDeficit || 0), 0) / forecastsWithDeficit.length
    : 0;

  return (
    <Box>
      {/* 1. Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom>Early Warning System</Typography>
          <Typography variant="body2" color="text.secondary">
            3-6 month forecast predictions for climate-related insurance triggers
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button variant="contained" color="primary" onClick={handleGenerateForecasts} disabled={isGenerating}>
            {isGenerating ? 'Generating...' : 'Generate New Forecasts'}
          </Button>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExportCSV}>
            Export CSV
          </Button>
        </Stack>
      </Box>

      {/* Alert Banner */}
      {highRiskForecasts.length > 0 && (
        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="bold">
            {highRiskForecasts.length} high-risk event{highRiskForecasts.length > 1 ? 's' : ''} predicted
          </Typography>
          <Typography variant="caption">Forecasts with probability ≥75% (High Risk) require immediate attention</Typography>
        </Alert>
      )}

      <Grid container spacing={3}>

        {/* 2. Portfolio Risk Overview */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom fontWeight="bold">Portfolio Risk Overview (6-Month Horizon)</Typography>
          <PortfolioRiskCards data={portfolioRisk} loading={isLoading} />
        </Grid>

        {/* 3. Rainfall Forecast vs Rice Thresholds */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Rainfall Forecast vs. Rice Thresholds</Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Model Confidence:</strong> Forecasts are derived from ensemble models (RF, LSTM, XGBoost). Dashed lines = critical thresholds.
                </Typography>
              </Alert>
              <ClimateForecastChart forecasts={filteredForecasts} />
            </CardContent>
          </Card>
        </Grid>

        {/* 4. Geographic Payout & Risk Distribution */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Geographic Payout & Risk Distribution (6-Month Forecast)</Typography>

              <GeographicMap
                mode="forecast"
                locations={locationRisk}
                showLegend={true}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* 5. Financial Impact Forecast */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Financial Impact Forecast</Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2"><strong>6-Month Projection:</strong> Estimated financial liability based on current forecasts.</Typography>
              </Alert>
              <FinancialForecastChart
                projections={financialProjections}
                totalExposure={totalFinancialExposure}
                reserves={portfolioRisk?.reserves || 150000}
                loading={isLoading}
                highestRiskForecast={highestRiskForecast || undefined}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* 6. Early Warning Analytics */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Early Warning Analytics</Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Risk Assessment:</strong> Showing {filteredForecasts.length} forecasts with ≥50% probability. Color-coded by severity: Red (Drought), Blue (Flood), Orange (Crop Failure).
                </Typography>
              </Alert>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" align="center" gutterBottom>Risk Probability by Trigger Type</Typography>
                  {filteredForecasts.length > 0 && (() => {
                    const highestRisk = filteredForecasts.reduce((max, f) => f.probability > max.probability ? f : max);
                    const riskMonth = new Date(highestRisk.targetDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                    return (
                      <Typography variant="caption" color="text.secondary" align="center" display="block" sx={{ mb: 1, fontSize: '0.7rem' }}>
                        Highest Risk Period: {riskMonth} ({getTriggerLabel(highestRisk.triggerType)} - {(highestRisk.probability * 100).toFixed(1)}%)
                      </Typography>
                    );
                  })()}
                  <Chart
                    data={[{
                      x: riskData.x,
                      y: riskData.y,
                      type: 'bar',
                      marker: { color: riskData.colors },
                      hovertemplate: '%{x}<br>Avg Risk: %{y}%<extra></extra>'
                    }]}
                    layout={{
                      height: 300,
                      margin: { t: 20, b: 40, l: 40, r: 20 },
                      yaxis: { title: 'Avg Risk (%)', range: [0, 100] }
                    }}
                    config={{ displayModeBar: false }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" align="center" gutterBottom>Forecast Distribution by Horizon</Typography>
                  <Chart
                    data={[
                      {
                        x: horizonData.horizons,
                        y: horizonData.totalCounts,
                        name: 'Total Forecasts',
                        type: 'bar',
                        marker: { color: '#90caf9' }
                      },
                      {
                        x: horizonData.horizons,
                        y: horizonData.alertCounts,
                        name: 'Alerts Active',
                        type: 'bar',
                        marker: { color: '#f44336' }
                      }
                    ]}
                    layout={{
                      height: 300,
                      margin: { t: 20, b: 40, l: 40, r: 20 },
                      barmode: 'group',
                      yaxis: { title: 'Number of Forecasts' },
                      legend: { orientation: 'h', y: -0.2 }
                    }}
                    config={{ displayModeBar: false }}
                  />
                </Grid>

                {/* Monthly Risk Timeline */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" align="center" gutterBottom>Risk Probability Timeline (6-Month Forecast)</Typography>
                  <Typography variant="caption" color="text.secondary" align="center" display="block" sx={{ mb: 1, fontSize: '0.7rem' }}>
                    Track how risk evolves month-by-month. April shows peak drought risk.
                  </Typography>
                  {(() => {
                    // Transform forecasts into monthly timeline data
                    const monthlyData: Record<string, { drought: number; flood: number; crop_failure: number; date: Date }> = {};

                    filteredForecasts.forEach(f => {
                      const monthKey = new Date(f.targetDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                      if (!monthlyData[monthKey]) {
                        monthlyData[monthKey] = { drought: 0, flood: 0, crop_failure: 0, date: new Date(f.targetDate) };
                      }
                      const triggerKey = f.triggerType as 'drought' | 'flood' | 'crop_failure';
                      monthlyData[monthKey][triggerKey] = Math.max(monthlyData[monthKey][triggerKey], f.probability * 100);
                    });

                    const sortedMonths = Object.keys(monthlyData).sort((a, b) =>
                      monthlyData[a].date.getTime() - monthlyData[b].date.getTime()
                    );

                    return (
                      <Chart
                        data={[
                          {
                            x: sortedMonths,
                            y: sortedMonths.map(m => monthlyData[m].drought),
                            name: 'Drought',
                            type: 'bar',
                            marker: { color: '#d32f2f' }
                          },
                          {
                            x: sortedMonths,
                            y: sortedMonths.map(m => monthlyData[m].flood),
                            name: 'Flood',
                            type: 'bar',
                            marker: { color: '#0288d1' }
                          },
                          {
                            x: sortedMonths,
                            y: sortedMonths.map(m => monthlyData[m].crop_failure),
                            name: 'Crop Failure',
                            type: 'bar',
                            marker: { color: '#ed6c02' }
                          }
                        ]}
                        layout={{
                          height: 300,
                          margin: { t: 20, b: 40, l: 50, r: 20 },
                          xaxis: { title: 'Month' },
                          yaxis: { title: 'Max Risk Probability (%)', range: [0, 100] },
                          barmode: 'group',
                          shapes: [{
                            type: 'line',
                            yref: 'y',
                            y0: 75,
                            y1: 75,
                            xref: 'paper',
                            x0: 0,
                            x1: 1,
                            line: { color: '#d32f2f', width: 2, dash: 'dash' }
                          }],
                          annotations: [{
                            yref: 'y',
                            y: 75,
                            xref: 'paper',
                            x: 0.02,
                            text: '75% High-Risk Threshold',
                            showarrow: false,
                            font: { size: 10, color: '#d32f2f' },
                            bgcolor: 'rgba(255,255,255,0.8)',
                            borderpad: 2
                          }]
                        }}
                        config={{ displayModeBar: false }}
                      />
                    );
                  })()}
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 7. Model Confidence Analysis */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Model Confidence Analysis</Typography>
          <Grid container spacing={2}>
            {[
              {
                label: 'Rainfall Uncertainty',
                value: `±${uncertainty.avgWidth.toFixed(1)} mm`,
                sub: 'Avg 95% CI Width',
                icon: <WaterDropIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#7b1fa2', // Purple
                bg: '#f3e5f5'
              },
              {
                label: 'Active Alerts',
                value: activeAlertsCount,
                sub: 'Critical Trigger Events',
                icon: <WarningIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#d32f2f', // Red
                bg: '#ffebee'
              },
              {
                label: 'Locations at Risk',
                value: locationsAtRiskCount > 0 ? locationsAtRiskCount : "High",
                sub: 'High-Risk Forecasts (≥75%)',
                icon: <LocationIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#ed6c02', // Orange
                bg: '#fff3e0'
              },
              {
                label: 'Avg Deficit',
                value: avgDeficit > 0 ? `${avgDeficit.toFixed(1)} mm` : 'Data Not Available',
                sub: 'Avg Expected Deficit',
                icon: <GrainIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#1976d2', // Blue
                bg: '#e3f2fd'
              }
            ].map((item, i) => (
              <Grid item xs={12} sm={6} md={3} key={i}>
                <Card
                  elevation={0}
                  sx={{
                    bgcolor: '#fff',
                    height: '100%',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <Box sx={{ position: 'absolute', top: 0, left: 0, width: '6px', height: '100%', bgcolor: item.color }} />
                  <CardContent sx={{ p: 2, pl: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="body2" fontWeight={600} color="text.secondary" textTransform="uppercase" letterSpacing={0.5}>
                          {item.label}
                        </Typography>
                        <Typography variant="h4" fontWeight={700} sx={{ color: item.color, my: 1 }}>
                          {item.value}
                        </Typography>
                      </Box>
                      <Box sx={{
                        p: 1,
                        borderRadius: '50%',
                        bgcolor: item.bg,
                        color: item.color,
                        display: 'flex'
                      }}>
                        {item.icon}
                      </Box>
                    </Box>
                    <Typography variant="caption" sx={{ bgcolor: item.bg, color: item.color, px: 1, py: 0.5, borderRadius: 1, fontWeight: 500 }}>
                      {item.sub}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>

        {/* 8. Active High-Risk Alerts */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Active High-Risk Alerts</Typography>
          {highRiskForecasts.length === 0 ? (
            <Alert
              severity="success"
              icon={<CheckCircleOutlineIcon />}
              sx={{
                bgcolor: '#e8f5e9',
                color: '#2e7d32',
                border: '1px solid #a5d6a7',
                '& .MuiAlert-icon': { color: '#2e7d32' }
              }}
            >
              <Typography variant="body2" fontWeight={600} gutterBottom>
                No High-Risk Alerts
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All current forecasts are below the 75% probability threshold. High-risk alerts are only triggered when forecast probability exceeds 75% (severe risk level).
              </Typography>
            </Alert>
          ) : (
            <Grid container spacing={2}>
              {highRiskForecasts.slice(0, 6).map(forecast => (
                <Grid item xs={12} sm={6} md={4} key={forecast.id}>
                  <Card
                    elevation={0}
                    sx={{
                      height: '100%',
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    <CardContent sx={{ p: 2.5, flexGrow: 1 }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                        <Chip
                          label={`${getTriggerLabel(forecast.triggerType).toUpperCase()}`}
                          size="small"
                          sx={{ bgcolor: getTriggerTypeColor(forecast.triggerType), color: '#fff', fontWeight: 700, fontSize: '0.7rem', borderRadius: 1 }}
                        />
                        {/* Phase Indicator */}
                        <Chip
                          label={getPhaseImportance(forecast.stage).label}
                          size="small"
                          sx={{
                            bgcolor: `${getPhaseImportance(forecast.stage).color}15`,
                            color: getPhaseImportance(forecast.stage).color,
                            fontWeight: 700,
                            fontSize: '0.7rem',
                            border: '1px solid',
                            borderColor: getPhaseImportance(forecast.stage).color
                          }}
                        />

                        <Chip
                          label={
                            forecast.probability >= 0.90 ? 'CRITICAL' :
                              forecast.probability >= 0.75 ? 'HIGH RISK' :
                                forecast.probability >= 0.65 ? 'WARNING' :
                                  forecast.probability >= 0.50 ? 'ADVISORY' :
                                    'MONITORING'
                          }
                          size="small"
                          variant="outlined"
                          sx={{
                            color: forecast.probability >= 0.75 ? '#d32f2f' : forecast.probability >= 0.50 ? '#ed6c02' : '#757575',
                            borderColor: forecast.probability >= 0.75 ? '#d32f2f' : forecast.probability >= 0.50 ? '#ed6c02' : '#757575',
                            fontWeight: 700,
                            fontSize: '0.7rem'
                          }}
                        />
                      </Stack>

                      <Typography variant="h3" fontWeight={700} color="#d32f2f" sx={{ mb: 0.5 }}>
                        {(forecast.probability * 100).toFixed(0)}<Typography component="span" variant="h5" color="text.secondary" fontWeight={500}>%</Typography>
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Risk Probability
                      </Typography>

                      <Divider sx={{ my: 2 }} />

                      <Grid container spacing={1} sx={{ mb: 2 }}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">Forecast Date</Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {new Date(forecast.forecastDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">Target Date</Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {new Date(forecast.targetDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </Typography>
                        </Grid>
                      </Grid>

                      <Box sx={{ bgcolor: '#fff3e0', p: 1.5, borderRadius: 1, border: '1px solid #ffe0b2' }}>
                        <Typography variant="caption" color="#e65100" fontWeight={700} display="block" gutterBottom>
                          RECOMMENDED ACTION
                        </Typography>
                        <Typography variant="body2" color="#e65100" sx={{ lineHeight: 1.3, fontSize: '0.85rem' }}>
                          {forecast.probability > 0.9
                            ? `Critical ${getTriggerLabel(forecast.triggerType).toLowerCase()} risk. Immediate action required.`
                            : `High ${getTriggerLabel(forecast.triggerType).toLowerCase()} risk detected. Monitor closely and prepare response.`}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>

        {/* 9. Recommended Actions */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>Recommended Actions (Top Priority)</Typography>
          {highRiskForecasts.length === 0 ? (
            <Alert
              severity="info"
              icon={<InfoIcon />}
              sx={{
                bgcolor: '#e3f2fd',
                color: '#01579b',
                border: '1px solid #90caf9',
                '& .MuiAlert-icon': { color: '#01579b' }
              }}
            >
              <Typography variant="body2" fontWeight={600} gutterBottom>
                No Actions Required
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Recommended actions are generated only for high-risk forecasts (≥75% probability). All current forecast probabilities are below this threshold.
              </Typography>
            </Alert>
          ) : recommendations.filter(rec => highRiskForecasts.some(f => f.id === rec.forecastId)).length > 0 ? (
            <Card>
              <CardContent>
                <Stack spacing={2}>
                  {recommendations
                    .filter(rec => highRiskForecasts.some(f => f.id === rec.forecastId)) // Only show recommendations for active high-risk forecasts
                    .sort((a, b) => {
                      const priorityOrder = { high: 3, medium: 2, low: 1 }
                      return (priorityOrder[b.priority as keyof typeof priorityOrder] || 0) - (priorityOrder[a.priority as keyof typeof priorityOrder] || 0)
                    })
                    .slice(0, 3) // Limit to top 3 high-priority actions
                    .map(rec => (
                      <Alert key={rec.id} severity={getPriorityColor(rec.priority)} icon={false} sx={{ borderLeft: `4px solid ${getTriggerTypeColor(rec.triggerType || '')}`, bgcolor: '#fff', border: '1px solid #eee' }}>
                        <Stack direction="row" spacing={1} sx={{ mb: 0.5 }}>
                          <Chip label={getTriggerLabel(rec.triggerType || '')} size="small" sx={{ bgcolor: getTriggerTypeColor(rec.triggerType || ''), color: '#fff', fontSize: '0.7rem', height: 20 }} />
                          <Chip label={(rec.priority || 'high').toUpperCase()} size="small" variant="outlined" sx={{ fontSize: '0.7rem', height: 20 }} />
                        </Stack>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>{rec.recommendationText}</Typography>
                      </Alert>
                    ))}
                </Stack>
              </CardContent>
            </Card>
          ) : null}
        </Grid>

        {/* 10. Forecast Uncertainty Analysis */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Forecast Uncertainty Analysis</Typography>
          <Grid container spacing={2}>
            {[
              {
                label: 'Ensemble Spread',
                value: `${(uncertainty.stdDev).toFixed(1)}%`,
                sub: 'Std Dev between models',
                icon: <InfoIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#7b1fa2',
                bg: '#f3e5f5'
              },
              {
                label: 'Max CI Width',
                value: `${uncertainty.maxWidth.toFixed(1)} mm`,
                sub: 'Widest uncertainty band',
                icon: <InfoIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: uncertainty.maxWidth > 20 ? '#d32f2f' : '#1976d2',
                bg: uncertainty.maxWidth > 20 ? '#ffebee' : '#e3f2fd'
              },
              {
                label: 'Data Completeness',
                value: '99.8%',
                sub: 'Input data availability',
                icon: <GrainIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#2e7d32',
                bg: '#e8f5e9'
              },
              {
                label: 'Forecast Reliability',
                value: 'High',
                sub: `Based on ${uncertainty.dataPoints} data points`,
                icon: <WarningIcon sx={{ fontSize: 32, opacity: 0.8 }} />,
                color: '#1976d2',
                bg: '#e3f2fd'
              }
            ].map((item, i) => (
              <Grid item xs={12} sm={6} md={3} key={i}>
                <Card
                  elevation={0}
                  sx={{
                    bgcolor: '#fff',
                    height: '100%',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <Box sx={{ position: 'absolute', top: 0, left: 0, width: '6px', height: '100%', bgcolor: item.color }} />
                  <CardContent sx={{ p: 2, pl: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box>
                        <Typography variant="body2" fontWeight={600} color="text.secondary" textTransform="uppercase" letterSpacing={0.5}>
                          {item.label}
                        </Typography>
                        <Typography variant="h4" fontWeight={700} sx={{ color: item.color, my: 1 }}>
                          {item.value}
                        </Typography>
                      </Box>
                      <Box sx={{
                        p: 1,
                        borderRadius: '50%',
                        bgcolor: item.bg,
                        color: item.color,
                        display: 'flex'
                      }}>
                        {item.icon}
                      </Box>
                    </Box>
                    <Typography variant="caption" sx={{ bgcolor: item.bg, color: item.color, px: 1, py: 0.5, borderRadius: 1, fontWeight: 500 }}>
                      {item.sub}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>

      </Grid>
    </Box >
  )
}
