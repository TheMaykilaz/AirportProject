import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { t } from '../translations/translations'
import { flightAPI, bookingAPI, paymentAPI } from '../services/api'
import { format, parseISO } from 'date-fns'
import './BookingPage.css'

const BookingPage = () => {
  const { flightId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { language, formatPrice, convertPrice, currencySymbol } = useLanguage()
  const [flight, setFlight] = useState(null)
  const [seatMap, setSeatMap] = useState(null)
  const [selectedSeats, setSelectedSeats] = useState({}) // { passengerIndex: seatNumber }
  const [loading, setLoading] = useState(true)
  const [booking, setBooking] = useState(false)
  const [error, setError] = useState(null)
  const [passengers, setPassengers] = useState([{
    gender: '',
    firstName: '',
    lastName: '',
    birthDay: '',
    birthMonth: '',
    birthYear: '',
    seat: null
  }])
  const [currentStep, setCurrentStep] = useState(1) // 1 = passenger data, 2 = seat selection
  const [ticketExchange, setTicketExchange] = useState(false)
  const [checkedBaggage, setCheckedBaggage] = useState(false)
  const [baggageProtection, setBaggageProtection] = useState(false)
  const [timerSeconds, setTimerSeconds] = useState(20 * 60) // 20 minutes in seconds

  // Visual-only Passport Autofill toggle (based on ProfilePage prefs in localStorage)
  const PASSPORT_PREFS_KEY = 'passport_autofill_prefs'
  const [passportAutofill, setPassportAutofill] = useState(false)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(PASSPORT_PREFS_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        setPassportAutofill(!!parsed.enabled)
      }
    } catch {}
  }, [])

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/booking/' + flightId)
      return
    }
    loadFlightData()
  }, [flightId, user])

  // Timer countdown
  useEffect(() => {
    if (timerSeconds <= 0) return
    
    const interval = setInterval(() => {
      setTimerSeconds(prev => {
        if (prev <= 1) {
          clearInterval(interval)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [timerSeconds])

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
        gender: '',
        firstName: '',
        lastName: '',
        birthDay: '',
        birthMonth: '',
        birthYear: '',
        seat: null
      }))
      setPassengers(initialPassengers)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load flight data')
    } finally {
      setLoading(false)
    }
  }

  // Categorize seats: window (A, K), middle (B, J), aisle (C, H)
  const categorizeSeats = () => {
    if (!seatMap?.seat_map) return { window: [], middle: [], aisle: [] }
    
    const windowSeats = [] // A, K
    const middleSeats = [] // B, J
    const aisleSeats = [] // C, H
    
    seatMap.seat_map.forEach(seat => {
      const match = seat.seat_number.match(/^(\d+)([A-Z]+)$/)
      if (match) {
        const col = match[2]
        const seatData = { ...seat, row: parseInt(match[1]), col }
        
        if (col === 'A' || col === 'K') {
          windowSeats.push(seatData)
        } else if (col === 'B' || col === 'J') {
          middleSeats.push(seatData)
        } else if (col === 'C' || col === 'H') {
          aisleSeats.push(seatData)
        }
      }
    })
    
    // Sort by row number
    const sortByRow = (a, b) => a.row - b.row
    windowSeats.sort(sortByRow)
    middleSeats.sort(sortByRow)
    aisleSeats.sort(sortByRow)
    
    return { window: windowSeats, middle: middleSeats, aisle: aisleSeats }
  }

  const handlePassengerChange = (index, field, value) => {
    setPassengers(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
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

  const validatePassengerData = () => {
    for (let i = 0; i < passengers.length; i++) {
      const p = passengers[i]
      if (!p.gender || !p.firstName || !p.lastName || !p.birthDay || !p.birthMonth || !p.birthYear) {
        return false
      }
    }
    return true
  }

  const handleNext = async () => {
    if (currentStep === 1) {
      if (!validatePassengerData()) {
        setError(t('pleaseFillAllFields', language))
        return
      }
      setCurrentStep(2)
      setError(null)
    } else if (currentStep === 2) {
      const seatNumbers = Object.values(selectedSeats).filter(Boolean)
      
      if (seatNumbers.length < passengers.length) {
        setError(t('pleaseSelectSeat', language))
        return
      }

    setBooking(true)
    setError(null)

    try {
      const bookingResponse = await bookingAPI.createBooking({
        flight_id: parseInt(flightId),
          seat_numbers: seatNumbers,
      })

      // Calculate surcharge for selected extra services (USD)
      const passengerCount = passengers.length
      let surchargeUSD = 0
      if (ticketExchange) surchargeUSD += (2159 / 42) * passengerCount
      if (checkedBaggage) surchargeUSD += (3484 / 42) * passengerCount
      if (baggageProtection) surchargeUSD += (362 / 42) * passengerCount

      const paymentResponse = await paymentAPI.createCheckoutSession(
        bookingResponse.data.order_id,
        Number(surchargeUSD.toFixed(2))
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
      return format(parseISO(dateString), 'EEE, d MMM')
    } catch {
      return dateString
    }
  }

  // Calculate total price in USD; displayPrice() will convert to chosen currency
  const calculateTotalPrice = () => {
    if (!flight) return 0
    const basePriceUSD = parseFloat(flight.min_price || 0)
    const passengerCount = passengers.length
    let totalUSD = basePriceUSD * passengerCount
    if (ticketExchange) totalUSD += (2159 / 42) * passengerCount
    if (checkedBaggage) totalUSD += (3484 / 42) * passengerCount
    if (baggageProtection) totalUSD += (362 / 42) * passengerCount
    return totalUSD
  }
  
  // Format price for display (priceUSD is already in USD)
  const displayPrice = (priceUSD) => {
    const converted = convertPrice(priceUSD, 'USD')
    if (currencySymbol === '₴') {
      return `${converted.toFixed(2)} грн`
    }
    return `$${converted.toFixed(2)}`
  }

  // Format timer
  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
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

  const { window: windowSeats, middle: middleSeats, aisle: aisleSeats } = categorizeSeats()
  const activePassengerIndex = passengers.findIndex(p => !p.seat)

  return (
    <div className="booking-page-container">
      {/* Header */}
      <div className="booking-header">
        <div className="header-content">
          <h1 className="header-title">
            {currentStep === 1 ? t('passengerData', language) : t('bookSeat', language)}
          </h1>
          {flight && (
            <div className="header-flight-info">
              <span className="flight-route">
                {flight.departure_city} - {flight.arrival_city}
              </span>
              <span className="flight-details">
                {formatTime(flight.departure_time)} - {formatTime(flight.arrival_time)}
              </span>
            </div>
          )}
        </div>
        <button className="close-btn" onClick={() => navigate('/results')}>×</button>
      </div>

      {/* Main Content */}
      {currentStep === 1 ? (
        <div className="booking-passenger-form">
          <div className="form-main-content">
            <div className="passenger-form-section">
              <h2 className="form-section-title">{t('passengerData', language)}</h2>
              <div className="checkbox-group" style={{ marginBottom: '12px' }}>
                <input
                  type="checkbox"
                  id="passport-autofill"
                  checked={passportAutofill}
                  onChange={(e) => {
                    setPassportAutofill(e.target.checked)
                    try {
                      const raw = localStorage.getItem(PASSPORT_PREFS_KEY)
                      const base = raw ? JSON.parse(raw) : {}
                      localStorage.setItem(PASSPORT_PREFS_KEY, JSON.stringify({ ...base, enabled: e.target.checked }))
                    } catch {}
                  }}
                />
                <label htmlFor="passport-autofill">
                  Автозаповнення даних паспорта
                </label>
              </div>
              
              {passengers.map((passenger, index) => (
                <div key={index} className="passenger-form-block">
                  <h3 className="passenger-form-subtitle">{t('passenger', language)} {index + 1}, {t('adult', language)}</h3>
                  
                  <div className="form-group">
                    <label>{t('gender', language)}</label>
                    <div className="radio-group">
                      <label className="radio-label">
                        <input
                          type="radio"
                          name={`gender-${index}`}
                          value="male"
                          checked={passenger.gender === 'male'}
                          onChange={(e) => handlePassengerChange(index, 'gender', e.target.value)}
                        />
                        <span>{t('male', language)}</span>
                      </label>
                      <label className="radio-label">
                        <input
                          type="radio"
                          name={`gender-${index}`}
                          value="female"
                          checked={passenger.gender === 'female'}
                          onChange={(e) => handlePassengerChange(index, 'gender', e.target.value)}
                        />
                        <span>{t('female', language)}</span>
                      </label>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>
                      {t('firstName', language)}
                      {!passenger.firstName && <span className="error-icon">!</span>}
                    </label>
                    <input
                      type="text"
                      value={passenger.firstName}
                      onChange={(e) => handlePassengerChange(index, 'firstName', e.target.value)}
                      className={!passenger.firstName ? 'error' : ''}
                    />
                    {!passenger.firstName && (
                      <span className="error-message">{t('enterFirstName', language)}</span>
                    )}
                  </div>

                  <div className="form-group">
                    <label>
                      {t('lastName', language)}
                      {!passenger.lastName && <span className="error-icon">!</span>}
                    </label>
                    <input
                      type="text"
                      value={passenger.lastName}
                      onChange={(e) => handlePassengerChange(index, 'lastName', e.target.value)}
                      className={!passenger.lastName ? 'error' : ''}
                    />
                    {!passenger.lastName && (
                      <span className="error-message">{t('enterLastName', language)}</span>
                    )}
                  </div>

                  <div className="form-group">
                    <label>{t('dateOfBirth', language)}</label>
                    <div className="date-inputs">
                      <input
                        type="text"
                        placeholder={t('day', language)}
                        maxLength="2"
                        value={passenger.birthDay}
                        onChange={(e) => handlePassengerChange(index, 'birthDay', e.target.value)}
                      />
                      <select
                        value={passenger.birthMonth}
                        onChange={(e) => handlePassengerChange(index, 'birthMonth', e.target.value)}
                      >
                        <option value="">{t('month', language)}</option>
                        {Array.from({ length: 12 }, (_, i) => (
                          <option key={i + 1} value={i + 1}>{i + 1}</option>
                        ))}
                      </select>
                      <input
                        type="text"
                        placeholder={t('year', language)}
                        maxLength="4"
                        value={passenger.birthYear}
                        onChange={(e) => handlePassengerChange(index, 'birthYear', e.target.value)}
                      />
                    </div>
                  </div>

                  <a href="#" className="info-link">{t('whatAboutPassport', language)} ℹ️</a>

                  <div className="checkbox-group">
                    <input
                      type="checkbox"
                      id={`exchange-${index}`}
                      checked={ticketExchange}
                      onChange={(e) => setTicketExchange(e.target.checked)}
                    />
                    <label htmlFor={`exchange-${index}`}>
                      {t('ticketExchange', language)} ℹ️ <span className="price-tag">{displayPrice(2159 / 42)}</span>
                    </label>
                  </div>
                </div>
              ))}

              <div className="baggage-section">
                <h2 className="form-section-title">{t('baggageAllowance', language)}</h2>
                
                <div className="baggage-item included">
                  <div className="baggage-icon">👜</div>
                  <div className="baggage-info">
                    <div className="baggage-name">{t('smallBag', language)}</div>
                    <div className="baggage-desc">{t('underSeat', language)}</div>
                    <div className="baggage-size">22х25х43 см</div>
                  </div>
                  <div className="baggage-status">{t('included', language)}</div>
                </div>

                <div className="baggage-item included">
                  <div className="baggage-icon">🧳</div>
                  <div className="baggage-info">
                    <div className="baggage-name">{t('handLuggage2', language)}</div>
                    <div className="baggage-desc">{t('standard', language)}</div>
                    <div className="baggage-size">55х35х23 см (7 кг)</div>
                  </div>
                  <div className="baggage-status">{t('included', language)}</div>
                  <div className="baggage-free">✓ {t('free', language)}</div>
                  <div className="baggage-count">1 од. (7 кг)</div>
                </div>

                <div className="baggage-item optional">
                  <div className="baggage-icon">🧳</div>
                  <div className="baggage-info">
                    <div className="baggage-name">{t('checkedBaggage', language)}</div>
                    <div className="baggage-desc">{t('regularSuitcases', language)}</div>
                    <div className="baggage-size">23 кг - 1 од.</div>
                  </div>
                  <div className="baggage-status-optional">ДОДАТКОВА ОПЦІЯ</div>
                  
                  <div className="baggage-options">
                    <label className="radio-label">
                      <input
                        type="radio"
                        name="checked-baggage"
                        checked={checkedBaggage}
                        onChange={() => setCheckedBaggage(true)}
                      />
                      <span>{t('add', language)}</span>
                      <span className="price-highlight">{t('cheaperNow', language)}</span>
                      <span className="price-tag">{displayPrice(3484 / 42)}/переліт</span>
                    </label>
                    <label className="radio-label">
                      <input
                        type="radio"
                        name="checked-baggage"
                        checked={!checkedBaggage}
                        onChange={() => setCheckedBaggage(false)}
                      />
                      <span>{t('withoutCheckedBaggage', language)}</span>
                    </label>
                  </div>

                  <div className="checkbox-group">
                    <input
                      type="checkbox"
                      id="baggage-protection"
                      checked={baggageProtection}
                      onChange={(e) => setBaggageProtection(e.target.checked)}
                    />
                    <label htmlFor="baggage-protection">
                      {t('baggageProtection', language)} ℹ️ <span className="price-tag">{displayPrice(362 / 42)}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <aside className="booking-summary-sidebar">
              <div className="summary-section">
                <h3>{t('flight', language)}</h3>
                <a href="#" className="summary-link">{t('travelDetails', language)}</a>
                {flight && (
                  <>
                    <div className="flight-summary-item">
                      <span className="flight-icon">✈️</span>
                      <div className="flight-summary-details">
                        <div className="flight-time">{formatTime(flight.departure_time)} - {formatTime(flight.arrival_time)}</div>
                        <div className="flight-date">{formatDate(flight.departure_time)}</div>
                        <div className="flight-airline">{flight.airline_name || 'Airline'}</div>
                        <div className="flight-route">{flight.departure_airport_code}-{flight.arrival_airport_code}</div>
                        <div className="flight-duration">8г 30хв ({t('direct', language)})</div>
                        <div className="flight-class">{t('economy', language)}</div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="summary-section">
                <h3>{t('passengers2', language)}</h3>
                <p className="summary-note">{t('ensureDataMatches', language)}</p>
                {passengers.map((_, index) => (
                  <div key={index} className="passenger-summary-item">
                    <span className="passenger-icon">👤</span>
                    <span>{t('passenger', language)} {index + 1}</span>
                    <span className="baggage-icons">🧳👜</span>
                  </div>
                ))}
              </div>

              <div className="summary-section">
                <h3>{t('price', language)}</h3>
                <a href="#" className="summary-link" onClick={(e) => {
                  e.preventDefault()
                  const details = e.target.closest('.summary-section').querySelector('.price-details')
                  if (details) {
                    details.style.display = details.style.display === 'none' ? 'block' : 'none'
                  }
                }}>{t('details2', language)} ▼</a>
                <div className="price-details" style={{ display: 'none', marginTop: '12px', fontSize: '12px', color: 'rgba(255, 255, 255, 0.7)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>{t('baseTariff', language)} ({passengers.length} {passengers.length === 1 ? t('passenger2', language) : t('passengers3', language)}):</span>
                    <span>{displayPrice(parseFloat(flight?.min_price || 0) * passengers.length)}</span>
                  </div>
                  {ticketExchange && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span>{t('ticketExchange', language)} ({passengers.length} {passengers.length === 1 ? t('passenger2', language) : t('passengers3', language)}):</span>
                      <span>{displayPrice((2159 / 42) * passengers.length)}</span>
                    </div>
                  )}
                  {checkedBaggage && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span>{t('checkedBaggage', language)} ({passengers.length} {passengers.length === 1 ? t('passenger2', language) : t('passengers3', language)}):</span>
                      <span>{displayPrice((3484 / 42) * passengers.length)}</span>
                    </div>
                  )}
                  {baggageProtection && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span>{t('baggageProtection', language)} ({passengers.length} {passengers.length === 1 ? t('passenger2', language) : t('passengers3', language)}):</span>
                      <span>{displayPrice((362 / 42) * passengers.length)}</span>
                    </div>
                  )}
                </div>
                <div className="total-price">{displayPrice(calculateTotalPrice())}</div>
                <p className="price-note">{t('securePrice', language)}</p>
                <div className="price-lock">
                  <span className="lock-icon">🕐</span>
                  <span>{t('fareBooked', language)}</span>
                  <span className="timer">{formatTimer(timerSeconds)}</span>
                </div>
              </div>
            </aside>
          </div>
        </div>
      ) : (
        <div className="booking-seat-selection">
          <div className="seat-selection-content">
            <h2 className="seat-selection-title">{t('selectSeat', language)}</h2>
            
            <div className="seat-categories">
              <div className="seat-category">
                <h3 className="category-title">{t('windowSeats', language)}</h3>
                <div className="seat-grid">
                  {windowSeats.map((seat) => {
                    const isSelected = Object.values(selectedSeats).includes(seat.seat_number)
                    const passengerIndex = Object.entries(selectedSeats).find(
                      ([idx, sn]) => sn === seat.seat_number
                    )?.[0]
                    const isAvailable = seat.status === 'available'
                    
                    return (
                      <button
                        key={seat.seat_number}
                        className={`seat-button ${
                          isSelected ? 'selected' : 
                          !isAvailable ? 'unavailable' : 
                          'available'
                        }`}
                        onClick={() => handleSeatSelect(seat.seat_number, activePassengerIndex >= 0 ? activePassengerIndex : 0)}
                        disabled={!isAvailable || isSelected}
                        title={seat.seat_number}
                      >
                        {!isAvailable ? '✕' : seat.seat_number}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="seat-category">
                <h3 className="category-title">{t('middleSeats', language)}</h3>
                <div className="seat-grid">
                  {middleSeats.map((seat) => {
                    const isSelected = Object.values(selectedSeats).includes(seat.seat_number)
                    const passengerIndex = Object.entries(selectedSeats).find(
                      ([idx, sn]) => sn === seat.seat_number
                    )?.[0]
                    const isAvailable = seat.status === 'available'
                    
                    return (
                      <button
                        key={seat.seat_number}
                        className={`seat-button ${
                          isSelected ? 'selected' : 
                          !isAvailable ? 'unavailable' : 
                          'available'
                        }`}
                        onClick={() => handleSeatSelect(seat.seat_number, activePassengerIndex >= 0 ? activePassengerIndex : 0)}
                        disabled={!isAvailable || isSelected}
                        title={seat.seat_number}
                      >
                        {!isAvailable ? '✕' : seat.seat_number}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="seat-category">
                <h3 className="category-title">{t('aisleSeats', language)}</h3>
                <div className="seat-grid">
                  {aisleSeats.map((seat) => {
                    const isSelected = Object.values(selectedSeats).includes(seat.seat_number)
                    const passengerIndex = Object.entries(selectedSeats).find(
                      ([idx, sn]) => sn === seat.seat_number
                    )?.[0]
                    const isAvailable = seat.status === 'available'
                    
                    return (
                      <button
                        key={seat.seat_number}
                        className={`seat-button ${
                          isSelected ? 'selected' : 
                          !isAvailable ? 'unavailable' : 
                          'available'
                        }`}
                        onClick={() => handleSeatSelect(seat.seat_number, activePassengerIndex >= 0 ? activePassengerIndex : 0)}
                        disabled={!isAvailable || isSelected}
                        title={seat.seat_number}
                      >
                        {!isAvailable ? '✕' : seat.seat_number}
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>

            <div className="seat-legend">
              <div className="legend-item">
                <div className="legend-icon available-icon"></div>
                <span>{t('available', language)}</span>
              </div>
              <div className="legend-item">
                <div className="legend-icon unavailable-icon">✕</div>
                <span>{t('unavailable', language)}</span>
              </div>
              <div className="legend-item">
                <div className="legend-icon selected-icon"></div>
                <span>{t('selected', language)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <div className="booking-navigation">
        <button 
          className="nav-button back-button" 
          onClick={() => currentStep > 1 ? setCurrentStep(1) : navigate('/results')}
        >
          {t('back', language)}
        </button>
        {error && (
          <div className="error-banner">{error}</div>
        )}
        <button 
          className="nav-button next-button" 
          onClick={handleNext}
          disabled={booking || (currentStep === 2 && Object.values(selectedSeats).filter(Boolean).length < passengers.length)}
        >
          {booking ? t('processing', language) : t('next', language)}
        </button>
      </div>
    </div>
  )
}

export default BookingPage
