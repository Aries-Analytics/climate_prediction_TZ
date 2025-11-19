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
  SelectChangeEvent
} from '@mui/material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import DataTable from '../components/common/DataTable'
import Chart from '../components/charts/Chart'
import { ModelMetrics, FeatureImportance } from '../types'

export default function ModelPerformanceDashboard() {
  const [models, setModels] = useState<ModelMetrics[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [featureImportance, setFeatureImportance] = useState<FeatureImportance[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [driftAlert, setDriftAlert] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
  }, [])

  useEffect(() => {
    if (selectedModel) {
      fetchFeatureImportance(selectedModel)
    }
  }, [selectedModel])

  const fetchModels = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/models`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setModels(response.data)
      if (response.data.length > 0) {
        setSelectedModel(response.data[0].modelName)
      }
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch models')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchFeatureImportance = async (modelName: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(
        `${API_BASE_URL}/models/${modelName}/importance`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setFeatureImportance(response.data)
    } catch (err) {
      console.error('Failed to fetch feature importance:', err)
    }
  }

  const handleModelChange = (event: SelectChangeEvent) => {
    setSelectedModel(event.target.value)
  }

  const getMetricColor = (metric: string, value: number): 'success' | 'warning' | 'error' => {
    if (metric === 'r2Score') {
      if (value >= 0.8) return 'success'
      if (value >= 0.6) return 'warning'
      return 'error'
    }
    // For error metrics (RMSE, MAE, MAPE), lower is better
    if (value <= 0.1) return 'success'
    if (value <= 0.3) return 'warning'
    return 'error'
  }

  const selectedModelData = models.find(m => m.modelName === selectedModel)

  if (isLoading) {
    return <LoadingSpinner message="Loading model performance data..." />
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (models.length === 0) {
    return (
      <EmptyState
        message="No models found"
        description="Train some models to see performance metrics here"
      />
    )
  }

  const metricsColumns = [
    { id: 'modelName', label: 'Model Name' },
    { id: 'r2Score', label: 'R² Score', format: (v: number) => v.toFixed(4) },
    { id: 'rmse', label: 'RMSE', format: (v: number) => v.toFixed(4) },
    { id: 'mae', label: 'MAE', format: (v: number) => v.toFixed(4) },
    { id: 'mape', label: 'MAPE', format: (v: number) => v.toFixed(2) + '%' },
    { 
      id: 'trainingDate', 
      label: 'Training Date',
      format: (v: string) => new Date(v).toLocaleDateString()
    }
  ]

  const featureImportanceData = {
    x: featureImportance.map(f => f.importance),
    y: featureImportance.map(f => f.featureName),
    type: 'bar' as const,
    orientation: 'h' as const,
    marker: { color: '#1976d2' }
  }

  const metricsComparisonData = [
    {
      x: models.map(m => m.modelName),
      y: models.map(m => m.r2Score),
      name: 'R² Score',
      type: 'bar' as const,
      marker: { color: '#4caf50' }
    },
    {
      x: models.map(m => m.modelName),
      y: models.map(m => m.rmse),
      name: 'RMSE',
      type: 'bar' as const,
      yaxis: 'y2',
      marker: { color: '#ff9800' }
    }
  ]

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Model Performance Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Monitor ML model metrics, compare performance, and track drift
        </Typography>
      </Box>

      {driftAlert && (
        <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setDriftAlert(null)}>
          {driftAlert}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Model Selector */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <FormControl fullWidth>
                <InputLabel>Select Model</InputLabel>
                <Select
                  value={selectedModel}
                  label="Select Model"
                  onChange={handleModelChange}
                >
                  {models.map((model) => (
                    <MenuItem key={model.modelName} value={model.modelName}>
                      {model.modelName}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        {/* Selected Model Metrics */}
        {selectedModelData && (
          <>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    R² Score
                  </Typography>
                  <Typography variant="h4" color={getMetricColor('r2Score', selectedModelData.r2Score)}>
                    {selectedModelData.r2Score.toFixed(4)}
                  </Typography>
                  <Chip
                    label={selectedModelData.r2Score >= 0.8 ? 'Excellent' : selectedModelData.r2Score >= 0.6 ? 'Good' : 'Needs Improvement'}
                    size="small"
                    color={getMetricColor('r2Score', selectedModelData.r2Score)}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    RMSE
                  </Typography>
                  <Typography variant="h4">
                    {selectedModelData.rmse.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Root Mean Squared Error
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    MAE
                  </Typography>
                  <Typography variant="h4">
                    {selectedModelData.mae.toFixed(4)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Mean Absolute Error
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    MAPE
                  </Typography>
                  <Typography variant="h4">
                    {selectedModelData.mape.toFixed(2)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Mean Absolute Percentage Error
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Feature Importance Chart */}
        {featureImportance.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Feature Importance
                </Typography>
                <Chart
                  data={[featureImportanceData]}
                  layout={{
                    height: 400,
                    margin: { l: 150, r: 20, t: 20, b: 40 },
                    xaxis: { title: 'Importance' },
                    yaxis: { title: '' }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Model Comparison Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Comparison
              </Typography>
              <Chart
                data={metricsComparisonData}
                layout={{
                  height: 400,
                  barmode: 'group',
                  xaxis: { title: 'Model' },
                  yaxis: { title: 'R² Score' },
                  yaxis2: {
                    title: 'RMSE',
                    overlaying: 'y',
                    side: 'right'
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* All Models Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                All Models
              </Typography>
              <DataTable
                columns={metricsColumns}
                rows={models}
                searchable
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
