import Plot from 'react-plotly.js'
import { Box, IconButton, Tooltip, Menu, MenuItem } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { useState } from 'react'

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
    ...layout
  }

  const defaultConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: title || 'chart',
      height: 800,
      width: 1200,
      scale: 2
    },
    ...config
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
      <Plot
        ref={(ref: any) => setPlotRef(ref)}
        data={data}
        layout={defaultLayout}
        config={defaultConfig}
        style={{ width: '100%', height: '100%', minHeight: '400px' }}
        useResizeHandler={true}
        onRelayout={onRelayout}  // Forward the event handler
      />
    </Box>
  )
}
