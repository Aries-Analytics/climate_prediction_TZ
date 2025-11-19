import { Card, CardContent, Typography, Box, Chip, Tooltip } from '@mui/material'
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
}

export default function KPICard({ title, value, status = 'success', trend, subtitle, tooltip }: KPICardProps) {
  const statusColors = {
    success: 'success.main',
    warning: 'warning.main',
    error: 'error.main'
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography color="text.secondary" variant="body2">
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
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
