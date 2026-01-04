import { useEffect, useState, useMemo } from 'react'
import { Box, Grid, Typography, Alert, FormControl, InputLabel, Select, MenuItem, Tooltip, IconButton, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material'
import InfoIcon from '@mui/icons-material/Info'
import Plot from 'react-plotly.js'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import { useAuth } from '../contexts/AuthContext'
import KPICard from '../components/common/KPICard'
import LoadingSpinner from '../components/common/LoadingSpinner'

// --- MOCK DATA GENERATOR (Temporary until backend ready) ---
const generateMockData = (year: number) => {
  // 1. Solvency History (5 Year Trend)
  // PROPER ACCOUNTING: Loss Ratio drives Payout, which depletes Reserves
  const STARTING_CAPITAL = 20000000; // $20M initial fund
  const ANNUAL_PREMIUMS = 10000000; // $10M premiums/year (assumed constant)

  let cumulativeReserves = STARTING_CAPITAL;
  const solvencyTrend = Array.from({ length: 5 }, (_, i) => {
    const y = year - 4 + i;

    // Generate Loss Ratio (40% - 120% to include BANKRUPTCY scenarios)
    // > 100% = Paying out more than income = Reserves shrink
    const lossRatio = 0.40 + (Math.random() * 0.80); // 40% - 120%

    // Calculate Payout based on Loss Ratio
    const payout = ANNUAL_PREMIUMS * lossRatio;

    // Update Cumulative Reserves (can go negative if LR > 100%)
    cumulativeReserves = cumulativeReserves + ANNUAL_PREMIUMS - payout;

    return {
      year: y,
      ratio: lossRatio,
      payout: payout,
      reserves: Math.max(0, cumulativeReserves) // Floor at $0 for visualization
    };
  });

  // 2. Basis Risk Data (Scatter: VHI vs Payout)
  // INCLUDES: 6 Pilot Regions + Extra regions for Scale Demo
  const regions = ['Arusha', 'Dar es Salaam', 'Dodoma', 'Mbeya', 'Mwanza', 'Morogoro', 'Singida', 'Tabora', 'Shinyanga', 'Kigoma'];
  const basisRiskPoints = regions.map(r => ({
    region: r,
    vhi: 0.2 + Math.random() * 0.6, // 0.2 to 0.8
    payoutStatus: Math.random() > 0.6 ? 'Paid' : 'No Payout',
    severity: Math.random() * 100
  }));

  return {
    kpis: {
      farmers_protected: 12500 + Math.floor(Math.random() * 5000),
      hectares_insured: 45000 + Math.floor(Math.random() * 10000),
      avg_payout_days: 12 + Math.floor(Math.random() * 15), // 12-27 days
      loss_ratio_ytd: solvencyTrend[4].ratio
    },
    solvency_history: solvencyTrend,
    basis_risk: basisRiskPoints,
    watchlist: basisRiskPoints.filter(p => p.vhi < 0.35).sort((a, b) => a.vhi - b.vhi)
  };
};

export default function ExecutiveDashboard() {
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // Simulate API Call
    setLoading(true);
    setTimeout(() => {
      setData(generateMockData(selectedYear));
      setLoading(false);
    }, 800);
  }, [selectedYear]);

  if (loading) return <LoadingSpinner message="Loading Command Center metrics..." />;

  // --- DERIVED METRICS ---
  const criticalRegions = data ? data.watchlist.filter((r: any) => r.vhi < 0.3) : [];
  const criticalCount = criticalRegions.length;

  // Insight Logic
  const currentLossRatio = data.kpis.loss_ratio_ytd;
  let solvencyStatus: 'success' | 'warning' | 'error' = 'success';
  let solvencyMessage = "Fund is healthy. Retained earnings are growing.";
  if (currentLossRatio > 0.8) {
    solvencyStatus = 'error';
    solvencyMessage = "UNSUSTAINABLE: Claims exceed 80% of premiums. Immediate capital injection or reinsurance trigger required.";
  } else if (currentLossRatio > 0.6) {
    solvencyStatus = 'warning';
    solvencyMessage = "CAUTION: Loss ratio approaching break-even point. Monitor claim frequency closely.";
  }

  const basisRiskIssues = data.basis_risk.filter((p: any) => p.vhi < 0.3 && p.payoutStatus !== 'Paid').length;
  let basisStatus: 'success' | 'warning' | 'error' = 'success';
  let basisMessage = "Model Performance Optimal: High correlation between triggers and ground truth.";
  if (basisRiskIssues > 2) {
    basisStatus = 'error';
    basisMessage = `CRITICAL MISMATCH: ${basisRiskIssues} regions show crop failure signals (Low VHI) but NO payout triggered. Verify ground data.`;
  } else if (basisRiskIssues > 0) {
    basisStatus = 'warning';
    basisMessage = `Model Drift Detected: ${basisRiskIssues} potential false negatives requires investigation.`;
  }

  // --- CHART CONFIGS ---
  const solvencyChartLayout = {
    autosize: true,
    height: 300,
    margin: { l: 60, r: 20, t: 30, b: 40 },
    showlegend: false,
    xaxis: { title: 'Year', fixedrange: true },
    yaxis: {
      title: { text: 'Loss Ratio', standoff: 15 },
      tickformat: '.0%',
      range: [0, 1.2],
      shapes: [
        { type: 'line', y0: 0.6, y1: 0.6, x0: 0, x1: 1, xref: 'paper', line: { color: '#ed6c02', width: 2, dash: 'dot' } }, // Warning Orange
        { type: 'line', y0: 0.8, y1: 0.8, x0: 0, x1: 1, xref: 'paper', line: { color: '#d32f2f', width: 2, dash: 'dot' } }  // Error Red
      ]
    }
  };

  const capitalChartLayout = {
    autosize: true,
    height: 300,
    margin: { l: 60, r: 20, t: 30, b: 40 },
    barmode: 'group', // Changed from 'stack' to 'group' for better comparison
    xaxis: { title: 'Year', fixedrange: true },
    yaxis: { title: 'Amount (USD)', tickprefix: '$', tickformat: 's' }, // Added tickformat 's' for SI prefix
    showlegend: true,
    legend: { orientation: 'h', y: 1.1 }
  };

  const basisRiskChartLayout = {
    autosize: true,
    height: 300,
    margin: { l: 50, r: 20, t: 30, b: 40 },
    xaxis: { title: 'Vegetation Health Index (VHI)', range: [0, 1] },
    yaxis: { title: 'Severity (%)' },
    showlegend: true,
    legend: { orientation: 'h', y: 1.1 }
  };

  return (
    <Box sx={{ pb: 4 }}>
      {/* HEADER */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Typography variant="h4" fontWeight="bold" color="text.primary" sx={{ mb: 0 }}>
              Executive Command Center
            </Typography>
            <Chip
              label="SIMULATION DATA"
              size="small"
              variant="outlined"
              color="info"
              sx={{ fontWeight: 'bold', borderRadius: 1 }}
            />
          </Box>
          <Typography variant="body1" color="text.secondary">
            Crop Insurance Portfolio Performance & Strategic Risks
          </Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Year</InputLabel>
          <Select value={selectedYear} label="Year" onChange={(e) => setSelectedYear(Number(e.target.value))}>
            {[2025, 2024, 2023, 2022, 2021].map(y => <MenuItem key={y} value={y}>{y}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>

      {/* GLOBAL ALERT BLOCK */}
      {criticalCount > 0 ? (
        <Alert severity="warning" variant="filled" sx={{ mb: 4, borderRadius: 2 }}>
          <strong>Attention Needed:</strong> {criticalCount} regions are showing signs of potential Basis Risk (Low VHI without Payout).
        </Alert>
      ) : (
        <Alert severity="success" variant="filled" sx={{ mb: 4, borderRadius: 2 }}>
          <strong>Portfolio Status Healthy:</strong> No basis risk anomalies detected in the current view.
        </Alert>
      )}

      {/* TOP ROW: KPI CARDS */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* 1. FARMERS PROTECTED */}
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Farmers Covered"
            value={data.kpis.farmers_protected.toLocaleString()}
            status="success"
            trend="up"
            subtitle="+12% vs LY"
            insight="Unique policyholders with active coverage."
            insightSeverity="info"
          />
        </Grid>

        {/* 2. HECTARES INSURED */}
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Hectares Insured"
            value={`${data.kpis.hectares_insured.toLocaleString()} ha`}
            status="success"
            subtitle={`Est. Yield Value: $${(data.kpis.hectares_insured * 450).toLocaleString()}`}
            insight="Total land area covered. Estimated yield based on crop type."
            insightSeverity="info"
          />
        </Grid>

        {/* 3. REPLANTING SPEED */}
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Replanting Speed"
            value={`${data.kpis.avg_payout_days} Days`}
            status={data.kpis.avg_payout_days > 21 ? 'error' : (data.kpis.avg_payout_days > 14 ? 'warning' : 'success')}
            trend={data.kpis.avg_payout_days > 21 ? 'down' : 'up'}
            subtitle={data.kpis.avg_payout_days > 21 ? 'Missed Replanting Window' : 'Optimal for Replanting'}
            insight="Avg days from Trigger to Payout. Target < 14 Days."
            insightSeverity={data.kpis.avg_payout_days > 21 ? 'error' : 'success'}
          />
        </Grid>

        {/* 4. SOLVENCY RATIO */}
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Loss Ratio (YTD)"
            value={`${(data.kpis.loss_ratio_ytd * 100).toFixed(1)}%`}
            status={solvencyStatus}
            subtitle={solvencyStatus === 'error' ? 'UNSUSTAINABLE' : (solvencyStatus === 'warning' ? 'Monitor Closely' : 'Sustainable')}
            insight="Payouts / Premiums collected. >80% is Critical."
            insightSeverity={solvencyStatus}
          />
        </Grid>
      </Grid>

      {/* MIDDLE ROW: STRATEGIC CHARTS */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* SOLVENCY TREND */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>Financial Solvency Trend (5-Year)</Typography>
            <Box sx={{ flexGrow: 1, minHeight: 300 }}>
              <Plot
                data={[
                  {
                    x: data.solvency_history.map((d: any) => d.year),
                    y: data.solvency_history.map((d: any) => d.ratio),
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: solvencyStatus === 'error' ? '#d32f2f' : '#1976d2', size: 8 },
                    line: { width: 3 }
                  }
                ]}
                layout={{
                  ...solvencyChartLayout,
                  height: 300,
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
                config={{ displayModeBar: false }}
              />
            </Box>
            {/* STRATEGIC INSIGHT BLOCK */}
            <Alert
              severity={solvencyStatus}
              sx={{ mt: 2, '& .MuiAlert-message': { width: '100%' } }}
            >
              <strong>Strategy Insight:</strong> {solvencyMessage}
            </Alert>
          </Paper>
        </Grid>

        {/* NEW: CAPITAL UTILIZATION CHART */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>Capital Utilization & Liquidity</Typography>
            <Box sx={{ flexGrow: 1, minHeight: 300 }}>
              <Plot
                data={[
                  {
                    x: data.solvency_history.map((d: any) => d.year),
                    y: data.solvency_history.map((d: any) => d.payout),
                    type: 'bar',
                    name: 'Payouts',
                    marker: { color: '#ed6c02' } // Orange
                  },
                  {
                    x: data.solvency_history.map((d: any) => d.year),
                    y: data.solvency_history.map((d: any) => d.reserves),
                    type: 'bar',
                    name: 'Available Reserves',
                    marker: { color: '#2e7d32' } // Green
                  }
                ]}
                layout={{ ...capitalChartLayout, height: 300 }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
                config={{ displayModeBar: false }}
              />
            </Box>
            <Alert severity="info" sx={{ mt: 2, bgcolor: '#e3f2fd' }}>
              <strong>Liquidity Check:</strong> Reserves (Green) vs Payouts (Orange). Gap indicates safety margin.
            </Alert>
          </Paper>
        </Grid>

        {/* BASIS RISK SCATTER - MOVED TO NEW ROW */}
        <Grid item xs={12} md={12}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>Basis Risk Indicator (Model Accuracy)</Typography>
            <Alert severity="info" sx={{ mb: 2, py: 0, bgcolor: '#e3f2fd' }}>
              <Typography variant="body2">
                <strong>How to read:</strong> X-Axis = VHI (0=Dead Crops, 1=Healthy). Red X markers on the <strong>LEFT side (VHI &lt; 0.3, No Payout)</strong> are False Negatives (Basis Risk).
              </Typography>
            </Alert>
            <Box sx={{ flexGrow: 1, minHeight: 300 }}>
              <Plot
                data={[
                  {
                    x: data.basis_risk.filter((d: any) => d.payoutStatus === 'Paid').map((d: any) => d.vhi),
                    y: data.basis_risk.filter((d: any) => d.payoutStatus === 'Paid').map((d: any) => d.severity),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Paid (Success)',
                    marker: { color: '#2e7d32', size: 10, symbol: 'circle' }
                  },
                  {
                    x: data.basis_risk.filter((d: any) => d.payoutStatus !== 'Paid').map((d: any) => d.vhi),
                    y: data.basis_risk.filter((d: any) => d.payoutStatus !== 'Paid').map((d: any) => d.severity),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'No Payout',
                    marker: { color: '#d32f2f', size: 10, symbol: 'x' }
                  }
                ]}
                layout={{ ...basisRiskChartLayout, height: 300 }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
                config={{ displayModeBar: false }}
              />
            </Box>
            {/* STRATEGIC INSIGHT BLOCK */}
            <Alert
              severity={basisStatus}
              sx={{ mt: 2, '& .MuiAlert-message': { width: '100%' } }}
            >
              <strong>Model Check:</strong> {basisMessage}
            </Alert>
          </Paper>
        </Grid>
      </Grid>

      {/* BOTTOM ROW: WATCHLIST */}
      <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Priority Watchlist (Low VHI Regions)</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead sx={{ bgcolor: '#eee' }}>
            <TableRow>
              <TableCell><strong>Region</strong></TableCell>
              <TableCell><strong>Current VHI</strong></TableCell>
              <TableCell><strong>Severity %</strong></TableCell>
              <TableCell align="center"><strong>Pre-Trigger Status</strong></TableCell>
              <TableCell align="right"><strong>Est. Payout Needed</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.watchlist.map((row: any) => (
              <TableRow key={row.region}>
                <TableCell>{row.region}</TableCell>
                <TableCell sx={{
                  color: row.vhi < 0.3 ? 'error.main' : 'warning.main',
                  fontWeight: 'bold'
                }}>
                  {row.vhi.toFixed(2)}
                </TableCell>
                <TableCell>{row.severity.toFixed(1)}%</TableCell>
                <TableCell align="center">
                  <Chip
                    label={row.vhi < 0.3 ? "CRITICAL" : "MONITOR"}
                    color={row.vhi < 0.3 ? "error" : "warning"}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">${(row.severity * 1500).toLocaleString()}</TableCell>
              </TableRow>
            ))}
            {data.watchlist.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">No critical regions detected.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
