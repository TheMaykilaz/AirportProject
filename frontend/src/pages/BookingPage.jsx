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
  TextField,
  Paper,
} from '@mui/material'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { flightAPI, bookingAPI, paymentAPI } from '../services/api'

const BookingPage = () => {
  const { flightId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [flight, setFlight] = useState(null)
  const [seatMap, setSeatMap] = useState(null)
  const [selectedSeats, setSelectedSeats] = useState([])
  const [loading, setLoading] = useState(true)
  const [booking, setBooking] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/booking/' + flightId)
      return
    }
    loadFlightData()
  }, [flightId, user])

  const loadFlightData = async () => {
    try {
      const [flightResponse, seatMapResponse] = await Promise.all([
        flightAPI.getFlight(flightId),
        flightAPI.getSeatMap(flightId),
      ])
      setFlight(flightResponse.data)
      setSeatMap(seatMapResponse.data)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load flight data')
    } finally {
      setLoading(false)
    }
  }

  const handleSeatSelect = (seatNumber) => {
    setSelectedSeats((prev) => {
      if (prev.includes(seatNumber)) {
        return prev.filter((s) => s !== seatNumber)
      }
      return [...prev, seatNumber]
    })
  }

  const handleBooking = async () => {
    if (selectedSeats.length === 0) {
      setError('Please select at least one seat')
      return
    }

    setBooking(true)
    setError(null)

    try {
      const bookingResponse = await bookingAPI.createBooking({
        flight_id: parseInt(flightId),
        seat_numbers: selectedSeats,
      })

      const paymentResponse = await paymentAPI.createCheckoutSession(
        bookingResponse.data.order_id
      )

      if (paymentResponse.data.checkout_url) {
        window.location.href = paymentResponse.data.checkout_url
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Booking failed')
      setBooking(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error && !flight) {
    return <Alert severity="error">{error}</Alert>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ mb: 4 }}>
        Complete Your Booking
      </Typography>

      {flight && (
        <Grid container spacing={4}>
          <Grid item xs={12} md={8}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Flight Details
                </Typography>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Airline
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {flight.airline_name || 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Flight Number
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {flight.flight_number}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Departure
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {flight.departure_airport_code} - {flight.departure_city}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Arrival
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {flight.arrival_airport_code} - {flight.arrival_city}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {seatMap && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom fontWeight="bold">
                    Select Seats
                  </Typography>
                  {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      {error}
                    </Alert>
                  )}
                  <Box sx={{ mt: 2 }}>
                    <Grid container spacing={1}>
                      {seatMap.seat_map?.map((seat) => (
                        <Grid item key={seat.seat_number}>
                          <Button
                            variant={
                              selectedSeats.includes(seat.seat_number)
                                ? 'contained'
                                : seat.status === 'available'
                                ? 'outlined'
                                : 'disabled'
                            }
                            onClick={() =>
                              seat.status === 'available' &&
                              handleSeatSelect(seat.seat_number)
                            }
                            disabled={seat.status !== 'available'}
                            sx={{
                              minWidth: 60,
                              bgcolor:
                                selectedSeats.includes(seat.seat_number)
                                  ? 'primary.main'
                                  : seat.status === 'available'
                                  ? 'transparent'
                                  : 'grey.300',
                            }}
                          >
                            {seat.seat_number}
                          </Button>
                        </Grid>
                      ))}
                    </Grid>
                    <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box
                          sx={{
                            width: 20,
                            height: 20,
                            border: '1px solid',
                            borderColor: 'primary.main',
                            mr: 1,
                          }}
                        />
                        <Typography variant="body2">Available</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box
                          sx={{
                            width: 20,
                            height: 20,
                            bgcolor: 'grey.300',
                            mr: 1,
                          }}
                        />
                        <Typography variant="body2">Occupied</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box
                          sx={{
                            width: 20,
                            height: 20,
                            bgcolor: 'primary.main',
                            mr: 1,
                          }}
                        />
                        <Typography variant="body2">Selected</Typography>
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            )}
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, position: 'sticky', top: 20 }}>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Booking Summary
              </Typography>
              <Box sx={{ my: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Seats Selected:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {selectedSeats.length}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Price per seat:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    ${parseFloat(flight.base_price || 0).toFixed(2)}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    mt: 2,
                    pt: 2,
                    borderTop: '2px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h6" fontWeight="bold">
                    Total:
                  </Typography>
                  <Typography variant="h6" fontWeight="bold" color="primary">
                    ${(parseFloat(flight.base_price || 0) * selectedSeats.length).toFixed(2)}
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleBooking}
                disabled={booking || selectedSeats.length === 0}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  mt: 2,
                }}
              >
                {booking ? <CircularProgress size={24} /> : 'Proceed to Payment'}
              </Button>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}

export default BookingPage

