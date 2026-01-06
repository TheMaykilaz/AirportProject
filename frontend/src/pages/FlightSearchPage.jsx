import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import './FlightSearchPage.css'

const FlightSearchPage = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('flights')
  const [formData, setFormData] = useState({
    departure_city: '',
    arrival_city: '',
    departure_date: '',
    return_date: '',
    passengers: 1,
    class: 'economy',
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
      if (value && (key !== 'return_date' || formData.return_date)) {
        params.append(key, value)
      }
    })

    navigate(`/results?${params.toString()}`)
  }

  const swapAirports = () => {
    setFormData((prev) => ({
      ...prev,
      departure_city: prev.arrival_city,
      arrival_city: prev.departure_city,
    }))
  }

  const clearDate = (fieldName) => {
    setFormData((prev) => ({
      ...prev,
      [fieldName]: '',
    }))
  }

  const togglePassengerMenu = () => {
    const passengers = prompt('Enter number of passengers (1-9):', formData.passengers.toString())
    if (passengers && parseInt(passengers) >= 1 && parseInt(passengers) <= 9) {
      setFormData((prev) => ({
        ...prev,
        passengers: parseInt(passengers),
      }))
    }
    
    const classes = ['Economy', 'Business', 'First']
    const selectedClass = prompt('Select class:\n1. Economy\n2. Business\n3. First', 
      classes.findIndex(c => c.toLowerCase() === formData.class) + 1)
    if (selectedClass) {
      const classIndex = parseInt(selectedClass) - 1
      if (classIndex >= 0 && classIndex < classes.length) {
        setFormData((prev) => ({
          ...prev,
          class: classes[classIndex].toLowerCase(),
        }))
      }
    }
  }

  const today = format(new Date(), 'yyyy-MM-dd')

  return (
    <div className="flight-search-container">
      <h1 className="search-title">Search cheap flight tickets</h1>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'flights' ? 'active' : ''}`}
          onClick={() => setActiveTab('flights')}
        >
          <span className="tab-icon">✈️</span>
          <span>Flights</span>
        </button>
        <button 
          className={`tab ${activeTab === 'hotels' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('hotels')
            navigate('/hotels')
          }}
        >
          <span className="tab-icon">🏨</span>
          <span>Hotels</span>
        </button>
        <button 
          className={`tab ${activeTab === 'favorites' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('favorites')
            alert('Favorites feature coming soon!')
          }}
        >
          <span className="tab-icon">❤️</span>
          <span>Favorites</span>
        </button>
      </div>

      <div className="search-form-container">
        <form id="flightSearchForm" className="search-form" onSubmit={handleSubmit}>
          <div className="form-field departure">
            <label>From</label>
            <input 
              type="text" 
              name="departure_city" 
              placeholder="City or airport" 
              value={formData.departure_city}
              onChange={handleChange}
              autoComplete="off"
            />
            <div className="airport-code" id="departure_code"></div>
          </div>
          
          <button 
            type="button" 
            className="swap-button" 
            onClick={swapAirports}
            title="Swap airports"
          >
            ⇄
          </button>
          
          <div className="form-field arrival">
            <label>To</label>
            <input 
              type="text" 
              name="arrival_city" 
              placeholder="City or airport" 
              value={formData.arrival_city}
              onChange={handleChange}
              autoComplete="off"
            />
            <div className="airport-code" id="arrival_code"></div>
          </div>
          
          <div className="form-field dates">
            <label>Departure</label>
            <div style={{ position: 'relative' }}>
              <input 
                type="date" 
                name="departure_date" 
                value={formData.departure_date}
                onChange={handleChange}
                min={today}
                required
              />
              {formData.departure_date && (
                <button 
                  type="button" 
                  className="date-clear" 
                  onClick={() => clearDate('departure_date')}
                  title="Clear"
                >
                  ×
                </button>
              )}
            </div>
          </div>
          
          <div className="form-field dates">
            <label>Return</label>
            <div style={{ position: 'relative' }}>
              <input 
                type="date" 
                name="return_date" 
                value={formData.return_date}
                onChange={handleChange}
                min={formData.departure_date || today}
              />
              {formData.return_date && (
                <button 
                  type="button" 
                  className="date-clear" 
                  onClick={() => clearDate('return_date')}
                  title="Clear"
                >
                  ×
                </button>
              )}
            </div>
          </div>
          
          <div className="form-field passengers">
            <label>Passengers</label>
            <div className="passenger-dropdown" onClick={togglePassengerMenu}>
              <div className="passenger-display">
                <div className="passenger-info">
                  <span className="passenger-count">
                    {formData.passengers} {formData.passengers === 1 ? 'passenger' : 'passengers'}
                  </span>
                  <span className="passenger-class">
                    {formData.class.charAt(0).toUpperCase() + formData.class.slice(1)}
                  </span>
                </div>
                <span className="dropdown-arrow">▼</span>
              </div>
            </div>
            <input type="hidden" name="passengers" value={formData.passengers} />
            <input type="hidden" name="class" value={formData.class} />
          </div>
        </form>
        
        <div className="search-button-container">
          <a 
            href="#" 
            className="multi-city-link" 
            onClick={(e) => {
              e.preventDefault()
              alert('Multi-city route feature coming soon!')
            }}
          >
            🔗 Create multi-city route
          </a>
          <button type="submit" form="flightSearchForm" className="search-button">
            Search flights
          </button>
        </div>
        
        <div className="booking-checkbox">
          <input type="checkbox" id="open_booking" name="open_booking" />
          <label htmlFor="open_booking">Open Booking.com in new tab</label>
        </div>
      </div>
    </div>
  )
}

export default FlightSearchPage
