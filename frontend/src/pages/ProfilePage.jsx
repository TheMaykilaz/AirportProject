import { useState } from 'react'
import { Box, Paper, Typography, TextField, Button, Stack } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { userAPI } from '../services/api'

function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [phone, setPhone] = useState(user?.phone || '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

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

  return (
    <Box sx={{ minHeight: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column', gap: 2, p: 2 }}>
      <Paper elevation={3} sx={{ p: 2, bgcolor: '#121212', color: '#fff', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#FFA500' }}>Профіль</Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>Оновіть свій номер телефону.</Typography>
      </Paper>

      <Paper elevation={0} sx={{ p: 2, bgcolor: '#0d0d0d', border: '1px solid #2a2a2a', borderRadius: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Email"
            value={user?.email || ''}
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
            Зберегти
          </Button>
          {message && <Typography variant="body2" sx={{ color: '#FFA500' }}>{message}</Typography>}
        </Stack>
      </Paper>
    </Box>
  )
}

export default ProfilePage
