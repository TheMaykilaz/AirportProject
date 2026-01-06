import { Box, Typography, Button, Container, Grid, Card, CardContent, Paper, Chip } from '@mui/material'
import { 
  FlightTakeoff, 
  Search, 
  Security, 
  Speed, 
  Hotel, 
  Favorite, 
  TrendingUp,
  Support,
  VerifiedUser,
  LocalOffer,
  ArrowForward
} from '@mui/icons-material'
import { Link as RouterLink } from 'react-router-dom'
import './HomePage.css'

const HomePage = () => {
  const features = [
    {
      icon: <Search />,
      title: 'Easy Search',
      description: 'Search flights by airport code or city name. Compare prices across multiple airlines instantly.',
    },
    {
      icon: <Security />,
      title: 'Secure Booking',
      description: 'Safe and secure payment processing with Stripe. Your data is protected with industry-standard encryption.',
    },
    {
      icon: <Speed />,
      title: 'Fast & Reliable',
      description: 'Quick booking process with real-time seat availability and instant confirmations.',
    },
    {
      icon: <Hotel />,
      title: 'Hotel Booking',
      description: 'Book hotels near airports for your convenience. Find the perfect accommodation for your trip.',
    },
    {
      icon: <Favorite />,
      title: 'Save Favorites',
      description: 'Save your favorite flights and hotels for quick access. Never lose track of great deals.',
    },
    {
      icon: <TrendingUp />,
      title: 'Best Prices',
      description: 'Compare prices from multiple airlines and hotels to find the best deals for your budget.',
    }
  ]

  const stats = [
    { number: '500+', label: 'Flights Daily' },
    { number: '13', label: 'Hotels' },
    { number: '50+', label: 'Destinations' },
    { number: '10K+', label: 'Happy Customers' }
  ]

  return (
    <Box className="home-page-modern">
      {/* Hero Section */}
      <Box className="hero-modern">
        <Container maxWidth="lg">
          <Box className="hero-content-modern">
            <Box className="hero-icon-wrapper">
              <FlightTakeoff className="hero-icon-modern" />
            </Box>
            <Typography variant="h1" className="hero-title-modern">
              Find Your Perfect Flight
            </Typography>
            <Typography variant="h5" className="hero-subtitle-modern">
              Compare prices from multiple airlines and book the best deals. 
              Your journey starts here.
            </Typography>
            <Box className="hero-buttons-modern">
              <Button
                component={RouterLink}
                to="/search"
                variant="contained"
                size="large"
                className="hero-button-modern primary"
                endIcon={<ArrowForward />}
              >
                Search Flights
              </Button>
              <Button
                component={RouterLink}
                to="/hotels"
                variant="outlined"
                size="large"
                className="hero-button-modern secondary"
                endIcon={<ArrowForward />}
              >
                Book Hotels
              </Button>
            </Box>
            <Box className="hero-badges-modern">
              <Chip 
                icon={<VerifiedUser />} 
                label="Secure Payments" 
                className="badge-chip-modern"
              />
              <Chip 
                icon={<LocalOffer />} 
                label="Best Prices" 
                className="badge-chip-modern"
              />
              <Chip 
                icon={<Support />} 
                label="24/7 Support" 
                className="badge-chip-modern"
              />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="lg">
        <Box className="stats-section-modern">
          <Grid container spacing={3}>
            {stats.map((stat, index) => (
              <Grid item xs={6} md={3} key={index}>
                <Box className="stat-item-modern">
                  <Typography variant="h2" className="stat-number-modern">
                    {stat.number}
                  </Typography>
                  <Typography variant="body1" className="stat-label-modern">
                    {stat.label}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>

      {/* Features Section */}
      <Container maxWidth="lg" className="features-container-modern">
        <Box className="section-header-modern">
          <Typography variant="h2" className="section-title-modern">
            Why Choose Us?
          </Typography>
          <Typography variant="body1" className="section-subtitle-modern">
            We make travel planning simple, secure, and affordable
          </Typography>
        </Box>
        <Grid container spacing={3} className="features-grid-modern">
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card className="feature-card-modern">
                <CardContent className="feature-content-modern">
                  <Box className="feature-icon-modern">
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" className="feature-title-modern" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" className="feature-description-modern">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box className="cta-section-modern">
        <Container maxWidth="lg">
          <Box className="cta-content-modern">
            <Typography variant="h2" className="cta-title-modern">
              Ready to Start Your Journey?
            </Typography>
            <Typography variant="h6" className="cta-subtitle-modern">
              Search for flights and hotels now. Best prices guaranteed!
            </Typography>
            <Button
              component={RouterLink}
              to="/search"
              variant="contained"
              size="large"
              className="cta-button-modern"
              endIcon={<ArrowForward />}
            >
              Search Now
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}

export default HomePage
