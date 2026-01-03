import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Paper,
} from '@mui/material'
import { FlightTakeoff, AccessTime, People } from '@mui/icons-material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import { flightAPI } from '../services/api'

const FlightResultsPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [flights, setFlights] = useState([])
  const [returnFlights, setReturnFlights] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [priceStats, setPriceStats] = useState(null)

  useEffect(() => {
    searchFlights()
  }, [searchParams])

  const searchFlights = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = Object.fromEntries(searchParams.entries())
      const response = await flightAPI.search(params)
      setFlights(response.data.results || [])
      setReturnFlights(response.data.return_results || [])
      setPriceStats(response.data.price_stats)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to search flights')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timeString) => {
    try {
      return format(parseISO(timeString), 'HH:mm')
    } catch {
      return timeString
    }
  }

  const formatDuration = (duration) => {
    if (!duration) return 'N/A'
    const parts = duration.split(':')
    if (parts.length >= 2) {
      return `${parts[0]}h ${parts[1]}m`
    }
    return duration
  }

  const FlightCard = ({ flight, isReturn = false }) => (
    <Card sx={{ mb: 3, '&:hover': { boxShadow: 6 } }}>
      <CardContent>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={8}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <FlightTakeoff sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" fontWeight="bold">
                {flight.airline_name}
              </Typography>
              <Chip
                label={flight.airline_code}
                size="small"
                sx={{ ml: 2 }}
              />
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  Departure
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {formatTime(flight.departure_time)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {flight.departure_airport_code} - {flight.departure_city}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  Arrival
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {formatTime(flight.arrival_time)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {flight.arrival_airport_code} - {flight.arrival_city}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <AccessTime sx={{ mr: 0.5, fontSize: 18 }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Duration
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {formatDuration(flight.duration_formatted)}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <People sx={{ mr: 0.5, fontSize: 18 }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Available Seats
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {flight.available_seats}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
              <Typography variant="h4" fontWeight="bold" color="primary">
                ${parseFloat(flight.min_price).toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                per person
              </Typography>
              <Button
                variant="contained"
                fullWidth
                onClick={() => navigate(`/booking/${flight.flight_id}`)}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                Book Now
              </Button>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ mb: 4 }}>
        Flight Results
      </Typography>

      {priceStats && (
        <Paper sx={{ p: 3, mb: 4, bgcolor: 'primary.light', color: 'white' }}>
          <Grid container spacing={4}>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">Cheapest</Typography>
              <Typography variant="h5" fontWeight="bold">
                ${parseFloat(priceStats.min).toFixed(2)}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">Most Expensive</Typography>
              <Typography variant="h5" fontWeight="bold">
                ${parseFloat(priceStats.max).toFixed(2)}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">Average</Typography>
              <Typography variant="h5" fontWeight="bold">
                ${parseFloat(priceStats.average).toFixed(2)}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">Total Flights</Typography>
              <Typography variant="h5" fontWeight="bold">
                {flights.length + returnFlights.length}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {flights.length === 0 && returnFlights.length === 0 ? (
        <Alert severity="info">No flights found. Try adjusting your search criteria.</Alert>
      ) : (
        <>
          {flights.length > 0 && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Outbound Flights
              </Typography>
              {flights.map((flight) => (
                <FlightCard key={flight.flight_id} flight={flight} />
              ))}
            </Box>
          )}

          {returnFlights.length > 0 && (
            <Box>
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Return Flights
              </Typography>
              {returnFlights.map((flight) => (
                <FlightCard key={flight.flight_id} flight={flight} isReturn />
              ))}
            </Box>
          )}
        </>
      )}
    </Box>
  )
}

export default FlightResultsPage

