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
import LogoutIcon from '@mui/icons-material/Logout'
import { useAuth } from '../../contexts/AuthContext'

interface SidebarProps {
  onClose?: () => void
}

const menuItems = [
  { text: 'Executive Dashboard', icon: <DashboardIcon />, path: '/dashboard/executive' },
  { text: 'Model Performance', icon: <ModelTrainingIcon />, path: '/dashboard/models' },
  { text: 'Trigger Events', icon: <WarningIcon />, path: '/dashboard/triggers' },
  { text: 'Climate Insights', icon: <CloudIcon />, path: '/dashboard/climate' },
  { text: 'Risk Management', icon: <AssessmentIcon />, path: '/dashboard/risk' },
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
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo/Title */}
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="h6" color="primary" fontWeight="bold">
          Climate Dashboard
        </Typography>
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
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
          <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main' }}>
            {user?.username?.charAt(0).toUpperCase()}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2" fontWeight="bold">
              {user?.username}
            </Typography>
            <Typography variant="caption" color="text.secondary">
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
