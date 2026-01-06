import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { format, parseISO, differenceInHours, differenceInMinutes } from 'date-fns'
import { flightAPI } from '../services/api'
import './FlightResultsPage.css'

const FlightResultsPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [flights, setFlights] = useState([])
  const [returnFlights, setReturnFlights] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [priceStats, setPriceStats] = useState(null)
  const [selectedFlight, setSelectedFlight] = useState(null)
  const [filters, setFilters] = useState({
    baggageIncluded: false,
    layoverDuration: 24,
    noOvernightLayovers: false,
    convenientLayovers: false,
    sortBy: 'price', // 'price' or 'duration'
    directFlightsOnly: false,
    noVisaRequired: false,
  })

  useEffect(() => {
    searchFlights()
  }, [searchParams])

  const searchFlights = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = Object.fromEntries(searchParams.entries())
      // Convert city names to airport codes if needed
      if (params.departure_city && !params.departure_airport_code) {
        params.departure_airport_code = getAirportCode(params.departure_city)
      }
      if (params.arrival_city && !params.arrival_airport_code) {
        params.arrival_airport_code = getAirportCode(params.arrival_city)
      }
      
      const response = await flightAPI.search(params)
      setFlights(response.data.results || [])
      setReturnFlights(response.data.return_results || [])
      setPriceStats(response.data.price_stats)
      // Auto-select first flight for booking sidebar
      if (response.data.results && response.data.results.length > 0) {
        setSelectedFlight(response.data.results[0])
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to search flights')
    } finally {
      setLoading(false)
    }
  }

  const getAirportCode = (city) => {
    const codes = {
      'krakow': 'KRK', 'kraków': 'KRK',
      'tashkent': 'TAS',
      'london': 'LHR', 'lhr': 'LHR',
      'new york': 'JFK', 'jfk': 'JFK',
      'paris': 'CDG', 'cdg': 'CDG',
      'harbin': 'HRB', 'phuket': 'HKT'
    }
    return codes[city.toLowerCase()] || city.toUpperCase().slice(0, 3)
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
      return format(parseISO(dateString), 'EEE d MMM')
    } catch {
      return dateString
    }
  }

  const formatDateShort = (dateString) => {
    try {
      return format(parseISO(dateString), 'd MMM')
    } catch {
      return dateString
    }
  }

  const formatDuration = (duration) => {
    if (!duration) return 'N/A'
    const parts = duration.split(':')
    if (parts.length >= 2) {
      const hours = parseInt(parts[0])
      const minutes = parseInt(parts[1])
      if (hours > 0 && minutes > 0) {
        return `${hours} год. ${minutes} хв.`
      } else if (hours > 0) {
        return `${hours} год.`
      } else {
        return `${minutes} хв.`
      }
    }
    return duration
  }

  const calculateTotalDuration = (departureTime, arrivalTime) => {
    try {
      const dep = parseISO(departureTime)
      const arr = parseISO(arrivalTime)
      const totalHours = differenceInHours(arr, dep)
      const totalMinutes = differenceInMinutes(arr, dep) % 60
      
      if (totalHours >= 24) {
        const days = Math.floor(totalHours / 24)
        const hours = totalHours % 24
        return `${days} д. ${hours} год. ${totalMinutes} хв.`
      }
      return `${totalHours} год. ${totalMinutes} хв.`
    } catch {
      return 'N/A'
    }
  }

  const calculateFlightTime = (departureTime, arrivalTime) => {
    try {
      const dep = parseISO(departureTime)
      const arr = parseISO(arrivalTime)
      const hours = differenceInHours(arr, dep)
      const minutes = differenceInMinutes(arr, dep) % 60
      return `${hours} год. ${minutes} хв.`
    } catch {
      return 'N/A'
    }
  }

  const getBadge = (flight, allFlights) => {
    if (!allFlights || allFlights.length === 0) return null
    
    const cheapest = allFlights.reduce((min, f) => 
      parseFloat(f.min_price) < parseFloat(min.min_price) ? f : min, allFlights[0])
    
    if (flight.flight_id === cheapest.flight_id) {
      return { type: 'cheapest', text: 'Cheapest' }
    }
    
    return null
  }

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }))
  }

  const buyFlight = (flight) => {
    navigate(`/booking/${flight.flight_id}`)
  }

  const departureCity = searchParams.get('departure_city') || searchParams.get('departure_airport_code') || 'Krakow'
  const arrivalCity = searchParams.get('arrival_city') || searchParams.get('arrival_airport_code') || 'Tashkent'
  const departureDate = searchParams.get('departure_date') || ''
  const returnDate = searchParams.get('return_date') || ''
  const passengers = searchParams.get('passengers') || '1'
  const flightClass = searchParams.get('class') || 'Economy'

  if (loading) {
    return (
      <div className="flight-results-container">
        <div className="loading-spinner">Loading flights...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flight-results-container">
        <div className="error-message">{error}</div>
      </div>
    )
  }

  // Apply filters and sorting
  const applyFiltersAndSort = (flightList) => {
    let filtered = [...flightList]

    // Filter: Direct flights only
    if (filters.directFlightsOnly) {
      filtered = filtered.filter(flight => {
        // Assuming direct flights have no layovers (you may need to adjust based on your data structure)
        return !flight.has_layovers || flight.layover_count === 0
      })
    }

    // Filter: No visa required
    if (filters.noVisaRequired) {
      filtered = filtered.filter(flight => {
        // This would need to be based on your flight data structure
        // For now, we'll assume all flights pass this filter
        return true
      })
    }

    // Filter: No overnight layovers
    if (filters.noOvernightLayovers) {
      filtered = filtered.filter(flight => {
        // Check if flight has overnight layovers
        return !flight.has_overnight_layover
      })
    }

    // Sort
    if (filters.sortBy === 'price') {
      filtered.sort((a, b) => parseFloat(a.min_price) - parseFloat(b.min_price))
    } else if (filters.sortBy === 'duration') {
      filtered.sort((a, b) => {
        const durationA = calculateTotalDurationMinutes(a.departure_time, a.arrival_time)
        const durationB = calculateTotalDurationMinutes(b.departure_time, b.arrival_time)
        return durationA - durationB
      })
    }

    return filtered
  }

  const calculateTotalDurationMinutes = (departureTime, arrivalTime) => {
    try {
      const dep = parseISO(departureTime)
      const arr = parseISO(arrivalTime)
      return differenceInMinutes(arr, dep)
    } catch {
      return 0
    }
  }

  const filteredFlights = applyFiltersAndSort(flights)
  const filteredReturnFlights = applyFiltersAndSort(returnFlights)
  const allFlights = [...filteredFlights, ...filteredReturnFlights]
  const displayFlight = selectedFlight || (allFlights.length > 0 ? allFlights[0] : null)

  return (
    <div className="flight-results-container">
      <div className="top-bar">
        <div className="search-params">
          <div className="param-item">
            <span>{departureCity}</span>
            <span className="param-value">{getAirportCode(departureCity)}</span>
          </div>
          <span>→</span>
          <div className="param-item">
            <span>{arrivalCity}</span>
            <span className="param-value">{getAirportCode(arrivalCity)}</span>
          </div>
          {departureDate && (
            <div className="param-item">
              <span>{formatDate(departureDate)}</span>
            </div>
          )}
          {returnDate && (
            <div className="param-item">
              <span>{formatDate(returnDate)}</span>
            </div>
          )}
          <div className="param-item">
            <span>{passengers} passenger{passengers !== '1' ? 's' : ''} {flightClass}</span>
          </div>
        </div>
        <div>
          <button className="search-again-btn" onClick={() => navigate('/search')}>
            Search flights
          </button>
          <a href="#" className="multi-city-link" onClick={(e) => e.preventDefault()}>
            Create multi-city route
          </a>
        </div>
      </div>

      <div className="main-content-wrapper">
        <div className="main-content">
          <aside className="sidebar">
            <button className="save-search-btn" onClick={() => alert('Search saved!')}>
              ❤️ Save search
            </button>

            <div className="sidebar-section">
              <h3>Сортування</h3>
              <div className="filter-option">
                <input 
                  type="radio" 
                  id="sort_price" 
                  name="sortBy"
                  checked={filters.sortBy === 'price'}
                  onChange={() => handleFilterChange('sortBy', 'price')}
                />
                <label htmlFor="sort_price">
                  <span>Фільтрувати по ціні (найменша спочатку)</span>
                </label>
              </div>
              <div className="filter-option">
                <input 
                  type="radio" 
                  id="sort_duration" 
                  name="sortBy"
                  checked={filters.sortBy === 'duration'}
                  onChange={() => handleFilterChange('sortBy', 'duration')}
                />
                <label htmlFor="sort_duration">
                  <span>Фільтрувати по часу подорожі (найшвидше спочатку)</span>
                </label>
              </div>
            </div>

            <div className="sidebar-section">
              <h3>Тип рейсу</h3>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="direct_flights_only"
                  checked={filters.directFlightsOnly}
                  onChange={(e) => handleFilterChange('directFlightsOnly', e.target.checked)}
                />
                <label htmlFor="direct_flights_only">Тільки прямі рейси</label>
              </div>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="no_visa_required"
                  checked={filters.noVisaRequired}
                  onChange={(e) => handleFilterChange('noVisaRequired', e.target.checked)}
                />
                <label htmlFor="no_visa_required">Без додаткової візи під час польоту</label>
              </div>
            </div>

            <div className="sidebar-section">
              <h3>Baggage</h3>
              <div className="filter-option">
                <input 
                  type="checkbox" 
                  id="baggage_included" 
                  checked={filters.baggageIncluded}
                  onChange={(e) => handleFilterChange('baggageIncluded', e.target.checked)}
                />
                <label htmlFor="baggage_included">
                  <span>Baggage included</span>
                  {priceStats && <span className="filter-price">${parseFloat(priceStats.max).toFixed(0)}</span>}
                </label>
              </div>
            </div>

            <div className="sidebar-section">
              <h3>Layovers</h3>
              <div className="slider-container">
                <input 
                  type="range" 
                  min="0" 
                  max="24" 
                  value={filters.layoverDuration}
                  className="slider" 
                  onChange={(e) => handleFilterChange('layoverDuration', parseInt(e.target.value))}
                />
                <div className="slider-value">
                  Layover duration: Up to <span id="duration_value">{filters.layoverDuration}</span>hr
                </div>
              </div>
            </div>

            <div className="sidebar-section">
              <h3>Layover conditions</h3>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="convenient_layovers"
                  checked={filters.convenientLayovers}
                  onChange={(e) => handleFilterChange('convenientLayovers', e.target.checked)}
                />
                <label htmlFor="convenient_layovers">Convenient layovers</label>
              </div>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="no_overnight_layovers"
                  checked={filters.noOvernightLayovers}
                  onChange={(e) => handleFilterChange('noOvernightLayovers', e.target.checked)}
                />
                <label htmlFor="no_overnight_layovers">No overnight layovers</label>
              </div>
            </div>
          </aside>

          <div className="results-area">
            {flights.length > 0 && (
              <div className="fare-summary">
                <h3>Cheapest fare with baggage</h3>
                <div className="fare-features">
                  <span>Hand luggage 1x5 kg</span>
                  <span>Baggage 1x23 kg</span>
                  <span>No exchange</span>
                  <span>No refund</span>
                </div>
                <div className="fare-more">
                  <span>If other conditions are needed, suitable fares will be found</span>
                  <span>→</span>
                </div>
              </div>
            )}

            {flights.length > 0 && (
              <div className="flight-section">
                <h3 className="section-title">
                  {departureCity} — {arrivalCity}
                </h3>
                {filteredFlights.map((flight) => {
                  const badge = getBadge(flight, filteredFlights)
                  const totalDuration = calculateTotalDuration(flight.departure_time, flight.arrival_time)
                  const flightTime = calculateFlightTime(flight.departure_time, flight.arrival_time)
                  
                  return (
                    <div 
                      key={flight.flight_id} 
                      className={`flight-result-card ${selectedFlight?.flight_id === flight.flight_id ? 'selected' : ''}`}
                      onClick={() => setSelectedFlight(flight)}
                    >
                      <div className="flight-route-header">
                        <div className="route-info">
                          <span className="route-cities">{departureCity} — {arrivalCity}</span>
                          <span className="route-duration">{totalDuration} в дорозі</span>
                        </div>
                      </div>

                      <div className="flight-segment-detailed">
                        <div className="segment-header">
                          <div className="airline-info">
                            <div className="airline-logo-small">{flight.airline_code || 'FL'}</div>
                            <div>
                              <div className="airline-name">{flight.airline_name || 'Airline'}</div>
                              <div className="flight-time-info">{flightTime} в польоті</div>
                            </div>
                          </div>
                        </div>

                        <div className="segment-details">
                          <div className="segment-departure">
                            <div className="segment-time">{formatTime(flight.departure_time)}</div>
                            <div className="segment-location">
                              <div className="location-city">{flight.departure_city}</div>
                              <div className="location-date">{formatDateShort(flight.departure_time)}</div>
                              <div className="location-airport">{flight.departure_airport_name}, {flight.departure_airport_code}</div>
                            </div>
                          </div>

                          <div className="segment-arrival">
                            <div className="segment-time">{formatTime(flight.arrival_time)}</div>
                            <div className="segment-location">
                              <div className="location-city">{flight.arrival_city}</div>
                              <div className="location-date">{formatDateShort(flight.arrival_time)}</div>
                              <div className="location-airport">{flight.arrival_airport_name}, {flight.arrival_airport_code}</div>
                            </div>
                          </div>
                        </div>

                        <button className="details-btn">Детальніше</button>
                      </div>

                      <div className="flight-action">
                        <button 
                          className="price-btn"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedFlight(flight)
                          }}
                        >
                          від {parseFloat(flight.min_price).toFixed(0)} ₴
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {returnFlights.length > 0 && (
              <div className="flight-section">
                <h3 className="section-title">
                  {arrivalCity} — {departureCity}
                </h3>
                {filteredReturnFlights.map((flight) => {
                  const totalDuration = calculateTotalDuration(flight.departure_time, flight.arrival_time)
                  const flightTime = calculateFlightTime(flight.departure_time, flight.arrival_time)
                  
                  return (
                    <div 
                      key={`return-${flight.flight_id}`} 
                      className={`flight-result-card ${selectedFlight?.flight_id === flight.flight_id ? 'selected' : ''}`}
                      onClick={() => setSelectedFlight(flight)}
                    >
                      <div className="flight-route-header">
                        <div className="route-info">
                          <span className="route-cities">{arrivalCity} — {departureCity}</span>
                          <span className="route-duration">{totalDuration} в дорозі</span>
                        </div>
                      </div>

                      <div className="flight-segment-detailed">
                        <div className="segment-header">
                          <div className="airline-info">
                            <div className="airline-logo-small">{flight.airline_code || 'FL'}</div>
                            <div>
                              <div className="airline-name">{flight.airline_name || 'Airline'}</div>
                              <div className="flight-time-info">{flightTime} в польоті</div>
                            </div>
                          </div>
                        </div>

                        <div className="segment-details">
                          <div className="segment-departure">
                            <div className="segment-time">{formatTime(flight.departure_time)}</div>
                            <div className="segment-location">
                              <div className="location-city">{flight.departure_city}</div>
                              <div className="location-date">{formatDateShort(flight.departure_time)}</div>
                              <div className="location-airport">{flight.departure_airport_name}, {flight.departure_airport_code}</div>
                            </div>
                          </div>

                          <div className="segment-arrival">
                            <div className="segment-time">{formatTime(flight.arrival_time)}</div>
                            <div className="segment-location">
                              <div className="location-city">{flight.arrival_city}</div>
                              <div className="location-date">{formatDateShort(flight.arrival_time)}</div>
                              <div className="location-airport">{flight.arrival_airport_name}, {flight.arrival_airport_code}</div>
                            </div>
                          </div>
                        </div>

                        <button className="details-btn">Детальніше</button>
                      </div>

                      <div className="flight-action">
                        <button 
                          className="price-btn"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedFlight(flight)
                          }}
                        >
                          від {parseFloat(flight.min_price).toFixed(0)} ₴
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {allFlights.length === 0 && (
              <div className="flight-result-card">
                <p>No flights found. Try adjusting your search criteria.</p>
              </div>
            )}
          </div>
        </div>

        {displayFlight && (
          <aside className="booking-sidebar">
            <div className="booking-card">
              <div className="booking-price">
                <div className="price-amount-large">{parseFloat(displayFlight.min_price).toFixed(0)} ₴</div>
                <div className="price-provider">Airport Project</div>
              </div>
              
              <button 
                className="buy-btn"
                onClick={() => buyFlight(displayFlight)}
              >
                Купити
              </button>

              <div className="trust-message">
                <span className="trust-icon">✓</span>
                <span>Усім продавцям можна довіряти, але якщо будуть питання — ми поруч</span>
              </div>

              <div className="booking-note">
                <p>Follow instructions on the seller's website</p>
                <p className="poetic">Time flies, but flights take time</p>
              </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}

export default FlightResultsPage
