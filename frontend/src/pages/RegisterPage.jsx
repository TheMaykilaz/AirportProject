import { useState } from 'react'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const RegisterPage = () => {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!formData.first_name.trim() || !formData.last_name.trim()) {
      setError('Будь ласка, введіть імʼя та прізвище')
      return
    }

    if (formData.password !== formData.password_confirm) {
      setError('Паролі не співпадають')
      return
    }

    if (formData.password.length < 8) {
      setError('Пароль має містити щонайменше 8 символів')
      return
    }

    setLoading(true)
    const result = await register(formData)
    setLoading(false)

    if (result.success) {
      navigate('/login')
    } else {
      setError(
        typeof result.error === 'string'
          ? result.error
          : JSON.stringify(result.error)
      )
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '60vh',
      }}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h4" gutterBottom fontWeight="bold" align="center">
          Реєстрація
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Імʼя"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Прізвище"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Імʼя користувача"
            name="username"
            value={formData.username}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="username"
          />
          <TextField
            fullWidth
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="email"
          />
          <TextField
            fullWidth
            label="Пароль"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="new-password"
          />
          <TextField
            fullWidth
            label="Підтвердження паролю"
            name="password_confirm"
            type="password"
            value={formData.password_confirm}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="new-password"
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={loading}
            sx={{
              mt: 3,
              mb: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            {loading ? 'Реєструємо…' : 'Зареєструватись'}
          </Button>
          <Typography variant="body2" align="center">
            Вже маєте акаунт?{' '}
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/login')}
            >
              Увійти
            </Link>
          </Typography>
        </form>
      </Paper>
    </Box>
  )
}

export default RegisterPage

