import { useEffect, useState } from 'react'
import { Box, Grid, Typography, Alert } from '@mui/material'
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
  const { token } = useAuth()

  useEffect(() => {
    fetchKPIs()
  }, [])

  const fetchKPIs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/dashboard/executive`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setKpis(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading executive dashboard..." />
  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Executive Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Overview of key performance indicators and system health
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Flood Trigger Rate"
            value={`${(kpis?.flood_trigger_rate.rate || 0).toFixed(2)}%`}
            status={kpis?.flood_trigger_rate.status === 'within_target' ? 'success' : 'warning'}
            subtitle={`${kpis?.flood_trigger_rate.count || 0} events YTD`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Drought Trigger Rate"
            value={`${(kpis?.drought_trigger_rate.rate || 0).toFixed(2)}%`}
            status={kpis?.drought_trigger_rate.status === 'within_target' ? 'success' : 'warning'}
            subtitle={`${kpis?.drought_trigger_rate.count || 0} events YTD`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Loss Ratio"
            value={`${((kpis?.loss_ratio || 0) * 100).toFixed(1)}%`}
            status={
              kpis?.sustainability_status === 'sustainable' ? 'success' :
              kpis?.sustainability_status === 'warning' ? 'warning' : 'error'
            }
            subtitle={kpis?.sustainability_status || 'Unknown'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Total Payouts YTD"
            value={`$${(kpis?.estimated_payouts_ytd || 0).toLocaleString()}`}
            status="success"
            subtitle={`${kpis?.total_triggers_ytd || 0} total triggers`}
          />
        </Grid>
      </Grid>
    </Box>
  )
}
