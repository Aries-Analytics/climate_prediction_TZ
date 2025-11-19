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
  Chip
} from '@mui/material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import KPICard from '../components/common/KPICard'
import Chart from '../components/charts/Chart'
import { PortfolioMetrics, ScenarioResult } from '../types'
import WarningIcon from '@mui/icons-material/Warning'

export default function RiskManagementDashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioMetrics | null>(null)
  const [scenarioResults, setScenarioResults] = useState<ScenarioResult[]>([])
  const [recommendations, setRecommendations] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scenarioDialogOpen, setScenarioDialogOpen] = useState(false)
  const [scenarioName, setScenarioName] = useState('')
  const [scenarioParams, setScenarioParams] = useState('')

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
          parameters: JSON.parse(scenarioParams || '{}')
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setScenarioResults([...scenarioResults, response.data])
      setScenarioDialogOpen(false)
      setScenarioName('')
      setScenarioParams('')
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
            value={`$${portfolio.totalPremiumIncome.toLocaleString()}`}
            status="success"
            tooltip="Total premium collected from all policies"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <KPICard
            title="Expected Payouts"
            value={`$${portfolio.expectedPayouts.toLocaleString()}`}
            status="warning"
            tooltip="Estimated total payouts based on current risk"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <KPICard
            title="Loss Ratio"
            value={`${(portfolio.lossRatio * 100).toFixed(1)}%`}
            status={getLossRatioStatus(portfolio.lossRatio)}
            tooltip="Ratio of expected payouts to premium income"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <KPICard
            title="Number of Policies"
            value={portfolio.numberOfPolicies}
            status="success"
            tooltip="Total active insurance policies"
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
                      yaxis: { title: 'Value' }
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
                  ${portfolio.totalExposure.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Risk Exposure
                </Typography>
              </Box>
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
                  Based on current loss ratio of {(portfolio.lossRatio * 100).toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Scenario Dialog */}
      <Dialog open={scenarioDialogOpen} onClose={() => setScenarioDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Scenario Analysis</DialogTitle>
        <DialogContent>
          <TextField
            label="Scenario Name"
            fullWidth
            margin="normal"
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            placeholder="e.g., Severe Drought"
          />
          <TextField
            label="Parameters (JSON)"
            fullWidth
            margin="normal"
            multiline
            rows={4}
            value={scenarioParams}
            onChange={(e) => setScenarioParams(e.target.value)}
            placeholder='{"rainfall_reduction": 0.3, "temperature_increase": 2}'
          />
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
