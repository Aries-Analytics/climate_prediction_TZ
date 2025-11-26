import { useEffect, useState } from 'react'
import { Box, Grid, Typography, Alert, FormControl, InputLabel, Select, MenuItem, Tooltip, IconButton, Card, CardContent } from '@mui/material'
import InfoIcon from '@mui/icons-material/Info'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import { useAuth } from '../contexts/AuthContext'
import KPICard from '../components/common/KPICard'
import LoadingSpinner from '../components/common/LoadingSpinner'

interface ExecutiveKPIs {
  flood_trigger_rate: { rate: number; count: number; status: string }
  drought_trigger_rate: { rate: number; count: number; status: string }
  crop_failure_trigger_rate: { rate: number; count: number; status: string }
  combined_trigger_rate: number
  loss_ratio: number
  sustainability_status: string
  total_triggers_ytd: number
  estimated_payouts_ytd: number
}

export default function ExecutiveDashboard() {
  const [kpis, setKpis] = useState<ExecutiveKPIs | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedYear, setSelectedYear] = useState<number>(2023)
  const { token } = useAuth()

  // Generate year options from 2018 to 2023
  const yearOptions = Array.from({ length: 6 }, (_, i) => 2023 - i)

  useEffect(() => {
    fetchKPIs()
  }, [selectedYear])

  const fetchKPIs = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/dashboard/executive?year=${selectedYear}`, 
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setKpis(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading executive snapshot..." />
  if (error) return <Alert severity="error">{error}</Alert>

  // Format currency with commas
  const formatCurrency = (value: number) => {
    return Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Executive Snapshot
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Overview of key performance indicators and system health
          </Typography>
        </Box>
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Year</InputLabel>
          <Select
            value={selectedYear}
            label="Year"
            onChange={(e) => setSelectedYear(Number(e.target.value))}
          >
            {yearOptions.map(year => (
              <MenuItem key={year} value={year}>{year}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography color="text.secondary" variant="body2">
                  Flood Trigger Rate
                </Typography>
                <Tooltip title="Percentage of days with flood triggers. Target: 0.5-2% annually. Floods occur during heavy rainfall periods (March-May, Oct-Dec).">
                  <IconButton size="small"><InfoIcon fontSize="small" /></IconButton>
                </Tooltip>
              </Box>
              <Typography variant="h4" color={kpis?.flood_trigger_rate.status === 'within_target' ? 'success.main' : 'warning.main'}>
                {(kpis?.flood_trigger_rate.rate || 0).toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {kpis?.flood_trigger_rate.count || 0} events in {selectedYear}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography color="text.secondary" variant="body2">
                  Drought Trigger Rate
                </Typography>
                <Tooltip title="Percentage of days with drought triggers. Target: 1-3% annually. Droughts typically occur during dry seasons (June-Sept, Jan-Feb).">
                  <IconButton size="small"><InfoIcon fontSize="small" /></IconButton>
                </Tooltip>
              </Box>
              <Typography variant="h4" color={kpis?.drought_trigger_rate.status === 'within_target' ? 'success.main' : 'warning.main'}>
                {(kpis?.drought_trigger_rate.rate || 0).toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {kpis?.drought_trigger_rate.count || 0} events in {selectedYear}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography color="text.secondary" variant="body2">
                  Loss Ratio
                </Typography>
                <Tooltip title="Payouts divided by premiums. <60% = sustainable (profitable), 60-80% = warning (break-even), >80% = unsustainable (loss-making). Industry standard target: 40-60%.">
                  <IconButton size="small"><InfoIcon fontSize="small" /></IconButton>
                </Tooltip>
              </Box>
              <Typography variant="h4" color={
                kpis?.sustainability_status === 'sustainable' ? 'success.main' :
                kpis?.sustainability_status === 'warning' ? 'warning.main' : 'error.main'
              }>
                {((kpis?.loss_ratio || 0) * 100).toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {kpis?.sustainability_status || 'Unknown'} - {selectedYear}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography color="text.secondary" variant="body2">
                  Total Payouts {selectedYear}
                </Typography>
                <Tooltip title="Total insurance payouts triggered by climate events. Based on severity thresholds: Drought=500k TZS, Flood=750k TZS, Crop Failure=625k TZS (only when severity >30%).">
                  <IconButton size="small"><InfoIcon fontSize="small" /></IconButton>
                </Tooltip>
              </Box>
              <Typography variant="h4" color="primary.main">
                {formatCurrency(kpis?.estimated_payouts_ytd || 0)} TZS
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {kpis?.total_triggers_ytd || 0} total triggers
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
