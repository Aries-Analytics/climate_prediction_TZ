import { Box, Grid, Card, CardContent, Typography } from '@mui/material'

interface PortfolioRiskData {
    farmersAtRisk: number
    totalFarmers: number
    riskPercentage: number
    expectedPayouts: number
    byTriggerType: {
        drought: { count: number; payout: number }
        flood: { count: number; payout: number }
        crop_failure: { count: number; payout: number }
    }
    reserves: number
    bufferPercentage: number
    timeframeDays: number
    pilot_location_id?: number  // Morogoro pilot location ID
    pilot_location_name?: string  // Morogoro pilot location name
}

interface PortfolioRiskCardsProps {
    data: PortfolioRiskData | null
    loading?: boolean
}

export default function PortfolioRiskCards({ data, loading }: PortfolioRiskCardsProps) {
    if (loading || !data) {
        return (
            <Grid container spacing={3}>
                {[1, 2, 3].map((i) => (
                    <Grid item xs={12} md={4} key={i}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" color="text.secondary" gutterBottom>
                                    Loading...
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        )
    }

    const formatCurrency = (value: number) => {
        return '$' + Math.round(value).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    }

    const getRiskColor = () => {
        if (data.riskPercentage >= 15) return { main: '#f44336', light: '#ffebee', dark: '#c62828' }
        if (data.riskPercentage >= 10) return { main: '#ff9800', light: '#fff3e0', dark: '#f57c00' }
        return { main: '#4caf50', light: '#e8f5e9', dark: '#388e3c' }
    }

    const getBufferColor = () => {
        if (data.bufferPercentage >= 70) return { main: '#4caf50', light: '#e8f5e9', dark: '#388e3c' }
        if (data.bufferPercentage >= 50) return { main: '#ff9800', light: '#fff3e0', dark: '#f57c00' }
        return { main: '#f44336', light: '#ffebee', dark: '#c62828' }
    }

    const riskColor = getRiskColor()
    const bufferColor = getBufferColor()

    return (
        <Grid container spacing={3}>
            {/* Card 1: Farmers at Risk - Match TriggersDashboard styling */}
            <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                    <CardContent>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            Farmers at Risk ({data.timeframeDays}d)
                        </Typography>
                        <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                            {data.farmersAtRisk.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1, mb: 1 }}>
                            of {data.totalFarmers.toLocaleString()} farmers ({data.riskPercentage}%)
                        </Typography>
                        <Typography variant="caption" color="primary" sx={{ fontWeight: 600, display: 'block', mb: 1 }}>
                            📍 Morogoro Pilot (Location ID: 6)
                        </Typography>
                        <Box sx={{
                            mt: 2,
                            p: 1.5,
                            bgcolor: riskColor.light,
                            borderRadius: 1,
                            borderLeft: `4px solid ${riskColor.main}`
                        }}>
                            <Typography variant="body2" color={riskColor.dark} sx={{ lineHeight: 1.6 }}>
                                <strong>Payout by Type:</strong><br />
                                Drought: {formatCurrency(data.byTriggerType.drought.payout)} |
                                Flood: {formatCurrency(data.byTriggerType.flood.payout)} |
                                Crop: {formatCurrency(data.byTriggerType.crop_failure.payout)}
                            </Typography>
                        </Box>
                    </CardContent>
                </Card>
            </Grid>

            {/* Card 2: Expected Payouts - Green for money */}
            <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                    <CardContent>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            Expected Payouts
                        </Typography>
                        <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#388e3c' }}>
                            {formatCurrency(data.expectedPayouts)}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1, mb: 1 }}>
                            Total projected payouts
                        </Typography>
                        <Box sx={{
                            mt: 2,
                            p: 1.5,
                            bgcolor: '#e8f5e9',
                            borderRadius: 1,
                            borderLeft: '4px solid #4caf50'
                        }}>
                            <Typography variant="body2" color="success.dark" sx={{ lineHeight: 1.6 }}>
                                <strong>By Type:</strong> Drought: {formatCurrency(data.byTriggerType.drought.payout)} |
                                Flood: {formatCurrency(data.byTriggerType.flood.payout)} |
                                Crop: {formatCurrency(data.byTriggerType.crop_failure.payout)}
                            </Typography>
                        </Box>
                    </CardContent>
                </Card>
            </Grid>

            {/* Card 3: Coverage Status */}
            <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                    <CardContent>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            Reserve Coverage
                        </Typography>
                        <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                            {formatCurrency(data.reserves)}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1, mb: 1 }}>
                            Current cash reserves
                        </Typography>
                        <Box sx={{
                            mt: 2,
                            p: 1.5,
                            bgcolor: bufferColor.light,
                            borderRadius: 1,
                            borderLeft: `4px solid ${bufferColor.main}`
                        }}>
                            <Typography variant="body2" color={bufferColor.dark} sx={{ lineHeight: 1.6 }}>
                                <strong>Buffer: {data.bufferPercentage.toFixed(1)}%</strong><br />
                                {formatCurrency(data.reserves - data.expectedPayouts)} remaining after expected payouts
                            </Typography>
                        </Box>
                    </CardContent>
                </Card>
            </Grid>
        </Grid>
    )
}
