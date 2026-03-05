import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { CircularProgress, Box } from '@mui/material'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/LoginPage'

// Lazy load dashboard pages for code splitting
const ExecutiveDashboard = lazy(() => import('./pages/ExecutiveDashboard'))
const ModelPerformanceDashboard = lazy(() => import('./pages/ModelPerformanceDashboard'))
const TriggersDashboard = lazy(() => import('./pages/TriggersDashboard'))
const ClimateInsightsDashboard = lazy(() => import('./pages/ClimateInsightsDashboard'))
const RiskManagementDashboard = lazy(() => import('./pages/RiskManagementDashboard'))
const ForecastDashboard = lazy(() => import('./pages/ForecastDashboard'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const EvidencePackDashboard = lazy(() => import('./pages/EvidencePackDashboard'))

// Loading component
const LoadingFallback = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
    <CircularProgress />
  </Box>
)

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="executive" element={<Suspense fallback={<LoadingFallback />}><ExecutiveDashboard /></Suspense>} />
              <Route path="models" element={<Suspense fallback={<LoadingFallback />}><ModelPerformanceDashboard /></Suspense>} />
              <Route path="triggers" element={<Suspense fallback={<LoadingFallback />}><TriggersDashboard /></Suspense>} />
              <Route path="climate" element={<Suspense fallback={<LoadingFallback />}><ClimateInsightsDashboard /></Suspense>} />
              <Route path="risk" element={<Suspense fallback={<LoadingFallback />}><RiskManagementDashboard /></Suspense>} />
              <Route path="forecasts" element={<Suspense fallback={<LoadingFallback />}><ForecastDashboard /></Suspense>} />
              <Route path="evidence" element={<Suspense fallback={<LoadingFallback />}><EvidencePackDashboard /></Suspense>} />
              <Route path="admin" element={<Suspense fallback={<LoadingFallback />}><AdminDashboard /></Suspense>} />
            </Route>
            <Route path="/" element={<Navigate to="/dashboard/executive" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
