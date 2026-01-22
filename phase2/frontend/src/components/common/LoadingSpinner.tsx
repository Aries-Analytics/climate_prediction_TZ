import { Box, CircularProgress, Typography } from '@mui/material'

interface LoadingSpinnerProps {
  message?: string
  size?: number | string
}

export default function LoadingSpinner({ message = 'Loading...', size = 40 }: LoadingSpinnerProps) {
  // If size is small (e.g. for buttons), render inline without text/box
  const isInline = typeof size === 'number' && size < 30

  if (isInline) {
    return <CircularProgress size={size} color="inherit" />
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 200,
        gap: 2
      }}
    >
      <CircularProgress size={size} />
      <Typography color="text.secondary">{message}</Typography>
    </Box>
  )
}
