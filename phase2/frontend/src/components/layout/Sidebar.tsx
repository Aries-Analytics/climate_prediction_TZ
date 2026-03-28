import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Avatar,
  IconButton
} from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import ModelTrainingIcon from '@mui/icons-material/ModelTraining'
import WarningIcon from '@mui/icons-material/Warning'
import CloudIcon from '@mui/icons-material/Cloud'
import AssessmentIcon from '@mui/icons-material/Assessment'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings'
import LogoutIcon from '@mui/icons-material/Logout'
import ScienceIcon from '@mui/icons-material/Science'
import { useAuth } from '../../contexts/AuthContext'

interface SidebarProps {
  onClose?: () => void
}

const menuItems = [
  { text: 'Executive Snapshot', icon: <DashboardIcon />, path: '/dashboard/executive', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Model Performance', icon: <ModelTrainingIcon />, path: '/dashboard/models', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Trigger Events', icon: <WarningIcon />, path: '/dashboard/triggers', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Climate Insights', icon: <CloudIcon />, path: '/dashboard/climate', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Risk Management', icon: <AssessmentIcon />, path: '/dashboard/risk', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Early Warnings', icon: <TrendingUpIcon />, path: '/dashboard/forecasts', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Evidence Pack', icon: <ScienceIcon />, path: '/dashboard/evidence', roles: ['analyst', 'manager', 'admin'] },
  { text: 'Admin Panel', icon: <AdminPanelSettingsIcon />, path: '/dashboard/admin', roles: ['admin'] },
]

export default function Sidebar({ onClose }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const handleNavigation = (path: string) => {
    navigate(path)
    if (onClose) onClose()
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', color: 'white' }}>
      {/* Logo/Title */}
      <Box sx={{ p: 2, textAlign: 'center', borderBottom: '1px solid rgba(45, 212, 191, 0.2)' }}>
        <Typography variant="h6" fontWeight={700} sx={{ color: '#2dd4bf', letterSpacing: '0.03em' }}>
          Climate Dashboard
        </Typography>
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ flexGrow: 1 }}>
        {menuItems
          .filter((item) => !item.roles || item.roles.includes(user?.role || ''))
          .map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  color: 'rgba(255,255,255,0.8)',
                  '& .MuiListItemIcon-root': { color: 'rgba(255,255,255,0.5)' },
                  '&:hover': { backgroundColor: 'rgba(45,212,191,0.08)', color: 'white', '& .MuiListItemIcon-root': { color: '#2dd4bf' } },
                  '&.Mui-selected': { backgroundColor: 'rgba(45,212,191,0.15)', color: 'white', '& .MuiListItemIcon-root': { color: '#2dd4bf' } },
                  '&.Mui-selected:hover': { backgroundColor: 'rgba(45,212,191,0.2)' },
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
      </List>

      <Divider />

      {/* User Profile */}
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: '#2dd4bf', color: '#0a1628' }}>
            {user?.username?.charAt(0).toUpperCase()}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2" fontWeight="bold" sx={{ color: 'white' }}>
              {user?.username}
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
              {user?.role}
            </Typography>
          </Box>
          <IconButton size="small" onClick={handleLogout} title="Logout">
            <LogoutIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
    </Box>
  )
}
