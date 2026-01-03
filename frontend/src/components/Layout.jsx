import { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
} from '@mui/material'
import { FlightTakeoff, AccountCircle } from '@mui/icons-material'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Layout = ({ children }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState(null)

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    logout()
    handleMenuClose()
    navigate('/')
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Toolbar>
          <FlightTakeoff sx={{ mr: 2 }} />
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{
              flexGrow: 1,
              textDecoration: 'none',
              color: 'inherit',
              fontWeight: 'bold',
            }}
          >
            Airport Project
          </Typography>
          <Button color="inherit" component={Link} to="/search" sx={{ mr: 2 }}>
            Search Flights
          </Button>
          {user ? (
            <>
              <IconButton
                size="large"
                edge="end"
                aria-label="account menu"
                onClick={handleMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(255,255,255,0.2)' }}>
                  {user.email?.[0]?.toUpperCase() || <AccountCircle />}
                </Avatar>
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem component={Link} to="/dashboard" onClick={handleMenuClose}>
                  Dashboard
                </MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button color="inherit" component={Link} to="/login" sx={{ mr: 1 }}>
                Login
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/register"
                variant="outlined"
                sx={{ borderColor: 'rgba(255,255,255,0.5)' }}
              >
                Register
              </Button>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ flex: 1, py: 4 }}>
        {children}
      </Container>
      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          backgroundColor: (theme) =>
            theme.palette.mode === 'light' ? theme.palette.grey[200] : theme.palette.grey[800],
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="body2" color="text.secondary" align="center">
            © {new Date().getFullYear()} Airport Project. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  )
}

export default Layout

