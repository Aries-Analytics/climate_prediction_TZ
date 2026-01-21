import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Paper
} from '@mui/material'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import DataTable from '../components/common/DataTable'
import Chart from '../components/charts/Chart'
import GeographicMap from '../components/GeographicMap'
import GaugeChart from '../components/charts/GaugeChart'
import Sparkline from '../components/charts/Sparkline'
import PayoutActionCard from '../components/PayoutActionCard'

interface TriggerAlert {
  id: number
  alert_type: string
  location_name?: string
  location_id?: number
  forecast_value: number
  threshold_value: number
  deviation: number
  phenology_stage: string
  urgency_days: number
  recommended_action: string
  alert_date: string
  history?: number[]
}

// ... existing code ...

const formatCurrency = (value: number) => {
  return '$' + Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export default function TriggersDashboard() {
  const [alerts, setAlerts] = useState<TriggerAlert[]>([])
  const [filteredAlerts, setFilteredAlerts] = useState<TriggerAlert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter States
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [locations, setLocations] = useState<any[]>([])

  useEffect(() => {
    fetchClimateAlerts()
  }, [])

  // Filter Logic
  useEffect(() => {
    if (selectedLocation === 'all') {
      setFilteredAlerts(alerts);
    } else {
      setFilteredAlerts(alerts.filter(a => a.location_id?.toString() === selectedLocation));
    }
  }, [selectedLocation, alerts]);

  const fetchClimateAlerts = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('token')

      // Fetch Alerts
      const response = await axios.get(`${API_BASE_URL}/climate-forecasts/alerts`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const fetchedAlerts = response.data;
      setAlerts(fetchedAlerts);

      // Extract unique locations for filter
      const uniqueLocs = new Map();
      fetchedAlerts.forEach((a: TriggerAlert) => {
        if (a.location_id && a.location_name) {
          uniqueLocs.set(a.location_id, a.location_name);
        }
      });
      // Convert map to array for dropdown
      const locArray = Array.from(uniqueLocs.entries()).map(([id, name]) => ({ id, name }));
      setLocations(locArray);

    } catch (err: any) {
      console.error('Failed to fetch alerts:', err)
      setError('Failed to load active triggers. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const columns = [
    {
      id: 'location_name',
      label: 'Location',
      format: (val: string) => <strong>{val}</strong>
    },
    {
      id: 'alert_date',
      label: 'Date',
      format: (val: string) => new Date(val).toLocaleDateString()
    },
    {
      id: 'phenology_stage',
      label: 'Stage',
      format: (val: string) => <Chip label={val?.toUpperCase()} size="small" variant="outlined" />
    },
    {
      id: 'alert_type',
      label: 'Alert Type',
      format: (value: string) => (
        <Chip
          label={value?.replace('_', ' ').toUpperCase()}
          color={value?.includes('CRITICAL') ? 'error' : 'warning'}
          size="small"
        />
      )
    },
    {
      id: 'forecast_value',
      label: 'Forecast (mm)',
      numeric: true,
      format: (val: number, row: any) => (
        <Tooltip title={`Threshold: ${row.threshold_value}mm`}>
          <span>{val}mm <Typography variant="caption" color="text.secondary">vs {row.threshold_value}</Typography></span>
        </Tooltip>
      )
    },
    { id: 'deviation', label: 'Deviation', numeric: true, format: (val: number) => <span style={{ color: val > 0 ? 'green' : 'red' }}>{val > 0 ? '+' : ''}{val.toFixed(1)}</span> },
    {
      id: 'trend',
      label: 'Trend (3 Mo)',
      format: (val: any, row: any) => {
        if (!row.history || row.history.length === 0) {
          return (
            <Typography variant="caption" color="text.secondary">
              N/A
            </Typography>
          );
        }

        const data = row.history;
        const isCritical = row.deviation < 0;

        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Sparkline
              data={data}
              width={60}
              height={20}
              color={isCritical ? '#d32f2f' : '#2e7d32'}
            />
          </Box>
        );
      }
    },
    {
      id: 'recommended_action',
      label: 'Recommended Action',
      minWidth: 250,
      format: (val: string) => <Typography variant="body2" sx={{ fontStyle: 'italic' }}>{val}</Typography>
    }
  ]

  if (isLoading) return <LoadingSpinner message="Loading active triggers..." />

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  // Transform alerts to map format
  const triggerMapData = filteredAlerts.map(alert => ({
    location_id: alert.location_id,
    location_name: alert.location_name,
    alert_type: alert.alert_type,
    deviation: alert.deviation,
    threshold_value: alert.threshold_value
  }));

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Trigger Events & Alerts
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time monitoring of active parametric insurance triggers based on climate index forecasts.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Consolidated Action Card & KPIs */}
        <Grid item xs={12} md={6}>
          <PayoutActionCard activeTriggers={filteredAlerts} />
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Locations Affected
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="warning.main">
                {new Set(filteredAlerts.map(a => a.location_id)).size}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Unique locations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Avg Deviation
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="primary">
                {filteredAlerts.length > 0
                  ? (filteredAlerts.reduce((sum, a) => sum + Math.abs(a.deviation || 0), 0) / filteredAlerts.length).toFixed(1)
                  : '0'}mm
              </Typography>
              <Typography variant="caption" color="text.secondary">
                From thresholds
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* MAP SECTION - NEW INTEGRATION */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, minHeight: 600 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Geospatial Trigger Analysis
              </Typography>
              <Chip label="Live Data" color="success" size="small" variant="outlined" />
            </Box>
            <Alert severity="info" sx={{ mb: 2, py: 0 }}>
              Data visualized represents active trigger events. <strong>Red</strong> regions indicate critical deficits requiring immediate attention.
            </Alert>
            <GeographicMap
              mode="trigger"
              triggers={triggerMapData}
            />
          </Paper>
        </Grid>


        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Critical Threshold Analysis (Top Risks)
              </Typography>
              <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Threshold Analysis:</strong> Radial gauges display the severity of deviation from safety thresholds.
                  Red zones indicate confirmed payout conditions.
                </Typography>
              </Alert>

              {filteredAlerts.filter(a => a.deviation < 0).length === 0 ? (
                <Alert severity="success" variant="outlined">No critical deficits detected. All locations are above safety thresholds.</Alert>
              ) : (
                <Grid container spacing={2} justifyContent="center" alignItems="center">
                  {filteredAlerts
                    .filter(a => a.deviation < 0 || a.alert_type.includes('CRITICAL') || a.alert_type.includes('DEFICIT'))
                    .sort((a, b) => a.deviation - b.deviation) // Sort by worst deviation (most negative first)
                    .slice(0, 4) // Show top 4
                    .map((alert) => (
                      <Grid item key={alert.id} xs={12} sm={6} md={3} sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Box sx={{ textAlign: 'center' }}>
                          <GaugeChart
                            title={alert.location_name || `Location ${alert.location_id}`}
                            value={alert.forecast_value}
                            threshold={alert.threshold_value}
                            min={0}
                            max={alert.threshold_value * 1.5} // Scale max to 150% of threshold
                          />
                          <Typography variant="body2" color="error" fontWeight="bold">
                            {Math.abs(alert.deviation).toFixed(1)}mm Deficit
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Stage: {alert.phenology_stage}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Active Triggers Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
                <Typography variant="h6">Active Payout Triggers</Typography>
                <FormControl sx={{ minWidth: 200 }} size="small">
                  <InputLabel>Filter by Location</InputLabel>
                  <Select
                    value={selectedLocation}
                    label="Filter by Location"
                    onChange={(e) => setSelectedLocation(e.target.value as string)}
                  >
                    <MenuItem value="all">All Locations</MenuItem>
                    {locations.length > 0 ? locations.map(loc => (
                      <MenuItem key={loc.id} value={loc.id.toString()}>{loc.name}</MenuItem>
                    )) : <MenuItem disabled>No locations found</MenuItem>}
                  </Select>
                </FormControl>
              </Box>

              <Alert severity="warning" variant="outlined" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Payout Protocol:</strong> Verify trend data (3-month trajectory) before authorizing payouts. Critical alerts (Red) imply conditions have breached the payout threshold.
                </Typography>
              </Alert>

              {filteredAlerts.length === 0 ? (
                <Alert severity="success" sx={{ mt: 2 }}>
                  No active triggers detected. Climate conditions are within safe thresholds for the selected filter.
                </Alert>
              ) : (
                <DataTable
                  rows={filteredAlerts}
                  columns={columns}
                  loading={false}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
