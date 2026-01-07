import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Paper, Typography, Grid, Button, IconButton } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { useLanguage } from '../contexts/LanguageContext'

const FAVORITES_KEY = 'favorite_flights'

const readFavorites = () => {
  try { return JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]') } catch { return [] }
}
const writeFavorites = (items) => {
  try { localStorage.setItem(FAVORITES_KEY, JSON.stringify(items)) } catch {}
}

function FavoritesPage() {
  const [items, setItems] = useState(() => readFavorites())
  const { formatPrice } = useLanguage()
  const navigate = useNavigate()

  const remove = (id) => {
    const next = items.filter(i => i.flight_id !== id)
    setItems(next)
    writeFavorites(next)
  }

  const empty = useMemo(() => items.length === 0, [items])

  return (
    <Box sx={{
      minHeight: 'calc(100vh - 160px)',
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      p: 2,
    }}>
      <Paper elevation={3} sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#FFA500' }}>Мої улюблені рейси</Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>Збережені вами рейси з результатів пошуку.</Typography>
      </Paper>

      <Grid container spacing={2} sx={{ mt: 1 }}>
        {empty ? (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ddd' }}>
              Поки що немає улюблених рейсів.
            </Paper>
          </Grid>
        ) : items.map(item => (
          <Grid key={item.flight_id} item xs={12} md={6} lg={4}>
            <Paper sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1" sx={{ color: '#FFA500', fontWeight: 700 }}>
                  {item.departure_city} — {item.arrival_city}
                </Typography>
                <IconButton size="small" onClick={() => remove(item.flight_id)} title="Прибрати">
                  <DeleteIcon htmlColor="#ff9800" />
                </IconButton>
              </Box>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {item.airline_name} • {item.departure_airport_code} → {item.arrival_airport_code}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Від {formatPrice(item.min_price, 'USD')}
              </Typography>
              <Button variant="contained" color="warning" onClick={() => navigate(`/booking/${item.flight_id}`)}>
                Купити
              </Button>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default FavoritesPage
