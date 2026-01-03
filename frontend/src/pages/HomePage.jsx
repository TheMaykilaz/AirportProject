import { Box, Typography, Button, Container, Grid, Card, CardContent } from '@mui/material'
import { FlightTakeoff, Search, Security, Speed } from '@mui/icons-material'
import { Link } from 'react-router-dom'

const HomePage = () => {
  return (
    <Container maxWidth="lg">
      <Box
        sx={{
          textAlign: 'center',
          py: 8,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: 4,
          color: 'white',
          mb: 6,
        }}
      >
        <FlightTakeoff sx={{ fontSize: 80, mb: 2 }} />
        <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
          Find Your Perfect Flight
        </Typography>
        <Typography variant="h5" sx={{ mb: 4, opacity: 0.9 }}>
          Compare prices from multiple airlines and book the best deals
        </Typography>
        <Button
          component={Link}
          to="/search"
          variant="contained"
          size="large"
          sx={{
            bgcolor: 'white',
            color: '#667eea',
            px: 4,
            py: 1.5,
            fontSize: '1.2rem',
            '&:hover': {
              bgcolor: 'rgba(255,255,255,0.9)',
            },
          }}
        >
          Search Flights
        </Button>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', textAlign: 'center' }}>
            <CardContent>
              <Search sx={{ fontSize: 60, color: '#667eea', mb: 2 }} />
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Easy Search
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Search flights by airport code or city name. Compare prices across multiple airlines instantly.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', textAlign: 'center' }}>
            <CardContent>
              <Security sx={{ fontSize: 60, color: '#667eea', mb: 2 }} />
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Secure Booking
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Safe and secure payment processing with Stripe. Your data is protected.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', textAlign: 'center' }}>
            <CardContent>
              <Speed sx={{ fontSize: 60, color: '#667eea', mb: 2 }} />
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Fast & Reliable
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Quick booking process with real-time seat availability and instant confirmations.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  )
}

export default HomePage

