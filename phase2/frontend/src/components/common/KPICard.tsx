import { Card, CardContent, Typography, Box, Chip, Tooltip, Alert } from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'

interface KPICardProps {
  title: string
  value: string | number
  status?: 'success' | 'warning' | 'error'
  trend?: 'up' | 'down'
  subtitle?: string
  tooltip?: string
  insight?: string
  insightSeverity?: 'info' | 'warning' | 'error' | 'success'
}

export default function KPICard({ title, value, status = 'success', trend, subtitle, tooltip, insight, insightSeverity = 'info' }: KPICardProps) {
  const statusColors = {
    success: 'success.main',
    warning: 'warning.main',
    error: 'error.main'
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography color="text.secondary" variant="body2" fontWeight="medium">
            {title}
          </Typography>
          {tooltip && (
            <Tooltip title={tooltip} arrow>
              <InfoOutlinedIcon fontSize="small" sx={{ color: 'text.secondary', cursor: 'help' }} />
            </Tooltip>
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, my: 1 }}>
          <Typography variant="h4" component="div" color={statusColors[status]}>
            {value}
          </Typography>
          {trend && (
            <Chip
              icon={trend === 'up' ? <TrendingUpIcon /> : <TrendingDownIcon />}
              label={trend === 'up' ? 'Up' : 'Down'}
              size="small"
              color={trend === 'up' ? 'success' : 'error'}
            />
          )}
        </Box>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {subtitle}
          </Typography>
        )}

        {/* Visible Info Block */}
        {insight && (
          <Alert
            severity={insightSeverity}
            sx={{
              mt: 2,
              py: 0.5,
              px: 1,
              '& .MuiAlert-message': { fontSize: '0.75rem' },
              '& .MuiAlert-icon': { fontSize: '1rem', mr: 1 }
            }}
          >
            {insight}
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
