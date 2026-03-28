import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import Sidebar from './Sidebar'

const HS_NAVY = '#0a1628'
const HS_SIDEBAR = '#0e2440'
const HS_TEAL_BORDER = 'rgba(45, 212, 191, 0.2)'

const DRAWER_WIDTH = 240

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          backgroundColor: HS_NAVY,
          borderBottom: `1px solid ${HS_TEAL_BORDER}`,
          boxShadow: '0 2px 12px rgba(0,0,0,0.4)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box
            component="img"
            src="/hewasense-icon.png"
            alt="HewaSense"
            sx={{ height: 46, width: 46, flexShrink: 0, mr: 1.5 }}
          />
          <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 800, letterSpacing: '-0.5px' }}>
            Hewa<Box component="span" sx={{ color: '#2dd4bf' }}>Sense</Box>
          </Typography>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, backgroundColor: HS_SIDEBAR },
          }}
        >
          <Sidebar onClose={handleDrawerToggle} />
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, backgroundColor: HS_SIDEBAR },
          }}
          open
        >
          <Sidebar />
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: 8,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}
