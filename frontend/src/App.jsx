import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import FlightSearchPage from './pages/FlightSearchPage'
import FlightResultsPage from './pages/FlightResultsPage'
import BookingPage from './pages/BookingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import { AuthProvider } from './contexts/AuthContext'
import { LanguageProvider } from './contexts/LanguageContext'

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<FlightSearchPage />} />
            <Route path="/results" element={<FlightResultsPage />} />
            <Route path="/booking/:flightId" element={<BookingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </LanguageProvider>
  )
}

export default App

