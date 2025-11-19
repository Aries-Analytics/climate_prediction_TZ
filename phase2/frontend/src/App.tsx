import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/LoginPage'
import ExecutiveDashboard from './pages/ExecutiveDashboard'
import ModelPerformanceDashboard from './pages/ModelPerformanceDashboard'
import TriggersDashboard from './pages/TriggersDashboard'
import ClimateInsightsDashboard from './pages/ClimateInsightsDashboard'
import RiskManagementDashboard from './pages/RiskManagementDashboard'

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
              <Route path="executive" element={<ExecutiveDashboard />} />
              <Route path="models" element={<ModelPerformanceDashboard />} />
              <Route path="triggers" element={<TriggersDashboard />} />
              <Route path="climate" element={<ClimateInsightsDashboard />} />
              <Route path="risk" element={<RiskManagementDashboard />} />
            </Route>
            <Route path="/" element={<Navigate to="/dashboard/executive" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
