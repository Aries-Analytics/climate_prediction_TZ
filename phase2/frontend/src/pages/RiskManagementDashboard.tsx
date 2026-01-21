import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Chip,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import KPICard from '../components/common/KPICard'
import Chart from '../components/charts/Chart'
import { PortfolioMetrics, ScenarioResult } from '../types'
import WarningIcon from '@mui/icons-material/Warning'

// Pre-defined Scenario Templates (Based on ARC Africa & Industry Standards)
const SCENARIO_TEMPLATES = [
  { name: 'Custom Scenario', rainfall: 0, temperature: 0, description: 'Define your own parameters' },
  { name: 'Moderate Drought (1-in-10 year)', rainfall: 30, temperature: 1, description: 'Typical dry season stress' },
  { name: 'Severe Drought (1-in-25 year)', rainfall: 50, temperature: 2, description: 'Significant yield impact expected' },
  { name: 'Extreme Drought (El Niño)', rainfall: 55, temperature: 2.5, description: 'Similar to 2015/16 East Africa drought' },
  { name: 'Flash Drought', rainfall: 70, temperature: 4, description: 'Rapid onset during flowering stage' },
  { name: 'Moderate Flood (La Niña)', rainfall: -40, temperature: 0, description: 'Waterlogging + delayed planting' },
  { name: 'Severe Flood', rainfall: -80, temperature: -1, description: 'Prolonged inundation, crop loss' },
  { name: 'Heat Stress', rainfall: 0, temperature: 4, description: 'Heat wave during flowering (no water stress)' },
  { name: 'Sequential Shock', rainfall: 40, temperature: 1.5, description: 'Drought followed by flood' },
  { name: 'Climate Change (+1.5°C)', rainfall: 15, temperature: 1.5, description: 'IPCC RCP 4.5 scenario (2050)' },
  { name: 'Climate Change (+3°C)', rainfall: 25, temperature: 3, description: 'IPCC RCP 8.5 scenario (2050)' }
]

