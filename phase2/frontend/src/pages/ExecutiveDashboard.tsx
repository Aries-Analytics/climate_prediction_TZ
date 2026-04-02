import { useEffect, useState, useMemo } from 'react'
import {
  Box, Grid, Typography, Alert, Chip, Paper,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  CircularProgress, Divider, LinearProgress, Tooltip
} from '@mui/material'
import axios from '../config/axiosInstance'
import { API_BASE_URL } from '../config/api'
import KPICard from '../components/common/KPICard'

// ─── types ───────────────────────────────────────────────────────────────────
interface PortfolioMetrics {
  totalPremiumIncome: number
  expectedPayouts: number
  lossRatio: number
  numberOfPolicies: number
  totalExposure: number
  reserves: number
  triggerBreakdown: { drought: number; flood: number; crop_failure: number }
  timeframe: string
  pilotLocation: string
  shadowRunConfig: { start: string; end: string; brierEvalDate: string }
}

interface ForecastRow {
  id: number
  triggerType: string
  horizonMonths: number
  probability: number
  targetDate: string
  confidenceLower: number
  confidenceUpper: number
  stage?: string
}

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
}

// ─── constants ───────────────────────────────────────────────────────────────
const TRIGGER_COLORS: Record<string, string> = {
  drought: '#d32f2f',
  flood: '#1565c0',
  crop_failure: '#e65100',
}
const HORIZON_LABELS: Record<number, string> = { 3: '3-mo', 4: '4-mo', 5: '5-mo*', 6: '6-mo*' }
const PRIMARY_HORIZONS = [3, 4]
const ADVISORY_HORIZONS = [5, 6]
const PAYOUT_THRESHOLD = 0.75
const ADVISORY_THRESHOLD = 0.50

