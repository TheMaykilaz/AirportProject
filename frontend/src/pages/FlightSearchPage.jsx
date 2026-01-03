import { useState } from 'react'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Grid,
  FormControlLabel,
  Switch,
  MenuItem,
} from '@mui/material'
import { Search as SearchIcon } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'

const FlightSearchPage = () => {
  const navigate = useNavigate()
  const [isRoundTrip, setIsRoundTrip] = useState(false)
  const [formData, setFormData] = useState({
    departure_airport_code: '',
    arrival_airport_code: '',
    departure_date: '',
    return_date: '',
    passengers: 1,
    sort_by: 'price',
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'passengers' ? parseInt(value) || 1 : value,
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const params = new URLSearchParams()
    
    Object.entries(formData).forEach(([key, value]) => {
      if (value && (key !== 'return_date' || isRoundTrip)) {
        params.append(key, value)
      }
    })

    navigate(`/results?${params.toString()}`)
  }

  const today = format(new Date(), 'yyyy-MM-dd')

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ mb: 4 }}>
        Search Flights
      </Typography>
      <Paper elevation={3} sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <FormControlLabel
            control={
              <Switch
                checked={isRoundTrip}
                onChange={(e) => setIsRoundTrip(e.target.checked)}
              />
            }
            label="Round Trip"
            sx={{ mb: 3 }}
          />

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Departure Airport Code"
                name="departure_airport_code"
                value={formData.departure_airport_code}
                onChange={handleChange}
                placeholder="e.g., JFK"
                inputProps={{ maxLength: 3, style: { textTransform: 'uppercase' } }}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Arrival Airport Code"
                name="arrival_airport_code"
                value={formData.arrival_airport_code}
                onChange={handleChange}
                placeholder="e.g., LHR"
                inputProps={{ maxLength: 3, style: { textTransform: 'uppercase' } }}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Departure Date"
                name="departure_date"
                type="date"
                value={formData.departure_date}
                onChange={handleChange}
                InputLabelProps={{ shrink: true }}
                inputProps={{ min: today }}
                required
              />
            </Grid>
            {isRoundTrip && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Return Date"
                  name="return_date"
                  type="date"
                  value={formData.return_date}
                  onChange={handleChange}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{ min: formData.departure_date || today }}
                  required={isRoundTrip}
                />
              </Grid>
            )}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Passengers"
                name="passengers"
                type="number"
                value={formData.passengers}
                onChange={handleChange}
                inputProps={{ min: 1, max: 9 }}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Sort By"
                name="sort_by"
                value={formData.sort_by}
                onChange={handleChange}
              >
                <MenuItem value="price">Price (Lowest First)</MenuItem>
                <MenuItem value="duration">Duration (Shortest First)</MenuItem>
                <MenuItem value="departure_time">Departure Time</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                startIcon={<SearchIcon />}
                sx={{
                  py: 1.5,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                Search Flights
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  )
}

export default FlightSearchPage