export default function RiskManagementDashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioMetrics | null>(null)
  const [scenarioResults, setScenarioResults] = useState<ScenarioResult[]>([])
  const [recommendations, setRecommendations] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scenarioDialogOpen, setScenarioDialogOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(0) // Index of template
  const [scenarioName, setScenarioName] = useState('')
  const [rainfallReduction, setRainfallReduction] = useState(0)
  const [temperatureIncrease, setTemperatureIncrease] = useState(0)

  // Auto-populate parameters when template changes
  const handleTemplateChange = (templateIndex: number) => {
    setSelectedTemplate(templateIndex)
    const template = SCENARIO_TEMPLATES[templateIndex]
    setScenarioName(template.name)
    setRainfallReduction(template.rainfall)
    setTemperatureIncrease(template.temperature)
  }

  useEffect(() => {
    fetchPortfolioData()
    fetchRecommendations()
  }, [])

  const fetchPortfolioData = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/risk/portfolio`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setPortfolio(response.data)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch portfolio data')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchRecommendations = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/risk/recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setRecommendations(response.data)
    } catch (err) {
      console.error('Failed to fetch recommendations:', err)
    }
  }

  const handleRunScenario = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/risk/scenario`,
        {
          scenarioName,
          parameters: {
            rainfall_reduction: rainfallReduction / 100, // Convert percentage to decimal
            temperature_increase: temperatureIncrease
          }
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setScenarioResults([...scenarioResults, response.data])
      setScenarioDialogOpen(false)
      // Reset form
      setSelectedTemplate(0)
      setScenarioName('')
      setRainfallReduction(0)
      setTemperatureIncrease(0)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to run scenario')
    }
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading risk management data..." />
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (!portfolio) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No portfolio data available</Alert>
      </Box>
    )
  }

  const getLossRatioStatus = (ratio: number): 'success' | 'warning' | 'error' => {
    if (ratio <= 0.6) return 'success'
    if (ratio <= 0.8) return 'warning'
    return 'error'
  }

  // Scenario comparison chart
  const scenarioChartData = scenarioResults.length > 0 ? [
    {
      x: scenarioResults.map(s => s.scenarioName),
      y: scenarioResults.map(s => s.lossRatio),
      name: 'Loss Ratio',
      type: 'bar' as const,
      marker: { color: '#ff9800' }
    },
    {
      x: scenarioResults.map(s => s.scenarioName),
      y: scenarioResults.map(s => s.triggerProbability),
      name: 'Trigger Probability',
      type: 'bar' as const,
      marker: { color: '#2196f3' }
    }
  ] : []

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Risk Management Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Monitor portfolio risk, run scenarios, and get recommendations
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Portfolio Metrics */}
        <Grid item xs={12} md={3}>
          <KPICard
            title="Total Premium Income"
            value={`$${(portfolio.totalPremiumIncome || 0).toLocaleString()}`}
            status="success"
            subtitle="Annual (1000 farmers × $75)"
            insight="Revenue from all active insurance policies in the Morogoro pilot."
            insightSeverity="info"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <KPICard
            title="Expected Payouts"
            value={`$${(portfolio.expectedPayouts || 0).toLocaleString()}`}
            status={
              (portfolio.expectedPayouts || 0) > (portfolio.reserves || 0) * 0.8 ? 'error' :
                (portfolio.expectedPayouts || 0) > (portfolio.reserves || 0) * 0.5 ? 'warning' :
                  'success'
            }
            subtitle="6-Month Projection"
            insight={
              (portfolio.expectedPayouts || 0) > (portfolio.reserves || 0)
                ? "⚠️ Payouts exceed reserves - urgent action required"
                : "Projected payouts based on high-risk forecasts (≥75% probability)"
            }
            insightSeverity={
              (portfolio.expectedPayouts || 0) > (portfolio.reserves || 0) ? 'error' :
                (portfolio.expectedPayouts || 0) > (portfolio.reserves || 0) * 0.8 ? 'warning' :
                  'success'
            }
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <KPICard
            title="Loss Ratio"
            value={`${((portfolio.lossRatio || 0) * 100).toFixed(1)}%`}
            status={getLossRatioStatus(portfolio.lossRatio || 0)}
            subtitle={
              (portfolio.lossRatio || 0) > 0.8 ? 'CRITICAL - Unsustainable' :
                (portfolio.lossRatio || 0) > 0.6 ? 'At Risk - Monitor' :
                  'Healthy Range'
            }
            insight={
              (portfolio.lossRatio || 0) > 0.8
                ? "🔴 Payouts exceed 80% of premiums - consider reserve increase or coverage adjustment"
                : (portfolio.lossRatio || 0) > 0.6
                  ? "🟡 Approaching break-even - monitor forecast trends closely"
                  : "🟢 Sustainable ratio - portfolio health good"
            }
            insightSeverity={getLossRatioStatus(portfolio.lossRatio || 0)}
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <KPICard
            title="Number of Policies"
            value={portfolio.numberOfPolicies || 0}
            status="success"
            subtitle="Morogoro Pilot"
            insight="Active insurance policies covering 1000 smallholder rice farmers in Kilombero Basin."
            insightSeverity="info"
          />
        </Grid>

        {/* Early Warnings */}
        {recommendations.length > 0 && (
          <Grid item xs={12}>
            <Alert severity="warning" icon={<WarningIcon />}>
              <Typography variant="subtitle2" gutterBottom>
                Risk Alerts & Recommendations
              </Typography>
              <List dense>
                {recommendations.slice(0, 5).map((rec, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={rec} />
                  </ListItem>
                ))}
              </List>
            </Alert>
          </Grid>
        )}

        {/* Scenario Analysis */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Scenario Analysis
                </Typography>
                <Button
                  variant="contained"
                  onClick={() => setScenarioDialogOpen(true)}
                >
                  Run New Scenario
                </Button>
              </Box>

              {scenarioResults.length > 0 ? (
                <>
                  <Chart
                    data={scenarioChartData}
                    layout={{
                      height: 400,
                      barmode: 'group',
                      xaxis: { title: 'Scenario' },
                      yaxis: { title: 'Value' },
                      autosize: true
                    }}
                    config={{
                      responsive: true
                    }}
                  />
                  <Box sx={{ mt: 2 }}>
                    {scenarioResults.map((result, index) => (
                      <Card key={index} sx={{ mb: 1, bgcolor: 'background.default' }}>
                        <CardContent>
                          <Typography variant="subtitle1" gutterBottom>
                            {result.scenarioName}
                          </Typography>
                          <Grid container spacing={2}>
                            <Grid item xs={4}>
                              <Typography variant="body2" color="text.secondary">
                                Expected Payouts
                              </Typography>
                              <Typography variant="h6">
                                ${result.expectedPayouts.toLocaleString()}
                              </Typography>
                            </Grid>
                            <Grid item xs={4}>
                              <Typography variant="body2" color="text.secondary">
                                Loss Ratio
                              </Typography>
                              <Typography variant="h6">
                                {(result.lossRatio * 100).toFixed(1)}%
                              </Typography>
                            </Grid>
                            <Grid item xs={4}>
                              <Typography variant="body2" color="text.secondary">
                                Trigger Probability
                              </Typography>
                              <Typography variant="h6">
                                {(result.triggerProbability * 100).toFixed(1)}%
                              </Typography>
                            </Grid>
                          </Grid>
                          <Box sx={{ mt: 1 }}>
                            <Chip
                              label={result.impact}
                              color={
                                result.impact.toLowerCase().includes('high') ? 'error' :
                                  result.impact.toLowerCase().includes('medium') ? 'warning' :
                                    'success'
                              }
                              size="small"
                            />
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
                  No scenarios run yet. Click "Run New Scenario" to start.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Exposure
              </Typography>
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h3" color="primary">
                  ${(portfolio.totalExposure || 0).toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Risk Exposure
                </Typography>
              </Box>
              <Alert severity="info" sx={{ mt: 2, py: 0.5, bgcolor: '#e3f2fd' }}>
                <Typography variant="body2">
                  <strong>Worst-case scenario:</strong> All 1000 farmers affected by crop failure ($90/farmer).
                  Current reserves: ${(portfolio.reserves || 0).toLocaleString()}
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* Sustainability Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sustainability Status
              </Typography>
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Chip
                  label={
                    portfolio.lossRatio <= 0.6 ? 'Sustainable' :
                      portfolio.lossRatio <= 0.8 ? 'Monitor' :
                        'At Risk'
                  }
                  color={getLossRatioStatus(portfolio.lossRatio)}
                  sx={{ fontSize: '1.2rem', py: 3, px: 2 }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Based on current loss ratio of {((portfolio.lossRatio || 0) * 100).toFixed(1)}%
                </Typography>
              </Box>
              <Alert
                severity={getLossRatioStatus(portfolio.lossRatio || 0)}
                sx={{ mt: 2, py: 0.5 }}
              >
                <Typography variant="body2">
                  {(portfolio.lossRatio || 0) <= 0.6
                    ? '✅ Portfolio is financially sustainable with healthy reserve margins'
                    : (portfolio.lossRatio || 0) <= 0.8
                      ? '⚠️ Monitor closely - approaching break-even threshold'
                      : '🚨 Portfolio at risk - immediate reserve increase or coverage reduction needed'}
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Scenario Dialog */}
      <Dialog open={scenarioDialogOpen} onClose={() => setScenarioDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Scenario Analysis</DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          {/* Scenario Template Selector */}
          <FormControl fullWidth margin="normal">
            <InputLabel>Select Scenario Template</InputLabel>
            <Select
              value={selectedTemplate}
              label="Select Scenario Template"
              onChange={(e) => handleTemplateChange(e.target.value as number)}
            >
              {SCENARIO_TEMPLATES.map((template, index) => (
                <MenuItem key={index} value={index}>
                  {template.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1, mb: 2 }}>
            {SCENARIO_TEMPLATES[selectedTemplate].description}
          </Typography>

          <TextField
            label="Scenario Name"
            fullWidth
            margin="normal"
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            placeholder="e.g., Severe Drought, El Niño Event"
            helperText="Give this scenario a descriptive name"
          />

          <Box sx={{ mt: 3, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Rainfall Reduction: {rainfallReduction}%
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                Normal (0%)
              </Typography>
              <Slider
                value={rainfallReduction}
                onChange={(_, value) => setRainfallReduction(value as number)}
                min={0}
                max={80}
                step={5}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 30, label: '30%' },
                  { value: 50, label: '50%' },
                  { value: 80, label: '80%' }
                ]}
                valueLabelDisplay="auto"
                sx={{ flexGrow: 1 }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 100 }}>
                Severe (80%)
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              How much less rainfall than normal? (e.g., 30% = drought conditions)
            </Typography>
          </Box>

          <Box sx={{ mt: 3, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Temperature Increase: +{temperatureIncrease}°C
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                Normal (0°C)
              </Typography>
              <Slider
                value={temperatureIncrease}
                onChange={(_, value) => setTemperatureIncrease(value as number)}
                min={0}
                max={5}
                step={0.5}
                marks={[
                  { value: 0, label: '0°C' },
                  { value: 2, label: '2°C' },
                  { value: 4, label: '4°C' },
                  { value: 5, label: '5°C' }
                ]}
                valueLabelDisplay="auto"
                sx={{ flexGrow: 1 }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 100 }}>
                Extreme (+5°C)
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              How much warmer than normal? (e.g., +2°C = heat stress conditions)
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScenarioDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRunScenario} variant="contained" disabled={!scenarioName}>
            Run Scenario
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
