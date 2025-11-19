import Plot from 'react-plotly.js'
import { Box, IconButton, Tooltip } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'

interface ChartProps {
  data: any[]
  layout?: any
  config?: any
  onExport?: () => void
}

export default function Chart({ data, layout = {}, config = {}, onExport }: ChartProps) {
  const defaultLayout = {
    autosize: true,
    margin: { l: 50, r: 50, t: 50, b: 50 },
    ...layout
  }

  const defaultConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    ...config
  }

  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      {onExport && (
        <Box sx={{ position: 'absolute', top: 0, right: 0, zIndex: 1 }}>
          <Tooltip title="Export Chart">
            <IconButton size="small" onClick={onExport}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>
      )}
      <Plot
        data={data}
        layout={defaultLayout}
        config={defaultConfig}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </Box>
  )
}
