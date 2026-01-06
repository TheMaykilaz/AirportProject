import { createContext, useContext, useState, useEffect } from 'react'

const LanguageContext = createContext(null)

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider')
  }
  return context
}

// Exchange rate: 1 USD = 42 UAH
const EXCHANGE_RATE = 42

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'uk'
  })

  useEffect(() => {
    localStorage.setItem('language', language)
  }, [language])

  const currency = language === 'uk' ? 'UAH' : 'USD'
  const currencySymbol = language === 'uk' ? '₴' : '$'

  // Convert price based on currency
  const convertPrice = (price, fromCurrency = 'USD') => {
    const numPrice = parseFloat(price) || 0
    
    if (fromCurrency === currency) {
      return numPrice
    }
    
    if (fromCurrency === 'USD' && currency === 'UAH') {
      return numPrice * EXCHANGE_RATE
    }
    
    if (fromCurrency === 'UAH' && currency === 'USD') {
      return numPrice / EXCHANGE_RATE
    }
    
    return numPrice
  }

  // Format price with currency symbol
  const formatPrice = (price, fromCurrency = 'USD') => {
    const converted = convertPrice(price, fromCurrency)
    return `${converted.toFixed(2)} ${currencySymbol === '₴' ? 'грн' : ''}`
  }

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'uk' ? 'en' : 'uk')
  }

  return (
    <LanguageContext.Provider value={{
      language,
      currency,
      currencySymbol,
      convertPrice,
      formatPrice,
      toggleLanguage,
      setLanguage
    }}>
      {children}
    </LanguageContext.Provider>
  )
}

