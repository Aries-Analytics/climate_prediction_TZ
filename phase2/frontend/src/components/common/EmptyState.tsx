import { Box, Typography, Paper } from '@mui/material'
import InboxIcon from '@mui/icons-material/Inbox'

interface EmptyStateProps {
  message?: string
  description?: string
  icon?: React.ReactNode
}

export default function EmptyState({ 
  message = 'No data available', 
  description,
  icon 
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 300,
        p: 3
      }}
    >
      <Paper 
        sx={{ 
          p: 4, 
          maxWidth: 400, 
          textAlign: 'center',
          bgcolor: 'background.default'
        }}
        elevation={0}
      >
        {icon || <InboxIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />}
        <Typography variant="h6" gutterBottom color="text.secondary">
          {message}
        </Typography>
        {description && (
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        )}
      </Paper>
    </Box>
  )
}
