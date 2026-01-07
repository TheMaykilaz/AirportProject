import { useEffect, useRef, useState } from 'react'
import { Box, Typography, TextField, IconButton, Paper, Stack } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import { aiChatAPI } from '../services/api'

function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Привіт! Я ваш AI-асистент. Чим допомогти?" },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return

    const nextHistory = [...messages, { role: 'user', content: text }]
    setMessages(nextHistory)
    setInput('')
    setLoading(true)

    try {
      const payloadHistory = nextHistory
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))

      const { data } = await aiChatAPI.send(text, payloadHistory)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (e) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Вибачте, сталася помилка. Спробуйте пізніше.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{
      height: 'calc(100vh - 160px)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <Paper elevation={3} sx={{
        p: 2,
        bgcolor: '#121212',
        color: '#fff',
        borderRadius: 2,
        border: '1px solid #2a2a2a',
      }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color: '#FFA500' }}>
          AI Chat
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>
          Запитайте мене про пошук рейсів, готелів або іншу інформацію.
        </Typography>
      </Paper>

      <Paper elevation={0} sx={{
        flex: 1,
        mt: 2,
        p: 2,
        bgcolor: '#0d0d0d',
        border: '1px solid #2a2a2a',
        borderRadius: 2,
        overflow: 'auto',
      }}>
        <Stack spacing={2}>
          {messages.map((m, idx) => (
            <Box key={idx} sx={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              <Box sx={{
                maxWidth: '75%',
                p: 1.5,
                borderRadius: 2,
                bgcolor: m.role === 'user' ? '#FF8C00' : '#1a1a1a',
                color: m.role === 'user' ? '#000' : '#fff',
                border: m.role === 'user' ? 'none' : '1px solid #2a2a2a',
                whiteSpace: 'pre-wrap',
              }}>
                <Typography variant="body1">{m.content}</Typography>
              </Box>
            </Box>
          ))}
          <div ref={bottomRef} />
        </Stack>
      </Paper>

      <Paper elevation={3} sx={{
        mt: 2,
        p: 1,
        bgcolor: '#121212',
        border: '1px solid #2a2a2a',
        borderRadius: 2,
        display: 'flex',
        gap: 1,
        alignItems: 'center',
      }}>
        <TextField
          fullWidth
          placeholder="Введіть повідомлення..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
          variant="outlined"
          size="medium"
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
        <IconButton color="warning" onClick={handleSend} disabled={loading}>
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  )
}

export default ChatPage
