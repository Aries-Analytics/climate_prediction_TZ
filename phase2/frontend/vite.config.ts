import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Polyfill Node built-ins required by Plotly's ndarray/typedarray-pool
      'buffer/': 'buffer/',
      buffer: 'buffer/',
    },
  },
  define: {
    // Ensure global Buffer is available for dependencies that expect it
    'globalThis.Buffer': ['buffer', 'Buffer'],
  },
  server: {
    port: 3000,
    host: true,
    allowedHosts: ['hewasense.majaribio.com', 'api.hewasense.majaribio.com'],
    watch: {
      usePolling: true,
      interval: 1000,
      ignored: ['**/Dockerfile*', '**/.dockerignore', '**/nginx*', '**/*.sh'],
    },
    fs: {
      deny: ['Dockerfile', 'Dockerfile.dev', '.dockerignore'],
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
          // Landing page icons — separate from dashboard bundle
          landing: ['lucide-react'],
        }
      }
    }
  }
})
