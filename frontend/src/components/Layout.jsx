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
  Grid,
  Link as MuiLink,
  Divider,
} from '@mui/material'
import { 
  FlightTakeoff, 
  AccountCircle, 
  Email, 
  Phone, 
  LocationOn,
  Facebook,
  Twitter,
  LinkedIn,
  Instagram
} from '@mui/icons-material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Layout.css'

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
            component={RouterLink}
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
          <Button color="inherit" component={RouterLink} to="/search" sx={{ mr: 2 }}>
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
                <MenuItem component={RouterLink} to="/dashboard" onClick={handleMenuClose}>
                  Dashboard
                </MenuItem>
                <MenuItem onClick={handleLogout}>Logout</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button color="inherit" component={RouterLink} to="/login" sx={{ mr: 1 }}>
                Login
              </Button>
              <Button
                color="inherit"
                component={RouterLink}
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
      <Box sx={{ flex: 1, width: '100%', py: 4 }}>
        {children}
      </Box>
      <Box
        component="footer"
        className="footer"
      >
        <Container maxWidth="xl">
          <Grid container spacing={4} sx={{ py: 4 }}>
            {/* Company Info */}
            <Grid item xs={12} md={4}>
              <Box className="footer-section">
                <Box className="footer-logo">
                  <FlightTakeoff sx={{ fontSize: 40, mr: 1 }} />
                  <Typography variant="h6" className="footer-company-name">
                    Airport Project
                  </Typography>
                </Box>
                <Typography variant="body2" className="footer-description">
                  Your trusted partner for flight and hotel bookings. 
                  We make travel planning simple, secure, and affordable.
                </Typography>
                <Box className="footer-social">
                  <IconButton 
                    className="social-icon" 
                    component="a" 
                    href="https://facebook.com" 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Facebook />
                  </IconButton>
                  <IconButton 
                    className="social-icon" 
                    component="a" 
                    href="https://twitter.com" 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Twitter />
                  </IconButton>
                  <IconButton 
                    className="social-icon" 
                    component="a" 
                    href="https://linkedin.com" 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <LinkedIn />
                  </IconButton>
                  <IconButton 
                    className="social-icon" 
                    component="a" 
                    href="https://instagram.com" 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Instagram />
                  </IconButton>
                </Box>
              </Box>
            </Grid>

            {/* Quick Links */}
            <Grid item xs={12} sm={6} md={2}>
              <Box className="footer-section">
                <Typography variant="h6" className="footer-heading">
                  Quick Links
                </Typography>
                <Box className="footer-links">
                  <MuiLink component={RouterLink} to="/search" className="footer-link">
                    Search Flights
                  </MuiLink>
                  <MuiLink component={RouterLink} to="/hotels" className="footer-link">
                    Book Hotels
                  </MuiLink>
                  <MuiLink component={RouterLink} to="/dashboard" className="footer-link">
                    My Bookings
                  </MuiLink>
                  <MuiLink component={RouterLink} to="/" className="footer-link">
                    About Us
                  </MuiLink>
                </Box>
              </Box>
            </Grid>

            {/* Support */}
            <Grid item xs={12} sm={6} md={3}>
              <Box className="footer-section">
                <Typography variant="h6" className="footer-heading">
                  Support
                </Typography>
                <Box className="footer-links">
                  <MuiLink href="#" className="footer-link">
                    Help Center
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Contact Us
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    FAQ
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Terms & Conditions
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Privacy Policy
                  </MuiLink>
                </Box>
              </Box>
            </Grid>

            {/* Contact Info */}
            <Grid item xs={12} md={3}>
              <Box className="footer-section">
                <Typography variant="h6" className="footer-heading">
                  Contact Us
                </Typography>
                <Box className="footer-contact">
                  <Box className="contact-item">
                    <Email className="contact-icon" />
                    <Typography variant="body2" className="contact-text">
                      support@airportproject.com
                    </Typography>
                  </Box>
                  <Box className="contact-item">
                    <Phone className="contact-icon" />
                    <Typography variant="body2" className="contact-text">
                      +1 (555) 123-4567
                    </Typography>
                  </Box>
                  <Box className="contact-item">
                    <LocationOn className="contact-icon" />
                    <Typography variant="body2" className="contact-text">
                      123 Airport Blvd, Suite 100<br />
                      New York, NY 10001
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>

          <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.2)' }} />

          {/* Copyright */}
          <Box className="footer-bottom">
            <Typography variant="body2" className="footer-copyright">
              © {new Date().getFullYear()} Airport Project. All rights reserved.
            </Typography>
            <Typography variant="body2" className="footer-credits">
              Developed with ❤️ by Airport Project Team
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}

export default Layout
