import { useState, useEffect, useMemo, lazy, Suspense } from 'react'
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
  Paper,
  Stack,
  CircularProgress
} from '@mui/material'
import axios from '../config/axiosInstance'
import { API_BASE_URL } from '../config/api'
import LoadingSpinner from '../components/common/LoadingSpinner'
import DataTable from '../components/common/DataTable'
// Lazy-load GeographicMap (1.97 MB — includes Tanzania GeoJSON) so map tab doesn't block initial render
const GeographicMap = lazy(() => import('../components/GeographicMap'))
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

// Phase Importance Mapping (Aligned with Parametric Logic)
const getPhaseImportance = (stage: string) => {
  const s = stage?.toLowerCase() || '';
  if (s.includes('flowering')) return { label: 'CRITICAL PHASE', color: 'error' as const };
  if (s.includes('vegetative')) return { label: 'HIGH PRIORITY', color: 'warning' as const };
  if (s.includes('germination')) return { label: 'MODERATE', color: 'info' as const };
  return { label: 'LOW PRIORITY', color: 'default' as const };
}

export default function TriggersDashboard() {
  const [alerts, setAlerts] = useState<TriggerAlert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter States
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [locations, setLocations] = useState<any[]>([])

  const filteredAlerts = useMemo(() =>
    selectedLocation === 'all'
      ? alerts
      : alerts.filter(a => a.location_id?.toString() === selectedLocation),
    [alerts, selectedLocation]
  )

  useEffect(() => {
    fetchClimateAlerts()
  }, [])

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

  const columns = useMemo(() => [
    {
      id: 'location_name',
      label: 'Location',
      format: (val: string) => <strong>{val}</strong>
    },
    {
      id: 'alert_date',
      label: 'Forecast Date',
      format: (val: string) => new Date(val).toLocaleDateString()
    },
    {
      id: 'phenology_stage',
      label: 'Growth Phase',
      format: (val: string) => {
        const importance = getPhaseImportance(val);
        return (
          <Stack direction="column" spacing={0.5}>
            <Typography variant="body2" fontWeight="bold">{val?.toUpperCase()}</Typography>
            <Chip
              label={importance.label}
              color={importance.color}
              size="small"
              sx={{ height: 20, fontSize: '0.65rem', width: 'fit-content' }}
            />
          </Stack>
        )
      }
    },
    {
      id: 'alert_type',
      label: 'Trigger Type',
      format: (value: string, row: TriggerAlert) => (
        <Chip
          label={`${row.phenology_stage?.toUpperCase()} ${value?.replace('_', ' ').toUpperCase()}`}
          color={value?.includes('CRITICAL') ? 'error' : 'warning'}
          size="small"
          variant="outlined"
        />
      )
    },
    {
      id: 'forecast_value',
      label: 'Status (mm)',
      numeric: true,
      format: (val: number, row: any) => (
        <Tooltip title={`Phase Threshold: ${row.threshold_value}mm`}>
          <Box>
            <Typography variant="body2" fontWeight="bold">
              {val}mm
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Target: {row.threshold_value}mm
            </Typography>
          </Box>
        </Tooltip>
      )
    },
    {
      id: 'deviation',
      label: 'Deficit/Gap',
      numeric: true,
      format: (val: number) => (
        <Typography
          fontWeight="bold"
          color={val < 0 ? 'error.main' : 'success.main'}
        >
          {val > 0 ? '+' : ''}{val.toFixed(1)}mm
        </Typography>
      )
    },
    {
      id: 'trend',
      label: 'Trend (3 Mo)',
      format: (_val: any, row: any) => {
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
      label: 'Protocol Action',
      minWidth: 200,
      format: (val: string) => <Typography variant="body2" sx={{ fontStyle: 'italic' }}>{val}</Typography>
    }
  ], [])

  if (isLoading) return <LoadingSpinner message="Loading parametric triggers..." />

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  const triggerSummary = useMemo(() => {
    const types = ['drought', 'flood', 'crop_failure'] as const
    return types.map(tt => {
      const typeAlerts = filteredAlerts.filter(a => a.alert_type === tt)
      return {
        tt,
        triggered: typeAlerts.length,
        worst: typeAlerts.reduce((w, a) => a.deviation < w ? a.deviation : w, 0),
      }
    })
  }, [filteredAlerts])

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
          Parametric Trigger Events
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitoring active insurance triggers based on <strong>Phase-Specific Logic</strong>. Payouts are triggered when environmental conditions breach phase thresholds.
        </Typography>
      </Box>

      {/* ── threshold summary bar ─────────────────────────────────────── */}
      {(
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Threshold Status Summary — {filteredAlerts.length === 0 ? 'All clear' : `${filteredAlerts.length} active payout alert${filteredAlerts.length !== 1 ? 's' : ''}`} (primary tier ≥75%)
          </Typography>
          <Grid container spacing={2}>
            {triggerSummary.map(({ tt, triggered, worst }) => {
              return (
                <Grid item xs={12} sm={4} key={tt}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box
                      sx={{
                        width: 36, height: 36, borderRadius: '50%',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        bgcolor: triggered > 0 ? 'error.light' : 'success.light',
                      }}
                    >
                      <Typography variant="caption" fontWeight="bold" color={triggered > 0 ? 'error.dark' : 'success.dark'}>
                        {triggered > 0 ? '!' : '✓'}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {tt.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </Typography>
                      {triggered > 0 ? (
                        <Typography variant="caption" color="error.main">
                          {triggered} trigger{triggered > 1 ? 's' : ''} · worst: {worst.toFixed(1)}mm deficit
                        </Typography>
                      ) : (
                        <Typography variant="caption" color="success.main">
                          Below payout threshold
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </Grid>
              )
            })}
          </Grid>
        </Paper>
      )}

      <Grid container spacing={3}>
        {/* Consolidated Action Card & KPIs */}
        <Grid item xs={12} md={6}>
          <PayoutActionCard activeTriggers={filteredAlerts} />
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Impacted Zones
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="warning.main">
                {new Set(filteredAlerts.map(a => a.location_id)).size}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Locations with active phase triggers
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Avg Deficit
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="error.main">
                {filteredAlerts.length > 0
                  ? (filteredAlerts.reduce((sum, a) => sum + (a.deviation < 0 ? Math.abs(a.deviation || 0) : 0), 0) / (filteredAlerts.filter(a => a.deviation < 0).length || 1)).toFixed(1)
                  : '0'}mm
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Average rainfall gap in triggered zones
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* MAP SECTION - NEW INTEGRATION */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, minHeight: 600 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Phase-Based Geospatial Analysis
              </Typography>
              <Stack direction="row" spacing={1}>
                <Chip label="Phase Logic Active" color="primary" size="small" />
                <Chip label="Live Data" color="success" size="small" variant="outlined" />
              </Stack>
            </Box>
            <Alert severity="info" sx={{ mb: 2, py: 0 }}>
              <strong>Visualization Guide:</strong> Red regions indicate locations where rainfall is below the specific threshold for the current growth phase (e.g., Flowering &lt; 120mm).
            </Alert>
            <Suspense fallback={<Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><CircularProgress /></Box>}>
              <GeographicMap
                mode="trigger"
                triggers={triggerMapData}
              />
            </Suspense>
          </Paper>
        </Grid>


        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Critical Phase Analysis (Top Risks)
              </Typography>
              <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Parametric Evaluation:</strong> These gauges show the deviation from the <strong>Phase Threshold</strong> (not annual average).
                  Red zones indicate a confirmed payout condition for that specific biological stage.
                </Typography>
              </Alert>

              {filteredAlerts.filter(a => a.deviation < 0).length === 0 ? (
                <Alert severity="success" variant="outlined">No critical deficits detected. All locations are safely within phase thresholds.</Alert>
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
                            title={`${alert.location_name} (${alert.phenology_stage})`}
                            value={alert.forecast_value}
                            threshold={alert.threshold_value}
                            min={0}
                            max={alert.threshold_value * 1.5} // Scale max to 150% of threshold
                          />
                          <Typography variant="subtitle2" color="error" fontWeight="bold">
                            {Math.abs(alert.deviation).toFixed(1)}mm Deficit
                          </Typography>
                          <Chip
                            size="small"
                            label={`Target: >${alert.threshold_value}mm`}
                            sx={{ mt: 0.5, bgcolor: 'background.paper', border: '1px solid #ddd' }}
                          />
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
                  <strong>Payout Protocol:</strong> Triggers listed below have breached the specific threshold for their current biological phase.
                  "Recommended Action" derives from the severity of the phase-specific deficit.
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
