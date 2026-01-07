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
  Instagram,
  SmartToy
} from '@mui/icons-material'
import { Link as RouterLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { t } from '../translations/translations'
import './Layout.css'

const Layout = ({ children }) => {
  const { user, logout } = useAuth()
  const { language, toggleLanguage, currencySymbol } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const [anchorEl, setAnchorEl] = useState(null)
  
  // Pages that should be full-width (no container)
  const fullWidthPages = ['/', '/search', '/results', '/booking', '/chat', '/hotels', '/favorites', '/my-flights', '/profile']
  const isFullWidth = fullWidthPages.some(path => location.pathname === path || location.pathname.startsWith(path + '/'))
  
  // Routes that use dark orange theme background for the whole viewport
  const darkThemeRoutes = ['/chat', '/hotels', '/favorites', '/my-flights', '/profile']
  const isDarkTheme = darkThemeRoutes.some(path => location.pathname === path || location.pathname.startsWith(path + '/'))

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
      <AppBar
        position="static"
        sx={{
          background:
            'linear-gradient(135deg, rgba(255,140,0,0.12) 0%, rgba(255,87,34,0.12) 100%), #0b0b0b',
          borderBottom: '1px solid rgba(255,153,0,0.25)',
          boxShadow: '0 2px 10px rgba(255,153,0,0.08)',
        }}
      >
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
            DavaiPoihalu
          </Typography>
          <Button color="inherit" component={RouterLink} to="/search" sx={{ mr: 2 }}>
            {t('searchFlights', language)}
          </Button>
          <Button 
            component={RouterLink}
            to="/chat"
            className="ai-chat-button"
            startIcon={<SmartToy />}
            sx={{ mr: 2 }}
          >
            {t('aiChat', language)}
          </Button>
          <Button color="inherit" component={RouterLink} to="/my-flights" sx={{ mr: 2 }}>
            Мої рейси
          </Button>
          <Button color="inherit" component={RouterLink} to="/favorites" sx={{ mr: 2 }}>
            Обране
          </Button>
          <Button 
            color="inherit" 
            onClick={toggleLanguage}
            sx={{ mr: 2, minWidth: '80px' }}
          >
            {language === 'uk' ? '🇺🇦 UKR' : '🇺🇸 ENG'} {currencySymbol}
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
                  {t('dashboard', language)}
                </MenuItem>
                <MenuItem component={RouterLink} to="/profile" onClick={handleMenuClose}>
                  Профіль
                </MenuItem>
                <MenuItem component={RouterLink} to="/my-flights" onClick={handleMenuClose}>
                  Мої рейси
                </MenuItem>
                <MenuItem onClick={handleLogout}>{t('logout', language)}</MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button color="inherit" component={RouterLink} to="/login" sx={{ mr: 1 }}>
                {t('login', language)}
              </Button>
              <Button
                color="inherit"
                component={RouterLink}
                to="/register"
                variant="outlined"
                sx={{ borderColor: 'rgba(255,255,255,0.5)' }}
              >
                {t('register', language)}
              </Button>
            </>
          )}
        </Toolbar>
      </AppBar>
      {isFullWidth ? (
        <Box sx={{ 
          flex: 1,
          ...(isDarkTheme && {
            background: 'radial-gradient(1200px 600px at 20% 10%, rgba(255,140,0,0.15) 0%, rgba(0,0,0,0.0) 60%), radial-gradient(1000px 500px at 80% 90%, rgba(255,87,34,0.12) 0%, rgba(0,0,0,0) 60%), #0b0b0b',
          })
        }}>
          {children}
        </Box>
      ) : (
        <Container maxWidth="xl" sx={{ 
          flex: 1, 
          py: 4,
          ...(isDarkTheme && {
            background: 'radial-gradient(1200px 600px at 20% 10%, rgba(255,140,0,0.15) 0%, rgba(0,0,0,0.0) 60%), radial-gradient(1000px 500px at 80% 90%, rgba(255,87,34,0.12) 0%, rgba(0,0,0,0) 60%), #0b0b0b',
          })
        }}>
          {children}
        </Container>
      )}
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
                    DavaiPoihalu
                  </Typography>
                </Box>
                <Typography variant="body2" className="footer-description">
                  Ваш надійний партнер для бронювання рейсів та готелів.
                  Ми робимо планування подорожей простим, безпечним і доступним.
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
                  Швидкі посилання
                </Typography>
                <Box className="footer-links">
                  <MuiLink component={RouterLink} to="/search" className="footer-link">
                    Пошук рейсів
                  </MuiLink>
                  <MuiLink component={RouterLink} to="/hotels" className="footer-link">
                    Бронювання готелів
                  </MuiLink>
                  <MuiLink component={RouterLink} to="/dashboard" className="footer-link">
                    Мої бронювання
                  </MuiLink>
                  <MuiLink component={RouterLink} to="/" className="footer-link">
                    Про нас
                  </MuiLink>
                </Box>
              </Box>
            </Grid>

            {/* Support */}
            <Grid item xs={12} sm={6} md={3}>
              <Box className="footer-section">
                <Typography variant="h6" className="footer-heading">
                  Підтримка
                </Typography>
                <Box className="footer-links">
                  <MuiLink href="#" className="footer-link">
                    Центр допомоги
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Звʼязатися з нами
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Питання та відповіді
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Умови та положення
                  </MuiLink>
                  <MuiLink href="#" className="footer-link">
                    Політика конфіденційності
                  </MuiLink>
                </Box>
              </Box>
            </Grid>

            {/* Contact Info */}
            <Grid item xs={12} md={3}>
              <Box className="footer-section">
                <Typography variant="h6" className="footer-heading">
                  Звʼязатися з нами
                </Typography>
                <Box className="footer-contact">
                  <Box className="contact-item">
                    <Email className="contact-icon" />
                    <Typography variant="body2" className="contact-text">
                      hordii.kotsiuba.oi.2023@lpnu.ua
                    </Typography>
                  </Box>
                  <Box className="contact-item">
                    <Phone className="contact-icon" />
                    <Typography variant="body2" className="contact-text">
                      +380977777777
                    </Typography>
                  </Box>
                  <Box className="contact-item">
                    <LocationOn className="contact-icon" />
                    <Typography variant="body2" className="contact-text">
                      село Переможне, Львівська область<br />
                      Львів
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
              © {new Date().getFullYear()} DavaiPoihalu. Всі права захищено.
            </Typography>
            <Typography variant="body2" className="footer-credits">
              Розроблено з ❤️ командою DavaiPoihalu
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}

export default Layout
