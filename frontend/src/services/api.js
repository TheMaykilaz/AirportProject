import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/users/auth/token/refresh/`, {
            refresh: refreshToken,
          })
          const { access } = response.data
          localStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (email, password) =>
    api.post('/users/auth/token/', { email, password }),
  
  register: (data) =>
    api.post('/users/auth/register/', data),
  
  refreshToken: (refresh) =>
    api.post('/users/auth/token/refresh/', { refresh }),
  
  getCurrentUser: () =>
    api.get('/users/users/me/'),
  
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },
}

// Flight API
export const flightAPI = {
  search: (params) =>
    api.get('/airport/flights/search/', { params }),
  
  getCheapest: (params) =>
    api.get('/airport/flights/cheapest/', { params }),
  
  compareAirlines: (params) =>
    api.get('/airport/flights/compare_airlines/', { params }),
  
  getSeatMap: (flightId) =>
    api.get(`/airport/flights/${flightId}/seat_map/`),
  
  getFlight: (flightId) =>
    api.get(`/airport/flights/${flightId}/`),
}

// Booking API
export const bookingAPI = {
  createBooking: (data) =>
    api.post('/bookings/orders/create_with_tickets/', data),
  
  getBookings: () =>
    api.get('/bookings/orders/'),
  
  getBooking: (orderId) =>
    api.get(`/bookings/orders/${orderId}/`),
}

// Payment API
export const paymentAPI = {
  createCheckoutSession: (orderId) =>
    api.post('/payments/payments/create_checkout_session/', { order: orderId }),
}

// Airport/Airline API
export const airportAPI = {
  getAirports: () =>
    api.get('/airport/airports/'),
  
  getAirlines: () =>
    api.get('/airport/airlines/'),
}

export const aiChatAPI = {
  send: (message, conversation_history = []) =>
    api.post('/ai-chat/api/chat/', { message, conversation_history }),
}

// Hotels API
export const hotelsAPI = {
  // Simple list/search with query params
  list: (params) => api.get('/hotels/hotels/', { params }),
  // Advanced search with availability check (POST)
  search: (data) => api.post('/hotels/hotels/search/', data),
  // Get rooms for a particular hotel
  rooms: (hotelId, params) => api.get(`/hotels/hotels/${hotelId}/rooms/`, { params }),
  // Get single hotel
  get: (hotelId) => api.get(`/hotels/hotels/${hotelId}/`),
}

// Stripe Hotel payment
export const stripeHotelAPI = {
  checkout: (payload) => api.post('/payments/hotel-checkout/', payload),
}

// User API
export const userAPI = {
  update: (userId, data) => api.patch(`/users/users/${userId}/`, data),
}

export default api

