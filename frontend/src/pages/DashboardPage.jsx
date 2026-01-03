import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { bookingAPI } from '../services/api'
import { format } from 'date-fns'

const DashboardPage = () => {
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadBookings()
  }, [])

  const loadBookings = async () => {
    try {
      const response = await bookingAPI.getBookings()
      setBookings(response.data.results || response.data || [])
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load bookings')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ mb: 4 }}>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Welcome, {user?.first_name || user?.email}!
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user?.email}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Bookings
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {bookings.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Status
              </Typography>
              <Chip label="Active" color="success" />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ mb: 2 }}>
        My Bookings
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {bookings.length === 0 ? (
        <Alert severity="info">You don't have any bookings yet.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Order ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Total Amount</TableCell>
                <TableCell>Created At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bookings.map((booking) => (
                <TableRow key={booking.id}>
                  <TableCell>#{booking.id}</TableCell>
                  <TableCell>
                    <Chip
                      label={booking.status || 'Pending'}
                      color={
                        booking.status === 'confirmed'
                          ? 'success'
                          : booking.status === 'cancelled'
                          ? 'error'
                          : 'warning'
                      }
                    />
                  </TableCell>
                  <TableCell>${parseFloat(booking.total_amount || 0).toFixed(2)}</TableCell>
                  <TableCell>
                    {booking.created_at
                      ? format(new Date(booking.created_at), 'MMM dd, yyyy')
                      : 'N/A'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  )
}

export default DashboardPage

