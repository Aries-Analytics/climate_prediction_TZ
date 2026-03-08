import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    allowedHosts: ['hewasense.majaribio.com', 'api.hewasense.majaribio.com'],
    watch: {
      usePolling: true,
      interval: 1000,
    },
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Isolate the 3MB Plotly bundle so it caches independently
          plotly: ['plotly.js', 'react-plotly.js'],
          // Isolate mapping libraries
          maps: ['leaflet', 'react-leaflet'],
          // Isolate chart.js separately from plotly
          chartjs: ['chart.js', 'react-chartjs-2'],
          // MUI into its own cacheable chunk
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
        }
      }
    }
  }
})
