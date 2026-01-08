import { useEffect, useState } from 'react'
import { Box, Typography, Paper, Grid, TextField, Button, MenuItem, CircularProgress, Card, CardContent, Chip, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { hotelsAPI } from '../services/api'
import { useLanguage } from '../contexts/LanguageContext'

function HotelsPage() {
  const navigate = useNavigate()
  const { formatPrice } = useLanguage()
  const [filters, setFilters] = useState({
    city: '',
    airport_code: '',
    max_distance_km: '',
    min_star_rating: '',
  })
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')

  const onChange = (field) => (e) => {
    setFilters((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const fetchHotels = async () => {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (filters.city) params.city = filters.city
      if (filters.airport_code) params.airport_code = filters.airport_code
      if (filters.max_distance_km) params.max_distance_km = filters.max_distance_km
      if (filters.min_star_rating) params.min_star_rating = filters.min_star_rating

      const { data } = await hotelsAPI.list(params)
      setResults(data)
    } catch (e) {
      setError('Не вдалося завантажити готелі. Спробуйте пізніше.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // первинне завантаження всіх активних готелів
    fetchHotels()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Box sx={{
      minHeight: 'calc(100vh - 160px)',
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
    }}>
      <Paper elevation={3} sx={{
        p: 3,
        bgcolor: '#121212',
        color: '#fff',
        borderRadius: 2,
        border: '1px solid #2a2a2a',
      }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#FFA500' }}>
          Пошук готелів
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>
          Оберіть напрямок і дати — ми підберемо найкращі варіанти.
        </Typography>
      </Paper>

      <Paper elevation={0} sx={{
        p: 2,
        bgcolor: '#0d0d0d',
        border: '1px solid #2a2a2a',
        borderRadius: 2,
      }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Місто або локація"
              variant="outlined"
              value={filters.city}
              onChange={onChange('city')}
              InputLabelProps={{ sx: { color: '#bbb' } }}
              InputProps={{
                sx: {
                  bgcolor: '#1a1a1a',
                  color: '#fff',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2a2a2a' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#FFA500' },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#FFA500' },
                },
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              label="Код аеропорту (IATA)"
              placeholder="JFK, LHR..."
              value={filters.airport_code}
              onChange={onChange('airport_code')}
              InputLabelProps={{ sx: { color: '#bbb' } }}
              InputProps={{
                sx: {
                  bgcolor: '#1a1a1a',
                  color: '#fff',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2a2a2a' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#FFA500' },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#FFA500' },
                },
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              label="Макс. відстань (км)"
              type="number"
              value={filters.max_distance_km}
              onChange={onChange('max_distance_km')}
              InputLabelProps={{ sx: { color: '#bbb' } }}
              InputProps={{
                sx: {
                  bgcolor: '#1a1a1a',
                  color: '#fff',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2a2a2a' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#FFA500' },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#FFA500' },
                },
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              select
              fullWidth
              label="Мін. рейтинг"
              value={filters.min_star_rating}
              onChange={onChange('min_star_rating')}
              InputLabelProps={{ sx: { color: '#bbb' } }}
              sx={{
                '& fieldset': { borderColor: '#2a2a2a' },
                '&:hover fieldset': { borderColor: '#FFA500' },
                '& .MuiSelect-select': { bgcolor: '#1a1a1a', color: '#fff' },
              }}
            >
              <MenuItem value="">Будь-який</MenuItem>
              {[1,2,3,4,5].map(v => (
                <MenuItem key={v} value={v}>{v}+</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} md={2} sx={{ display: 'flex', alignItems: 'stretch' }}>
            <Button fullWidth variant="contained" color="warning" sx={{ fontWeight: 700 }} onClick={fetchHotels}>
              Пошук
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={0} sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
            <CircularProgress color="warning" />
          </Box>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : (
          <Grid container spacing={2}>
            {results.length === 0 ? (
              <Grid item xs={12}>
                <Typography sx={{ color: '#ddd' }}>Нічого не знайдено. Спробуйте змінити фільтри.</Typography>
              </Grid>
            ) : (
              results.map((h) => (
                <Grid key={h.id} item xs={12} md={6} lg={4}>
                  <Card onClick={() => navigate(`/hotels/${h.id}`)} sx={{ bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', cursor: 'pointer', '&:hover': { borderColor: '#FFA500' } }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700 }}>
                        {h.name}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                        {h.city}, {h.country}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        ⭐ {h.star_rating} • {h.distance_from_airport_km} км від {h.nearest_airport_code}
                      </Typography>
                      {h.min_price_per_night && (
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                          Від {formatPrice(h.min_price_per_night, 'USD')} / ніч
                        </Typography>
                      )}
                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                        {(h.amenities || []).slice(0, 4).map((a, i) => (
                          <Chip key={i} size="small" label={a} color="warning" variant="outlined" sx={{ color: '#FFA500', borderColor: '#FFA500' }} />
                        ))}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        )}
      </Paper>
    </Box>
  )
}

export default HotelsPage
