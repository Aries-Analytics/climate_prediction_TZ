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

  // Models that support feature importance (tree-based models)
  const supportsFeatureImportance = (modelName: string) => {
    return ['random_forest', 'xgboost'].includes(modelName.toLowerCase())
  }

  useEffect(() => {
    if (selectedModel && supportsFeatureImportance(selectedModel)) {
      fetchFeatureImportance(selectedModel)
    } else {
      // Clear feature importance for models that don't support it
      setFeatureImportance([])
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
      // Silently handle - feature importance may not be available
      setFeatureImportance([])
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

  const selectedModelData = models.find((m: ModelMetrics) => m.modelName === selectedModel)

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
    { id: 'r2Score', label: 'R² Score', format: (v: number) => v?.toFixed(4) ?? 'N/A' },
    { id: 'rmse', label: 'RMSE', format: (v: number) => v?.toFixed(4) ?? 'N/A' },
    { id: 'mae', label: 'MAE', format: (v: number) => v?.toFixed(4) ?? 'N/A' },
    { id: 'mape', label: 'MAPE', format: (v: number) => (v?.toFixed(2) ?? 'N/A') + '%' },
    { 
      id: 'trainingDate', 
      label: 'Training Date',
      format: (v: string) => new Date(v).toLocaleDateString()
    }
  ]

  // Cleveland dot plot for feature importance
  const featureImportanceData = [
    // Lines from baseline to dots
    {
      x: featureImportance.map((f: FeatureImportance) => f.importance),
      y: featureImportance.map((f: FeatureImportance) => f.featureName),
      mode: 'lines',
      type: 'scatter' as const,
      line: { 
        color: '#bdbdbd',
        width: 1
      },
      hoverinfo: 'skip',
      showlegend: false
    },
    // Dots
    {
      x: featureImportance.map((f: FeatureImportance) => f.importance),
      y: featureImportance.map((f: FeatureImportance) => f.featureName),
      mode: 'markers',
      type: 'scatter' as const,
      marker: { 
        size: 10,
        color: featureImportance.map((f: FeatureImportance) => f.importance),
        colorscale: [
          [0, '#e3f2fd'],
          [0.5, '#1976d2'],
          [1, '#0d47a1']
        ],
        showscale: false,
        line: {
          color: '#fff',
          width: 1
        }
      },
      hovertemplate: '<b>%{y}</b><br>' +
                     'Importance: %{x:.4f}<br>' +
                     '<i>Contribution to model predictions</i><br>' +
                     '<extra></extra>',
      showlegend: false
    }
  ]

  // R² Score bar chart data
  const r2ScoreData = [
    {
      x: models.map((m: ModelMetrics) => m.modelName),
      y: models.map((m: ModelMetrics) => m.r2Score),
      type: 'bar' as const,
      marker: { 
        color: '#4caf50',
        line: {
          color: '#2e7d32',
          width: 1
        }
      },
      hovertemplate: '<b>%{x}</b><br>' +
                     'R² Score: %{y:.4f}<br>' +
                     '<i>Explains %{customdata:.1f}% of variance</i><br>' +
                     '<extra></extra>',
      customdata: models.map((m: ModelMetrics) => (m.r2Score ?? 0) * 100)
    }
  ]

  // RMSE bar chart data
  const rmseData = [
    {
      x: models.map((m: ModelMetrics) => m.modelName),
      y: models.map((m: ModelMetrics) => m.rmse),
      type: 'bar' as const,
      marker: { 
        color: '#ff9800',
        line: {
          color: '#e65100',
          width: 1
        }
      },
      hovertemplate: '<b>%{x}</b><br>' +
                     'RMSE: %{y:.4f} mm<br>' +
                     '<i>Average prediction error</i><br>' +
                     '<extra></extra>'
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
                  {models.map((model: ModelMetrics) => (
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
            {/* Primary Metric - R² Score (Most Important) */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%', bgcolor: 'primary.50' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography color="text.secondary" variant="body2">
                      R² Score (Coefficient of Determination)
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      - Primary Quality Metric
                    </Typography>
                  </Box>
                  <Typography variant="h3" color={getMetricColor('r2Score', selectedModelData.r2Score)} sx={{ mb: 1 }}>
                    {selectedModelData.r2Score?.toFixed(4) ?? 'N/A'}
                  </Typography>
                  <Chip
                    label={(selectedModelData.r2Score ?? 0) >= 0.8 ? 'Excellent' : (selectedModelData.r2Score ?? 0) >= 0.6 ? 'Good' : 'Needs Improvement'}
                    size="small"
                    color={getMetricColor('r2Score', selectedModelData.r2Score ?? 0)}
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary" display="block">
                    Explains {((selectedModelData.r2Score ?? 0) * 100).toFixed(1)}% of variance in rainfall predictions
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Secondary Metrics - Absolute Errors */}
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    RMSE
                  </Typography>
                  <Typography variant="h4">
                    {selectedModelData.rmse?.toFixed(4) ?? 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Root Mean Squared Error (mm)
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
                    {selectedModelData.mae?.toFixed(4) ?? 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Mean Absolute Error (mm)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* MAPE with Warning */}
            <Grid item xs={12} md={12}>
              <Card sx={{ bgcolor: 'warning.50' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography color="text.secondary" variant="body2">
                      MAPE (Mean Absolute Percentage Error)
                    </Typography>
                    <Chip label="⚠️ Interpret with Caution" size="small" color="warning" variant="outlined" />
                  </Box>
                  <Typography variant="h5" sx={{ mb: 1 }}>
                    {selectedModelData.mape?.toFixed(2) ?? 'N/A'}%
                  </Typography>
                  <Alert severity="info" sx={{ mt: 1 }}>
                    <Typography variant="caption">
                      <strong>Note:</strong> MAPE can be inflated by low rainfall values (near-zero). 
                      For rainfall prediction, focus on <strong>R² and RMSE</strong> for overall model quality. 
                      MAPE is most useful for comparing relative performance across models.
                    </Typography>
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}

        {/* Feature Importance Chart */}
        {selectedModel && supportsFeatureImportance(selectedModel) && featureImportance.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Feature Importance
                </Typography>
                <Chart
                  data={featureImportanceData}
                  layout={{
                    height: 400,
                    margin: { l: 150, r: 20, t: 20, b: 40 },
                    xaxis: { 
                      title: 'Importance',
                      rangemode: 'tozero'
                    },
                    yaxis: { 
                      title: '',
                      autorange: 'reversed'
                    },
                    autosize: true
                  }}
                  config={{
                    responsive: true
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Feature Importance Not Available Message */}
        {selectedModel && !supportsFeatureImportance(selectedModel) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Feature Importance
                </Typography>
                <Alert severity="info">
                  <Typography variant="body2">
                    Feature importance is only available for tree-based models (Random Forest, XGBoost). 
                    The <strong>{selectedModel}</strong> model uses a different architecture that doesn't provide traditional feature importance scores.
                  </Typography>
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Model Comparison Charts - Small Multiples */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                R² Score Comparison
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Higher is better - Measures how well the model explains variance
              </Typography>
              <Chart
                data={r2ScoreData}
                layout={{
                  height: 350,
                  xaxis: { 
                    title: 'Model',
                    showgrid: false
                  },
                  yaxis: { 
                    title: 'R² Score',
                    rangemode: 'tozero',
                    gridcolor: '#e0e0e0'
                  },
                  margin: { l: 60, r: 20, t: 20, b: 80 },
                  autosize: true,
                  showlegend: false
                }}
                config={{
                  responsive: true
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                RMSE Comparison
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Lower is better - Measures average prediction error
              </Typography>
              <Chart
                data={rmseData}
                layout={{
                  height: 350,
                  xaxis: { 
                    title: 'Model',
                    showgrid: false
                  },
                  yaxis: { 
                    title: 'RMSE (mm)',
                    rangemode: 'tozero',
                    gridcolor: '#e0e0e0'
                  },
                  margin: { l: 60, r: 20, t: 20, b: 80 },
                  autosize: true,
                  showlegend: false
                }}
                config={{
                  responsive: true
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
