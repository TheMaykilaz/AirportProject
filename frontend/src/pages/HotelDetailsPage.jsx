import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Box, Paper, Typography, Grid, Chip, Stack, ImageList, ImageListItem, Divider, TextField, Button, Dialog, IconButton } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import { hotelsAPI, stripeHotelAPI } from '../services/api'
import { useLanguage } from '../contexts/LanguageContext'

function HotelDetailsPage() {
  const { id } = useParams()
  const { formatPrice } = useLanguage()
  const [hotel, setHotel] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [question, setQuestion] = useState('')
  const [sending, setSending] = useState(false)
  const [sentMsg, setSentMsg] = useState('')

  // Lightbox for images
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const { data } = await hotelsAPI.get(id)
        setHotel(data)
      } catch (e) {
        setError('Не вдалося завантажити готель')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // mock reviews if backend doesn't provide
  const reviews = [
    { id: 1, user: 'Олена', rating: 9.2, text: 'Чисто, зручно, близько до аеропорту.' },
    { id: 2, user: 'Ігор', rating: 8.7, text: 'Гарний сервіс і сніданки. Рекомендую.' },
    { id: 3, user: 'Марія', rating: 9.0, text: 'Зручне розташування, тиха кімната.' },
  ]

  const mapSrc = hotel ? `https://www.google.com/maps?q=${encodeURIComponent((hotel.address || '') + ', ' + (hotel.city || '') + ', ' + (hotel.country || ''))}&output=embed` : ''

  // Build images with sensible defaults if none provided by backend
  const defaultImages = (typeof window !== 'undefined' && window.DEFAULT_HOTEL_IMAGES) || [
    '/images/hotel-default-1.jpg',
    '/images/hotel-default-2.jpg',
    '/images/hotel-default-3.jpg',
    '/images/hotel-default-4.jpg',
  ]
  const remoteFallbacks = [
    'https://images.unsplash.com/photo-1501117716987-c8e2a1a936ca?q=80&w=1200&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1200&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1551776235-dde6d4829808?q=80&w=1200&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1551776235-0bdf8853f4bd?q=80&w=1200&auto=format&fit=crop',
  ]
  const images = (Array.isArray(hotel?.images) && hotel.images.length > 0)
    ? hotel.images
    : (defaultImages || remoteFallbacks)

  // Booking widget state
  const [nights, setNights] = useState(1)
  const [board, setBoard] = useState('bb') // bb, hb, ai
  const boardLabels = { bb: 'Лише сніданок', hb: 'Напівпансіон', ai: 'Все включено' }
  const boardMultiplier = { bb: 1.0, hb: 1.3, ai: 1.8 }
  const basePrice = (() => {
    try {
      // prefer backend min_price_per_night if present
      return parseFloat(hotel?.min_price_per_night || 100)
    } catch { return 100 }
  })()
  const totalPrice = Math.max(1, nights) * basePrice * (boardMultiplier[board] || 1)

  return (
    <Box sx={{ minHeight: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column', gap: 2, p: 2 }}>
      <Paper elevation={3} sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#FFA500' }}>Деталі готелю</Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>Фото, відгуки, карта та інформація.</Typography>
      </Paper>

      {loading ? (
        <Paper sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ddd' }}>Завантаження…</Paper>
      ) : error ? (
        <Paper sx={{ p: 3, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', color: 'salmon' }}>{error}</Paper>
      ) : hotel ? (
        <>
          <Paper sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
            <Typography variant="h4" sx={{ color: '#fff', fontWeight: 800 }}>{hotel.name}</Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>{hotel.city}, {hotel.country}</Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap', gap: 1 }}>
              <Chip label={`⭐ ${hotel.star_rating}`} color="warning" variant="outlined" sx={{ color: '#FFA500', borderColor: '#FFA500' }} />
              {hotel.nearest_airport_code && (
                <Chip label={`Аеропорт: ${hotel.nearest_airport_code}`} variant="outlined" sx={{ color: '#ffb74d', borderColor: '#ffb74d' }} />
              )}
              {hotel.distance_from_airport_km && (
                <Chip label={`${hotel.distance_from_airport_km} км`} variant="outlined" sx={{ color: '#ffb74d', borderColor: '#ffb74d' }} />
              )}
            </Stack>
          </Paper>

          {images.length > 0 && (
            <Paper sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
              <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>Фотографії</Typography>
              <ImageList cols={3} gap={8}>
                {images.map((src, idx) => (
                  <ImageListItem key={idx} onClick={() => { setLightboxIndex(idx); setLightboxOpen(true) }} style={{ cursor:'pointer' }}>
                    <img src={src} alt={`Фото ${idx+1}`} loading="lazy" style={{ borderRadius: 8 }} />
                  </ImageListItem>
                ))}
              </ImageList>
            </Paper>
          )}

          <Grid container spacing={2}>
            <Grid item xs={12} md={7}>
              <Paper sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
                <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>Опис</Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>{hotel.description || 'Опис відсутній.'}</Typography>
                {hotel.amenities?.length > 0 && (
                  <>
                    <Divider sx={{ my: 2, borderColor: '#2a2a2a' }} />
                    <Typography variant="subtitle1" sx={{ color: '#ffb74d', fontWeight: 700, mb: 1 }}>Зручності</Typography>
                    <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                      {hotel.amenities.map((a, i) => (
                        <Chip key={i} label={a} color="warning" variant="outlined" sx={{ color: '#FFA500', borderColor: '#FFA500' }} />
                      ))}
                    </Stack>
                  </>
                )}
              </Paper>

              <Paper sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2, mt: 2 }}>
                <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>Відгуки</Typography>
                <Stack spacing={1.5}>
                  {reviews.map(r => (
                    <Box key={r.id} sx={{ bgcolor:'#121212', border:'1px solid #2a2a2a', borderRadius:1, p:1.5 }}>
                      <Typography sx={{ color:'#fff', fontWeight:700 }}>{r.user}</Typography>
                      <Typography sx={{ color:'#ffb74d' }}>Оцінка: {r.rating}</Typography>
                      <Typography sx={{ color:'rgba(255,255,255,0.9)' }}>{r.text}</Typography>
                    </Box>
                  ))}
                </Stack>
              </Paper>

              <Paper sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2, mt: 2 }}>
                <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>Задати питання</Typography>
                <TextField
                  multiline
                  minRows={3}
                  fullWidth
                  placeholder="Ваше запитання про готель..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  InputLabelProps={{ sx: { color: '#bbb' } }}
                  InputProps={{ sx: { bgcolor: '#1a1a1a', color: '#fff', '& fieldset': { borderColor: '#2a2a2a' } } }}
                />
                <Box sx={{ mt: 1, display:'flex', gap:1, alignItems:'center' }}>
                  <Button
                    variant="contained"
                    color="warning"
                    disabled={!question.trim() || sending}
                    onClick={() => {
                      setSending(true)
                      try {
                        const key = 'hotel_questions'
                        const raw = localStorage.getItem(key)
                        const obj = raw ? JSON.parse(raw) : {}
                        const arr = Array.isArray(obj[id]) ? obj[id] : []
                        arr.push({ q: question.trim(), at: new Date().toISOString() })
                        obj[id] = arr
                        localStorage.setItem(key, JSON.stringify(obj))
                        setSentMsg('Питання надіслано! Ми відповімо на email, якщо це буде потрібно.')
                        setQuestion('')
                      } catch {
                        setSentMsg('Не вдалося зберегти питання локально.')
                      }
                      setSending(false)
                    }}
                  >
                    Надіслати питання
                  </Button>
                  {sentMsg && <Typography variant="body2" sx={{ color:'#ffb74d' }}>{sentMsg}</Typography>}
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={5}>
              <Paper sx={{ p: 0, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2, overflow:'hidden' }}>
                <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, p:2 }}>Карта</Typography>
                {mapSrc ? (
                  <iframe title="hotel-map" src={mapSrc} width="100%" height="320" style={{ border:0 }} loading="lazy" allowFullScreen></iframe>
                ) : (
                  <Box sx={{ p:2, color:'#ddd' }}>Немає адреси для відображення на карті.</Box>
                )}
              </Paper>

              {hotel.min_price_per_night && (
                <Paper sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2, mt:2 }}>
                  <Typography variant="subtitle1" sx={{ color:'#fff', mb:1 }}>Від {formatPrice(hotel.min_price_per_night, 'USD')} / ніч</Typography>
                  <Stack spacing={1}>
                    <TextField
                      label="Кількість ночей"
                      type="number"
                      value={nights}
                      onChange={(e) => setNights(Math.max(1, Math.min(30, parseInt(e.target.value) || 1)))}
                      InputProps={{ sx: { bgcolor:'#1a1a1a', color:'#fff' } }}
                      InputLabelProps={{ sx: { color:'#bbb' } }}
                    />
                    <TextField
                      select
                      label="Тип послуги"
                      value={board}
                      onChange={(e) => setBoard(e.target.value)}
                      SelectProps={{ native: true }}
                      sx={{ '& fieldset': { borderColor:'#2a2a2a' } }}
                    >
                      <option value="bb">{boardLabels.bb}</option>
                      <option value="hb">{boardLabels.hb}</option>
                      <option value="ai">{boardLabels.ai}</option>
                    </TextField>
                    <Typography variant="h6" sx={{ color:'#FFA500', fontWeight:800 }}>
                      Разом: {formatPrice(totalPrice, 'USD')}
                    </Typography>
                    <Button
                      variant="contained"
                      color="warning"
                      onClick={async () => {
                        try {
                          const { data } = await stripeHotelAPI.checkout({ hotel_id: hotel.id, nights, board })
                          window.location.href = data.checkout_url
                        } catch (e) {
                          alert('Не вдалося створити оплату')
                        }
                      }}
                    >Оплатити через Stripe</Button>
                  </Stack>
                </Paper>
              )}
            </Grid>
          </Grid>
        </>
      ) : null}

      {/* Lightbox */}
      <Dialog open={lightboxOpen} onClose={() => setLightboxOpen(false)} fullWidth maxWidth="md" PaperProps={{ sx: { bgcolor: '#000' } }}>
        <Box sx={{ position:'relative' }}>
          <IconButton onClick={() => setLightboxOpen(false)} sx={{ position:'absolute', top:8, right:8, color:'#fff', zIndex:2 }}>
            <CloseIcon />
          </IconButton>
          {images.length > 0 && (
            <>
              <IconButton onClick={() => setLightboxIndex((lightboxIndex - 1 + images.length) % images.length)} sx={{ position:'absolute', top:'50%', left:8, transform:'translateY(-50%)', color:'#fff', zIndex:2 }}>
                <ChevronLeftIcon />
              </IconButton>
              <img src={images[lightboxIndex]} alt="Фото" style={{ width:'100%', height:'auto', display:'block' }} />
              <IconButton onClick={() => setLightboxIndex((lightboxIndex + 1) % images.length)} sx={{ position:'absolute', top:'50%', right:8, transform:'translateY(-50%)', color:'#fff', zIndex:2 }}>
                <ChevronRightIcon />
              </IconButton>
            </>
          )}
        </Box>
      </Dialog>
    </Box>
  )
}

export default HotelDetailsPage