export default function ExecutiveDashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioMetrics | null>(null)
  const [forecasts, setForecasts] = useState<ForecastRow[]>([])
  const [alerts, setAlerts] = useState<TriggerAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }

    Promise.all([
      axios.get(`${API_BASE_URL}/risk/portfolio`, { headers }),
      axios.get(`${API_BASE_URL}/forecasts`, { headers, params: { location_id: 6, days: 180 } }),
      axios.get(`${API_BASE_URL}/climate-forecasts/alerts`, { headers }),
    ])
      .then(([p, f, a]) => {
        setPortfolio(p.data)
        setForecasts(f.data)
        setAlerts(a.data)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  // ── derived: forecast probability grid (trigger × horizon, latest run) ────
  const probGrid = useMemo(() => {
    if (!forecasts.length) return {}
    // keep most-recent forecast per (triggerType, horizonMonths)
    const grid: Record<string, Record<number, ForecastRow>> = {}
    for (const f of forecasts) {
      if (!grid[f.triggerType]) grid[f.triggerType] = {}
      const existing = grid[f.triggerType][f.horizonMonths]
      if (!existing || new Date(f.targetDate) > new Date(existing.targetDate)) {
        grid[f.triggerType][f.horizonMonths] = f
      }
    }
    return grid
  }, [forecasts])

  // ── derived: advisory warnings (5-6 month, above advisory threshold) ──────
  const advisoryWarnings = useMemo(() => {
    const seen = new Map<string, ForecastRow>()
    for (const f of forecasts) {
      if (!ADVISORY_HORIZONS.includes(f.horizonMonths)) continue
      if (f.probability < ADVISORY_THRESHOLD) continue
      const key = f.triggerType
      const existing = seen.get(key)
      if (!existing || f.probability > existing.probability) seen.set(key, f)
    }
    return Array.from(seen.values()).sort((a, b) => b.probability - a.probability)
  }, [forecasts])

  // ── loss ratio status ─────────────────────────────────────────────────────
  const lrStatus = !portfolio ? 'success' :
    portfolio.lossRatio > 0.8 ? 'error' :
    portfolio.lossRatio > 0.6 ? 'warning' : 'success'

  const lrLabel = !portfolio ? '—' :
    portfolio.lossRatio > 0.8 ? 'CRITICAL' :
    portfolio.lossRatio > 0.6 ? 'Monitor' : 'Healthy'

  if (loading) return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
      <CircularProgress />
    </Box>
  )

  if (error) return (
    <Box sx={{ p: 3 }}>
      <Alert severity="error">Failed to load executive data: {error}</Alert>
    </Box>
  )

  const triggerTypes = ['drought', 'flood', 'crop_failure']
  const allHorizons = [3, 4, 5, 6]

  return (
    <Box sx={{ pb: 4 }}>
      {/* ── header ─────────────────────────────────────────────────────── */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
            <Typography variant="h4" fontWeight="bold">Executive Command Center</Typography>
            <Chip label="SHADOW RUN ACTIVE" color="warning" size="small" sx={{ fontWeight: 'bold' }} />
            <Chip label="LIVE DATA" color="success" size="small" variant="outlined" />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Morogoro Rice Pilot · 1,000 Farmers · Shadow Run: {portfolio ? `${portfolio.shadowRunConfig.start} – ${portfolio.shadowRunConfig.end}` : 'Mar 7 – Jun 12, 2026'} · Brier Score evaluation: {portfolio?.shadowRunConfig.brierEvalDate ?? '~Jun 9, 2026'}
          </Typography>
        </Box>
      </Box>

      {/* ── global status banner ────────────────────────────────────────── */}
      {alerts.length > 0 ? (
        <Alert severity="warning" variant="filled" sx={{ mb: 3 }}>
          <strong>{alerts.length} high-probability forecast alert{alerts.length > 1 ? 's' : ''} (≥75% primary tier):</strong>{' '}
          {alerts.map(a => `${a.alert_type} @ ${a.location_name}`).join(' · ')} — reserve sizing active. Shadow run: no real payout until observed breach confirmed post Jun 12, 2026.
        </Alert>
      ) : (
        <Alert severity="success" variant="filled" sx={{ mb: 3 }}>
          <strong>No active forecast alerts above payout threshold.</strong> All primary-tier (3–4 month) forecasts are below the 75% probability threshold.
          {advisoryWarnings.length > 0 && ` ${advisoryWarnings.length} advisory warning${advisoryWarnings.length > 1 ? 's' : ''} flagged (see below).`}
        </Alert>
      )}

      {/* ── KPI row ─────────────────────────────────────────────────────── */}
      {portfolio && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Farmers Covered"
              value={portfolio.numberOfPolicies.toLocaleString()}
              status="success"
              subtitle="Active policyholders"
              insight="Morogoro pilot — 1 ha/farmer average"
              insightSeverity="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Reserves"
              value={`$${portfolio.reserves.toLocaleString()}`}
              status={portfolio.reserves > portfolio.expectedPayouts ? 'success' : 'error'}
              subtitle={`Exposure: $${portfolio.totalExposure.toLocaleString()}`}
              insight="100% Capital Adequacy Ratio target"
              insightSeverity="info"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Expected Payouts"
              value={`$${portfolio.expectedPayouts.toLocaleString()}`}
              status={portfolio.expectedPayouts > 0 ? 'warning' : 'success'}
              subtitle={portfolio.timeframe}
              insight="Primary-tier forecasts ≥75% only"
              insightSeverity={portfolio.expectedPayouts > 0 ? 'warning' : 'success'}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KPICard
              title="Loss Ratio"
              value={`${(portfolio.lossRatio * 100).toFixed(1)}%`}
              status={lrStatus}
              subtitle={lrLabel}
              insight="Payouts / 6-month premiums. >80% = critical."
              insightSeverity={lrStatus}
            />
          </Grid>
        </Grid>
      )}

      {/* ── forecast probability grid + advisory warnings ────────────────── */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* probability heatmap */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Forecast Risk Landscape</Typography>
            <Alert severity="info" sx={{ mb: 2, py: 0.5 }}>
              <Typography variant="caption">
                Latest forecast probabilities per trigger type and horizon. <strong>Columns marked * are advisory tier</strong> (early warning only — no payout). Payout threshold = 75%.
              </Typography>
            </Alert>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.100' }}>
                    <TableCell><strong>Trigger Type</strong></TableCell>
                    {allHorizons.map(h => (
                      <TableCell key={h} align="center">
                        <Typography variant="caption" fontWeight="bold">
                          {HORIZON_LABELS[h]}
                          {ADVISORY_HORIZONS.includes(h) && (
                            <Typography component="span" variant="caption" color="text.secondary"> advisory</Typography>
                          )}
                        </Typography>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {triggerTypes.map(tt => (
                    <TableRow key={tt} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: TRIGGER_COLORS[tt] }} />
                          <Typography variant="body2" fontWeight="medium">
                            {tt.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          </Typography>
                        </Box>
                      </TableCell>
                      {allHorizons.map(h => {
                        const f = probGrid[tt]?.[h]
                        const prob = f?.probability ?? null
                        const isPrimary = PRIMARY_HORIZONS.includes(h)
                        const bg = prob === null ? 'grey.50' :
                          prob >= PAYOUT_THRESHOLD ? '#ffebee' :
                          prob >= ADVISORY_THRESHOLD ? '#fff8e1' : '#e8f5e9'
                        const color = prob === null ? 'text.disabled' :
                          prob >= PAYOUT_THRESHOLD ? 'error.main' :
                          prob >= ADVISORY_THRESHOLD ? 'warning.main' : 'success.main'
                        return (
                          <TableCell key={h} align="center" sx={{ bgcolor: bg }}>
                            {prob === null ? (
                              <Typography variant="caption" color="text.disabled">—</Typography>
                            ) : (
                              <Tooltip title={f ? `Target: ${new Date(f.targetDate).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })} · CI: ${(f.confidenceLower*100).toFixed(0)}–${(f.confidenceUpper*100).toFixed(0)}%` : ''}>
                                <Box>
                                  <Typography variant="body2" fontWeight="bold" color={color}>
                                    {(prob * 100).toFixed(0)}%
                                  </Typography>
                                  {!isPrimary && (
                                    <Typography variant="caption" color="text.secondary">advisory</Typography>
                                  )}
                                  {isPrimary && prob >= PAYOUT_THRESHOLD && f?.stage !== 'off_season' && (
                                    <Chip label="TRIGGER" color="error" size="small" sx={{ height: 16, fontSize: '0.6rem', mt: 0.3 }} />
                                  )}
                                  {isPrimary && prob >= PAYOUT_THRESHOLD && f?.stage === 'off_season' && (
                                    <Chip label="OFF-SEASON" color="default" size="small" sx={{ height: 16, fontSize: '0.6rem', mt: 0.3 }} />
                                  )}
                                </Box>
                              </Tooltip>
                            )}
                          </TableCell>
                        )
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Box sx={{ mt: 1.5, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {[
                { color: '#ffebee', label: '≥75% — Payout trigger (in-season)' },
                { color: '#fff8e1', label: '50–75% — Advisory warning' },
                { color: '#e8f5e9', label: '<50% — No concern' },
              ].map(({ color, label }) => (
                <Box key={label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 14, height: 14, bgcolor: color, border: '1px solid #ddd', borderRadius: 0.5 }} />
                  <Typography variant="caption" color="text.secondary">{label}</Typography>
                </Box>
              ))}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Chip label="OFF-SEASON" color="default" size="small" sx={{ height: 16, fontSize: '0.6rem' }} />
                <Typography variant="caption" color="text.secondary">≥75% but no insured crop — no payout</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* advisory warnings panel */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Advisory Early Warnings</Typography>
            <Alert severity="info" sx={{ mb: 2, py: 0.5 }}>
              <Typography variant="caption">
                5–6 month horizon forecasts above 50%. <strong>No payout triggered</strong> — these are early signals to inform farmer advisories and planning.
              </Typography>
            </Alert>

            {advisoryWarnings.length === 0 ? (
              <Alert severity="success" variant="outlined">
                No advisory-tier risks above 50% threshold.
              </Alert>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {advisoryWarnings.map(f => {
                  const pct = Math.round(f.probability * 100)
                  const color = f.probability >= 0.80 ? 'error' : 'warning'
                  return (
                    <Box key={f.id}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: TRIGGER_COLORS[f.triggerType] }} />
                          <Typography variant="body2" fontWeight="bold">
                            {f.triggerType.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          </Typography>
                          <Chip label={`${f.horizonMonths}-month`} size="small" variant="outlined" />
                        </Box>
                        <Chip label={`${pct}%`} color={color} size="small" />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={pct}
                        color={color}
                        sx={{ height: 6, borderRadius: 1 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        Target: {new Date(f.targetDate).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}
                        {f.stage ? ` · Phase: ${f.stage}` : ''}
                      </Typography>
                    </Box>
                  )
                })}
              </Box>
            )}

            <Divider sx={{ my: 2 }} />
            <Typography variant="caption" color="text.secondary" display="block">
              <strong>Shadow run context:</strong> Advisory signals at this horizon are consistent with XGBoost's
              capability range. Accuracy is evaluated when 3-month windows mature ({portfolio?.shadowRunConfig.brierEvalDate ?? '~Jun 9, 2026'}).
              These warnings support farmer preparation, not insurance payouts.
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* ── reserve adequacy bar ────────────────────────────────────────── */}
      {portfolio && (
        <Paper sx={{ p: 2, mb: 4 }}>
          <Typography variant="h6" gutterBottom>Reserve Adequacy</Typography>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              {[
                { label: 'Annual Premiums', value: portfolio.totalPremiumIncome, max: portfolio.reserves, color: '#2e7d32' },
                { label: 'Expected Payouts (6-mo)', value: portfolio.expectedPayouts, max: portfolio.reserves, color: '#d32f2f' },
                { label: 'Reserves', value: portfolio.reserves, max: portfolio.reserves, color: '#1565c0' },
              ].map(({ label, value, max, color }) => (
                <Box key={label} sx={{ mb: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">{label}</Typography>
                    <Typography variant="body2" fontWeight="bold">${value.toLocaleString()}</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(100, (value / max) * 100)}
                    sx={{ height: 8, borderRadius: 1, bgcolor: 'grey.200', '& .MuiLinearProgress-bar': { bgcolor: color } }}
                  />
                </Box>
              ))}
            </Grid>
            <Grid item xs={12} md={6}>
              <Alert severity={portfolio.reserves >= portfolio.expectedPayouts ? 'success' : 'error'}>
                <strong>Capital buffer: ${(portfolio.reserves - portfolio.expectedPayouts).toLocaleString()}</strong>
                {' '}({portfolio.reserves > 0 ? ((1 - portfolio.expectedPayouts / portfolio.reserves) * 100).toFixed(1) : '100'}% of reserves intact)
              </Alert>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Worst-case full exposure: ${portfolio.totalExposure.toLocaleString()} (all 1,000 farmers trigger crop failure)
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* ── active payout triggers table ───────────────────────────────── */}
      <Typography variant="h6" gutterBottom>
        Active Payout Triggers
        <Chip
          label={alerts.length === 0 ? 'None' : `${alerts.length} active`}
          color={alerts.length === 0 ? 'success' : 'error'}
          size="small"
          sx={{ ml: 1 }}
        />
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'grey.100' }}>
            <TableRow>
              <TableCell><strong>Location</strong></TableCell>
              <TableCell><strong>Trigger Type</strong></TableCell>
              <TableCell><strong>Growth Phase</strong></TableCell>
              <TableCell align="right"><strong>Forecast (mm)</strong></TableCell>
              <TableCell align="right"><strong>Threshold (mm)</strong></TableCell>
              <TableCell align="right"><strong>Deviation</strong></TableCell>
              <TableCell align="right"><strong>Days to Impact</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                  No active payout triggers — all primary-tier forecasts are below the 75% threshold.
                </TableCell>
              </TableRow>
            ) : (
              alerts.map((a, idx) => (
                <TableRow key={idx}>
                  <TableCell>{a.location_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={a.alert_type.replace('_', ' ').toUpperCase()}
                      size="small"
                      sx={{ bgcolor: TRIGGER_COLORS[a.alert_type] + '22', color: TRIGGER_COLORS[a.alert_type], fontWeight: 'bold' }}
                    />
                  </TableCell>
                  <TableCell>{a.phenology_stage}</TableCell>
                  <TableCell align="right">{a.forecast_value}mm</TableCell>
                  <TableCell align="right">{a.threshold_value}mm</TableCell>
                  <TableCell align="right" sx={{ color: a.deviation < 0 ? 'error.main' : 'success.main', fontWeight: 'bold' }}>
                    {a.deviation > 0 ? '+' : ''}{a.deviation.toFixed(1)}mm
                  </TableCell>
                  <TableCell align="right">{a.urgency_days}d</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
