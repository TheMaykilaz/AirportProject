import { useEffect, useState } from 'react'
import { Box, Paper, Typography, Grid } from '@mui/material'
import { bookingAPI } from '../services/api'
import { useLanguage } from '../contexts/LanguageContext'

function MyFlightsPage() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { formatPrice } = useLanguage()

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const { data } = await bookingAPI.getBookings()
        setOrders(Array.isArray(data) ? data : [])
      } catch (e) {
        setError('Не вдалося завантажити ваші рейси')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Box sx={{ minHeight: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column', gap: 2, p: 2 }}>
      <Paper elevation={3} sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#FFA500' }}>Мої рейси</Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>Список ваших бронювань.</Typography>
      </Paper>

      {loading ? (
        <Paper sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ddd' }}>Завантаження…</Paper>
      ) : error ? (
        <Paper sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', color: 'salmon' }}>{error}</Paper>
      ) : (
        <Grid container spacing={2}>
          {orders.length === 0 ? (
            <Grid item xs={12}>
              <Paper sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ddd' }}>Немає бронювань.</Paper>
            </Grid>
          ) : (
            orders.map((o) => (
              <Grid key={o.id} item xs={12} md={6} lg={4}>
                <Paper sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
                  <Typography variant="subtitle1" sx={{ color: '#FFA500', fontWeight: 700 }}>Бронювання #{o.id}</Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5 }}>Рейс: {o.flight}</Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5 }}>Статус: {o.status}</Typography>
                  <Typography variant="body2">Сума: {formatPrice(o.total_price, 'USD')}</Typography>
                </Paper>
              </Grid>
            ))
          )}
        </Grid>
      )}
    </Box>
  )
}

export default MyFlightsPage
