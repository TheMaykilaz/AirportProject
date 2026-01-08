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
import { useLanguage } from '../contexts/LanguageContext'

const DashboardPage = () => {
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const { formatPrice } = useLanguage()

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
    <Box sx={{
      minHeight: 'calc(100vh - 160px)'
    }}>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ mb: 4, color: '#fff' }}>
        Адмінська панель
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: '#FFA500' }}>
                Вітаємо, {user?.first_name || user?.email}!
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                {user?.email}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: '#FFA500' }}>
                Усього бронювань
              </Typography>
              <Typography variant="h4" fontWeight="bold" sx={{ color: '#FFA500' }}>
                {bookings.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: '#FFA500' }}>
                Статус акаунта
              </Typography>
              <Chip label="Активний" color="success" />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ mb: 2, color: '#fff' }}>
        Мої бронювання
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {bookings.length === 0 ? (
        <Alert severity="info">У вас поки немає бронювань.</Alert>
      ) : (
        <TableContainer component={Paper} sx={{ bgcolor: '#121212', border: '1px solid #2a2a2a' }}>
          <Table sx={{
            '& th': { color: '#ffb74d' },
            '& td': { color: '#fff' }
          }}>
            <TableHead>
              <TableRow>
                <TableCell>Замовлення</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Сума</TableCell>
                <TableCell>Створено</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bookings.map((booking) => (
                <TableRow key={booking.id}>
                  <TableCell>#{booking.id}</TableCell>
                  <TableCell>
                    <Chip
                      label={
                        booking.status === 'confirmed' ? 'підтверджено' :
                        booking.status === 'cancelled' ? 'скасовано' : 'опрацьовується'
                      }
                      color={
                        booking.status === 'confirmed'
                          ? 'success'
                          : booking.status === 'cancelled'
                          ? 'error'
                          : 'warning'
                      }
                    />
                  </TableCell>
                  <TableCell>{formatPrice(booking.total_price ?? booking.total_amount ?? 0, 'USD')}</TableCell>
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

