import { lazy, Suspense, useState } from 'react'
import { Box, IconButton, Tooltip, Menu, MenuItem, CircularProgress } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'

// Lazy-load Plotly (4.7 MB minified) so it doesn't block initial dashboard render
const Plot = lazy(() => import('react-plotly.js'))

interface ChartProps {
  data: any[]
  layout?: any
  config?: any
  title?: string
  onRelayout?: (event: any) => void  // Add event handler prop
}

export default function Chart({ data, layout = {}, config = {}, title, onRelayout }: ChartProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [plotRef, setPlotRef] = useState<any>(null)

  const defaultLayout = {
    autosize: true,
    margin: { l: 50, r: 50, t: 50, b: 50 },
    ...layout,
    dragmode: false, // Disable drag to zoom/pan (force override)
    xaxis: { ...(layout.xaxis || {}), fixedrange: true },
    yaxis: { ...(layout.yaxis || {}), fixedrange: true },
    yaxis2: { ...(layout.yaxis2 || {}), fixedrange: true },
  }

  const defaultConfig = {
    ...config,
    responsive: true,
    scrollZoom: false, // Force disable
    displayModeBar: false, // Force hide mode bar to prevent interactions
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: title || 'chart',
      height: 800,
      width: 1200,
      scale: 2
    }
  }

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleExport = (format: 'png' | 'svg' | 'pdf') => {
    if (plotRef && plotRef.el) {
      const filename = title || 'chart'

      // Use Plotly's downloadImage function
      const Plotly = (window as any).Plotly
      if (Plotly && Plotly.downloadImage) {
        Plotly.downloadImage(plotRef.el, {
          format: format,
          width: 1200,
          height: 800,
          filename: filename
        })
      }
    }
    handleClose()
  }

  return (
    <Box sx={{ position: 'relative', width: '100%', minHeight: '400px' }}>
      <Box sx={{ position: 'absolute', top: 0, right: 0, zIndex: 1 }}>
        <Tooltip title="Export Chart">
          <IconButton size="small" onClick={handleExportClick}>
            <DownloadIcon />
          </IconButton>
        </Tooltip>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleClose}
        >
          <MenuItem onClick={() => handleExport('png')}>Export as PNG</MenuItem>
          <MenuItem onClick={() => handleExport('svg')}>Export as SVG</MenuItem>
          <MenuItem onClick={() => handleExport('pdf')}>Export as PDF</MenuItem>
        </Menu>
      </Box>
      <Suspense fallback={<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}><CircularProgress size={32} /></Box>}>
        <Plot
          ref={(ref: any) => setPlotRef(ref)}
          data={data}
          layout={defaultLayout}
          config={defaultConfig}
          style={{ width: '100%', height: '100%', minHeight: '400px' }}
          useResizeHandler={true}
          onRelayout={onRelayout}
        />
      </Suspense>
    </Box>
  )
}
