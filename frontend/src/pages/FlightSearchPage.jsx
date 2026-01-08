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
  const [errors, setErrors] = useState({ departure_city: '', arrival_city: '' })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'passengers' ? parseInt(value) || 1 : value,
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // basic inline validation
    const nextErrors = { departure_city: '', arrival_city: '' }
    if (!formData.departure_city.trim()) nextErrors.departure_city = 'Вкажіть місто відправлення'
    if (!formData.arrival_city.trim()) nextErrors.arrival_city = 'Вкажіть місто прибуття'
    if (!nextErrors.departure_city && !nextErrors.arrival_city && formData.departure_city.trim().toLowerCase() === formData.arrival_city.trim().toLowerCase()) {
      nextErrors.arrival_city = 'Міста відправлення і прибуття не можуть співпадати'
    }
    setErrors(nextErrors)
    if (nextErrors.departure_city || nextErrors.arrival_city) return
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
      <h1 className="search-title">Пошук дешевих авіаквитків</h1>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'flights' ? 'active' : ''}`}
          onClick={() => setActiveTab('flights')}
        >
          <span className="tab-icon">✈️</span>
          <span>Рейси</span>
        </button>
        <button 
          className={`tab ${activeTab === 'hotels' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('hotels')
            navigate('/hotels')
          }}
        >
          <span className="tab-icon">🏨</span>
          <span>Готелі</span>
        </button>
        <button 
          className={`tab ${activeTab === 'favorites' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('favorites')
            navigate('/favorites')
          }}
        >
          <span className="tab-icon">❤️</span>
          <span>Обране</span>
        </button>
      </div>

      <div className="search-form-container">
        <form id="flightSearchForm" className="search-form" onSubmit={handleSubmit}>
          <div className="form-field departure">
            <label>Звідки</label>
            <input 
              type="text" 
              name="departure_city" 
              placeholder="Місто або аеропорт" 
              value={formData.departure_city}
              onChange={handleChange}
              autoComplete="off"
            />
            <div className="airport-code" id="departure_code"></div>
            {errors.departure_city && (
              <div style={{ color: '#ff6b6b', fontSize: 12, marginTop: 4 }}>{errors.departure_city}</div>
            )}
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
            <label>Куди</label>
            <input 
              type="text" 
              name="arrival_city" 
              placeholder="Місто або аеропорт" 
              value={formData.arrival_city}
              onChange={handleChange}
              autoComplete="off"
            />
            <div className="airport-code" id="arrival_code"></div>
            {errors.arrival_city && (
              <div style={{ color: '#ff6b6b', fontSize: 12, marginTop: 4 }}>{errors.arrival_city}</div>
            )}
          </div>
          
          <div className="form-field dates">
            <label>Виліт</label>
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
            <label>Повернення</label>
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
            <label>Пасажири</label>
            <div className="passenger-dropdown" onClick={togglePassengerMenu}>
              <div className="passenger-display">
                <div className="passenger-info">
                  <span className="passenger-count">
                    {formData.passengers} {formData.passengers === 1 ? 'пасажир' : 'пасажири'}
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
          <button type="submit" form="flightSearchForm" className="search-button">
            Search flights
          </button>
        </div>
      </div>
    </div>
  )
}

export default FlightSearchPage
