import { useState, useEffect } from 'react'
import { Box, Paper, Typography, TextField, Button, Stack, Grid, FormControlLabel, Checkbox, Switch, Divider, CircularProgress } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { userAPI } from '../services/api'
import { bookingAPI } from '../services/api'
import { useLanguage } from '../contexts/LanguageContext'

function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [phone, setPhone] = useState(user?.phone || '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const { formatPrice } = useLanguage()

  // Read-only basics
  const firstName = user?.first_name || ''
  const lastName = user?.last_name || ''
  const passportNumber = user?.profile?.passport_number || ''
  const passportExpiry = user?.profile?.passport_expiry || ''

  // Price alerts local preferences
  const PREFS_KEY = 'price_alert_prefs'
  const [prefs, setPrefs] = useState({
    enableEmail: true,
    enableSms: false,
    consent: false,
    alertEmail: user?.email || '',
    alertPhone: user?.phone || '',
  })

  useEffect(() => {
    try {
      const raw = localStorage.getItem(PREFS_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        setPrefs((p) => ({ ...p, ...parsed }))
      }
    } catch {}
  }, [])

  // Passport autofill preferences (local only)
  const PASSPORT_PREFS_KEY = 'passport_autofill_prefs'
  const [passportPrefs, setPassportPrefs] = useState({
    enabled: false,
    number: passportNumber || '',
    expiry: passportExpiry ? String(passportExpiry) : '',
  })

  useEffect(() => {
    try {
      const raw = localStorage.getItem(PASSPORT_PREFS_KEY)
      if (raw) setPassportPrefs((p) => ({ ...p, ...JSON.parse(raw) }))
    } catch {}
  }, [])

  const save = async () => {
    if (!user) return
    setSaving(true)
    setMessage('')
    try {
      await userAPI.update(user.id, { phone })
      await refreshUser()
      setMessage('Збережено')
    } catch (e) {
      setMessage('Помилка збереження')
    } finally {
      setSaving(false)
    }
  }

  const savePrefs = () => {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(prefs))
      setMessage('Налаштування нагадувань збережено')
    } catch {
      setMessage('Не вдалося зберегти налаштування')
    }
  }

  const savePassportPrefs = () => {
    try {
      localStorage.setItem(PASSPORT_PREFS_KEY, JSON.stringify(passportPrefs))
      setMessage('Налаштування паспорта збережено')
    } catch {
      setMessage('Не вдалося зберегти налаштування паспорта')
    }
  }

  // Flight history (recent bookings)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  useEffect(() => {
    const load = async () => {
      setHistoryLoading(true)
      try {
        const { data } = await bookingAPI.getBookings()
        const arr = Array.isArray(data?.results) ? data.results : (Array.isArray(data) ? data : [])
        setHistory(arr.slice(0, 5))
      } catch {
        setHistory([])
      } finally {
        setHistoryLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Box sx={{ minHeight: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column', gap: 2, p: 2 }}>
      <Paper elevation={3} sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#FFA500' }}>Мій профіль</Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>Персональні дані та налаштування сповіщень.</Typography>
      </Paper>

      <Paper elevation={0} sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Stack spacing={2}>
              <TextField
                label="Email"
                value={user?.email || ''}
                InputProps={{ readOnly: true, sx: { bgcolor: '#1a1a1a', color: '#fff' } }}
                InputLabelProps={{ sx: { color: '#bbb' } }}
              />
              <TextField
                label="Імʼя"
                value={firstName}
                InputProps={{ readOnly: true, sx: { bgcolor: '#1a1a1a', color: '#fff' } }}
                InputLabelProps={{ sx: { color: '#bbb' } }}
              />
              <TextField
                label="Прізвище"
                value={lastName}
                InputProps={{ readOnly: true, sx: { bgcolor: '#1a1a1a', color: '#fff' } }}
                InputLabelProps={{ sx: { color: '#bbb' } }}
              />
              <TextField
                label="Телефон"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+380501234567"
                InputLabelProps={{ sx: { color: '#bbb' } }}
                InputProps={{ sx: { bgcolor: '#1a1a1a', color: '#fff', '& fieldset': { borderColor: '#2a2a2a' } } }}
              />
              <Button variant="contained" color="warning" onClick={save} disabled={saving} sx={{ alignSelf: 'flex-start' }}>
                Зберегти телефон
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={0} sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>
          Нагадування про зміну ціни на улюблені рейси
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.75)', mb: 2 }}>
          Погоджуючись, ви даєте згоду на обробку персональних даних для надсилання email/SMS сповіщень.
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Stack spacing={2}>
              <FormControlLabel
                control={<Switch checked={prefs.enableEmail} onChange={(e) => setPrefs({ ...prefs, enableEmail: e.target.checked })} color="warning" />}
                label={<Typography sx={{ color: '#fff' }}>Email-сповіщення</Typography>}
              />
              <TextField
                label="Email для сповіщень"
                value={prefs.alertEmail}
                onChange={(e) => setPrefs({ ...prefs, alertEmail: e.target.value })}
                InputLabelProps={{ sx: { color: '#bbb' } }}
                InputProps={{ sx: { bgcolor: '#1a1a1a', color: '#fff', '& fieldset': { borderColor: '#2a2a2a' } } }}
              />
            </Stack>
          </Grid>
          <Grid item xs={12} md={6}>
            <Stack spacing={2}>
              <FormControlLabel
                control={<Switch checked={prefs.enableSms} onChange={(e) => setPrefs({ ...prefs, enableSms: e.target.checked })} color="warning" />}
                label={<Typography sx={{ color: '#fff' }}>SMS-сповіщення</Typography>}
              />
              <TextField
                label="Телефон для сповіщень"
                value={prefs.alertPhone}
                onChange={(e) => setPrefs({ ...prefs, alertPhone: e.target.value })}
                placeholder="+3809XXXXXXXX"
                InputLabelProps={{ sx: { color: '#bbb' } }}
                InputProps={{ sx: { bgcolor: '#1a1a1a', color: '#fff', '& fieldset': { borderColor: '#2a2a2a' } } }}
              />
            </Stack>
          </Grid>
        </Grid>
        <Divider sx={{ my: 2, borderColor: '#2a2a2a' }} />
        <FormControlLabel
          control={<Checkbox checked={prefs.consent} onChange={(e) => setPrefs({ ...prefs, consent: e.target.checked })} sx={{ color: '#ff9800' }} />}
          label={<Typography sx={{ color: 'rgba(255,255,255,0.85)' }}>Погоджуюся на обробку персональних даних</Typography>}
        />
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" color="warning" onClick={savePrefs} disabled={!prefs.consent}>
            Зберегти налаштування
          </Button>
        </Box>
      </Paper>

      <Paper elevation={0} sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>
          Автозаповнення даних паспорта
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <FormControlLabel
              control={<Switch checked={passportPrefs.enabled} onChange={(e) => setPassportPrefs({ ...passportPrefs, enabled: e.target.checked })} color="warning" />}
              label={<Typography sx={{ color: '#fff' }}>Увімкнути автозаповнення</Typography>}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              label="Номер паспорта (автозаповнення)"
              value={passportPrefs.number}
              onChange={(e) => setPassportPrefs({ ...passportPrefs, number: e.target.value })}
              disabled={!passportPrefs.enabled}
              InputLabelProps={{ sx: { color: '#bbb' } }}
              InputProps={{ sx: { bgcolor: '#1a1a1a', color: '#fff', '& fieldset': { borderColor: '#2a2a2a' } } }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              label="Термін дії паспорта (автозаповнення)"
              type="date"
              value={passportPrefs.expiry}
              onChange={(e) => setPassportPrefs({ ...passportPrefs, expiry: e.target.value })}
              disabled={!passportPrefs.enabled}
              InputLabelProps={{ shrink: true, sx: { color: '#bbb' } }}
              InputProps={{ sx: { bgcolor: '#1a1a1a', color: '#fff', '& fieldset': { borderColor: '#2a2a2a' } } }}
            />
          </Grid>
        </Grid>
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" color="warning" onClick={savePassportPrefs}>
            Зберегти автозаповнення
          </Button>
        </Box>
      </Paper>

      <Paper elevation={0} sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ color: '#FFA500', fontWeight: 700, mb: 1 }}>
          Історія моїх рейсів
        </Typography>
        {historyLoading ? (
          <Box sx={{ display:'flex', alignItems:'center', gap:1 }}>
            <CircularProgress size={20} />
            <Typography sx={{ color:'#aaa' }}>Завантаження…</Typography>
          </Box>
        ) : history.length === 0 ? (
          <Typography sx={{ color:'rgba(255,255,255,0.75)' }}>Поки що немає записів.</Typography>
        ) : (
          <Stack spacing={1}>
            {history.map((h) => (
              <Box key={h.id} sx={{ display:'flex', justifyContent:'space-between', alignItems:'center', p:1.5, bgcolor:'#121212', border:'1px solid #2a2a2a', borderRadius:1 }}>
                <Typography sx={{ color:'#fff' }}>#{h.id}</Typography>
                <Typography sx={{ color:'#ffb74d' }}>{
                  h.status === 'confirmed' ? 'підтверджено' : h.status === 'cancelled' ? 'скасовано' : 'опрацьовується'
                }</Typography>
                <Typography sx={{ color:'#fff' }}>{formatPrice(h.total_price ?? h.total_amount ?? 0, 'USD')}</Typography>
                <Typography sx={{ color:'rgba(255,255,255,0.75)' }}>{h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}</Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Paper>

      {message && <Typography variant="body2" sx={{ color: '#FFA500' }}>{message}</Typography>}
    </Box>
  )
}

export default ProfilePage
