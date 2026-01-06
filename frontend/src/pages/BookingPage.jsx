import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { flightAPI, bookingAPI, paymentAPI } from '../services/api'
import { format, parseISO } from 'date-fns'
import './BookingPage.css'

const BookingPage = () => {
  const { flightId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [flight, setFlight] = useState(null)
  const [seatMap, setSeatMap] = useState(null)
  const [selectedSeats, setSelectedSeats] = useState({}) // { passengerIndex: seatNumber }
  const [loading, setLoading] = useState(true)
  const [booking, setBooking] = useState(false)
  const [error, setError] = useState(null)
  const [passengers, setPassengers] = useState([{ name: user?.email?.split('@')[0] || 'Passenger 1', seat: null }])
  const [currentStep, setCurrentStep] = useState(1)
  const totalSteps = 4

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/booking/' + flightId)
      return
    }
    loadFlightData()
  }, [flightId, user])

  const loadFlightData = async () => {
    try {
      const [flightResponse, seatMapResponse] = await Promise.all([
        flightAPI.getFlight(flightId),
        flightAPI.getSeatMap(flightId),
      ])
      setFlight(flightResponse.data)
      setSeatMap(seatMapResponse.data)
      
      // Initialize passengers based on search params or default to 1
      const urlParams = new URLSearchParams(window.location.search)
      const passengerCount = parseInt(urlParams.get('passengers') || '1')
      const initialPassengers = Array.from({ length: passengerCount }, (_, i) => ({
        name: user?.email?.split('@')[0] || `Passenger ${i + 1}`,
        seat: null
      }))
      setPassengers(initialPassengers)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load flight data')
    } finally {
      setLoading(false)
    }
  }

  // Parse seat map into rows and columns
  const parseSeatMap = () => {
    if (!seatMap?.seat_map) return { rows: [], seatColumns: [] }
    
    const seatColumns = ['A', 'B', 'C', 'H', 'J', 'K'] // 3-3 configuration
    const seatMapByRow = {}
    
    seatMap.seat_map.forEach(seat => {
      const match = seat.seat_number.match(/^(\d+)([A-Z]+)$/)
      if (match) {
        const row = parseInt(match[1])
        const col = match[2]
        
        if (!seatMapByRow[row]) {
          seatMapByRow[row] = {}
        }
        seatMapByRow[row][col] = {
          ...seat,
          row,
          col
        }
      }
    })
    
    const rows = Object.keys(seatMapByRow)
      .map(Number)
      .sort((a, b) => a - b)
      .map(row => ({
        rowNumber: row,
        seats: seatColumns.map(col => seatMapByRow[row]?.[col] || null)
      }))
    
    return { rows, seatColumns }
  }

  const handleSeatSelect = (seatNumber, passengerIndex) => {
    if (!seatNumber) return
    
    const seat = seatMap.seat_map.find(s => s.seat_number === seatNumber)
    if (!seat || seat.status !== 'available') return
    
    setSelectedSeats(prev => {
      const newSeats = { ...prev }
      
      // Remove seat from other passengers if selected
      Object.keys(newSeats).forEach(key => {
        if (newSeats[key] === seatNumber) {
          delete newSeats[key]
        }
      })
      
      // Assign to current passenger
      if (prev[passengerIndex] === seatNumber) {
        // Deselect if clicking same seat
        delete newSeats[passengerIndex]
        setPassengers(prevPass => {
          const updated = [...prevPass]
          updated[passengerIndex].seat = null
          return updated
        })
      } else {
        newSeats[passengerIndex] = seatNumber
        setPassengers(prevPass => {
          const updated = [...prevPass]
          updated[passengerIndex].seat = seatNumber
          return updated
        })
      }
      
      return newSeats
    })
  }

  const handleNext = async () => {
    if (currentStep < totalSteps) {
      if (currentStep === totalSteps - 1) {
        // Last step - proceed to booking
        await handleBooking()
      } else {
        setCurrentStep(prev => prev + 1)
      }
    }
  }

  const handleBooking = async () => {
    const seatNumbers = Object.values(selectedSeats).filter(Boolean)
    
    if (seatNumbers.length === 0) {
      setError('Будь ласка, оберіть місце для кожного пасажира')
      return
    }

    setBooking(true)
    setError(null)

    try {
      const bookingResponse = await bookingAPI.createBooking({
        flight_id: parseInt(flightId),
        seat_numbers: seatNumbers,
      })

      const paymentResponse = await paymentAPI.createCheckoutSession(
        bookingResponse.data.order_id
      )

      if (paymentResponse.data.checkout_url) {
        window.location.href = paymentResponse.data.checkout_url
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Booking failed')
      setBooking(false)
    }
  }

  const formatTime = (timeString) => {
    try {
      return format(parseISO(timeString), 'HH:mm')
    } catch {
      return timeString
    }
  }

  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), 'd MMM')
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div className="booking-page-container">
        <div className="loading-spinner">Завантаження...</div>
      </div>
    )
  }

  if (error && !flight) {
    return (
      <div className="booking-page-container">
        <div className="error-message">{error}</div>
      </div>
    )
  }

  const { rows, seatColumns } = parseSeatMap()
  const activePassengerIndex = passengers.findIndex(p => !p.seat)

  return (
    <div className="booking-page-container">
      {/* Header */}
      <div className="booking-header">
        <div className="header-content">
          <h1 className="header-title">Забронювати місце</h1>
          {flight && (
            <div className="header-flight-info">
              <span className="flight-route">
                {flight.departure_city} - {flight.arrival_city}
              </span>
              <span className="flight-details">
                Рейс {currentStep} з {totalSteps} ({flight.departure_airport_code} - {flight.arrival_airport_code})
              </span>
            </div>
          )}
        </div>
        <button className="close-btn" onClick={() => navigate('/results')}>×</button>
      </div>

      {/* Main Content */}
      <div className="booking-main-content">
        {/* Left Panel - Passenger Information */}
        <aside className="passenger-panel">
          <h2 className="panel-title">Інформація про пасажира</h2>
          {passengers.map((passenger, index) => (
            <div 
              key={index} 
              className={`passenger-card ${activePassengerIndex === index ? 'active' : ''}`}
            >
              <div className="passenger-icon">👤</div>
              <div className="passenger-info">
                <div className="passenger-name">{passenger.name}</div>
                <div className="passenger-status">
                  {passenger.seat ? `Місце: ${passenger.seat}` : 'Не вибрано'}
                </div>
              </div>
            </div>
          ))}
        </aside>

        {/* Middle Panel - Seat Map */}
        <main className="seat-map-panel">
          <h2 className="panel-title">Seat Map</h2>
          <div className="seat-map-container">
            <div className="seat-map-header">
              <div className="seat-columns-header">
                <div className="seat-column-spacer"></div>
                {seatColumns.map(col => (
                  <div key={col} className="seat-column-label">
                    {col}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="seat-map-rows">
              {rows.map(({ rowNumber, seats }) => (
                <div key={rowNumber} className="seat-row">
                  <div className="row-number">{rowNumber}</div>
                  <div className="seat-columns">
                    {seats.map((seat, colIndex) => {
                      const col = seatColumns[colIndex]
                      const seatNumber = seat ? seat.seat_number : null
                      const isSelected = Object.values(selectedSeats).includes(seatNumber)
                      const isAssignedToPassenger = Object.entries(selectedSeats).find(
                        ([idx, sn]) => sn === seatNumber
                      )
                      const passengerIndex = isAssignedToPassenger ? parseInt(isAssignedToPassenger[0]) : null
                      
                      // Check if this is an aisle
                      if (colIndex === 3) {
                        return <div key={`aisle-${rowNumber}`} className="aisle-spacer"></div>
                      }
                      
                      if (!seat) {
                        return <div key={`empty-${rowNumber}-${col}`} className="seat-empty"></div>
                      }
                      
                      const seatStatus = seat.status || 'available'
                      const isAvailable = seatStatus === 'available'
                      const isUnavailable = seatStatus === 'booked' || seatStatus === 'reserved'
                      
                      return (
                        <button
                          key={seatNumber}
                          className={`seat-button ${
                            isSelected ? 'selected' : 
                            isUnavailable ? 'unavailable' : 
                            'available'
                          } ${activePassengerIndex === passengerIndex ? 'assigned-to-active' : ''}`}
                          onClick={() => handleSeatSelect(seatNumber, activePassengerIndex >= 0 ? activePassengerIndex : 0)}
                          disabled={!isAvailable || isSelected}
                          title={seatNumber}
                        >
                          {isUnavailable ? '✕' : seatNumber.slice(-1)}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>

        {/* Right Panel - Legend */}
        <aside className="legend-panel">
          <h2 className="panel-title">Пояснення до схеми місць</h2>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-icon available-icon"></div>
              <div className="legend-content">
                <div className="legend-title">Стандартне сидіння</div>
                <div className="legend-arrow">▼</div>
              </div>
            </div>
            <div className="legend-item">
              <div className="legend-icon unavailable-icon">✕</div>
              <div className="legend-content">
                <div className="legend-title">Недоступно</div>
                <div className="legend-arrow">▼</div>
              </div>
            </div>
            <div className="legend-item">
              <div className="legend-icon selected-icon"></div>
              <div className="legend-content">
                <div className="legend-title">Вибрано</div>
                <div className="legend-arrow">▼</div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Bottom Navigation */}
      <div className="booking-navigation">
        <button 
          className="nav-button back-button" 
          onClick={() => currentStep > 1 ? setCurrentStep(prev => prev - 1) : navigate('/results')}
        >
          Назад
        </button>
        {error && (
          <div className="error-banner">{error}</div>
        )}
        <button 
          className="nav-button next-button" 
          onClick={handleNext}
          disabled={booking || Object.values(selectedSeats).filter(Boolean).length < passengers.length}
        >
          {booking ? 'Обробка...' : 'Далі'}
        </button>
      </div>
    </div>
  )
}

export default BookingPage
