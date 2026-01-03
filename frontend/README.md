# Airport Project - React Frontend

Modern React frontend for the Airport Project built with Vite, Material-UI, and React Router.

## Features

- 🚀 **Fast Development** - Powered by Vite for instant HMR
- 🎨 **Modern UI** - Material-UI components with beautiful design
- 🔐 **Authentication** - JWT-based authentication with token refresh
- ✈️ **Flight Search** - Advanced flight search with filters
- 📱 **Responsive** - Mobile-friendly design
- 🛒 **Booking System** - Complete booking flow with seat selection
- 💳 **Payment Integration** - Stripe checkout integration

## Prerequisites

- Node.js 18+ and npm/yarn
- Django backend running on `http://localhost:8000`

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

The Vite dev server is configured to proxy API requests to `http://localhost:8000/api`

## Building for Production

Build the React app for production:

```bash
npm run build
```

This will create optimized production files in `../staticfiles/react/`

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   │   └── Layout.jsx   # Main layout with navigation
│   ├── contexts/        # React contexts
│   │   └── AuthContext.jsx  # Authentication context
│   ├── pages/          # Page components
│   │   ├── HomePage.jsx
│   │   ├── FlightSearchPage.jsx
│   │   ├── FlightResultsPage.jsx
│   │   ├── BookingPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   └── DashboardPage.jsx
│   ├── services/       # API services
│   │   └── api.js      # Axios instance and API functions
│   ├── App.jsx         # Main app component with routes
│   └── main.jsx        # Entry point
├── index.html          # HTML template
├── package.json        # Dependencies
└── vite.config.js     # Vite configuration
```

## API Integration

The frontend communicates with the Django REST API. All API calls are handled through the `api.js` service file which includes:

- Automatic token injection
- Token refresh on 401 errors
- Centralized error handling

## Environment Variables

Create a `.env` file in the frontend directory (optional):

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## Features Overview

### Flight Search
- Search by airport code or city
- Round trip support
- Advanced filters (price, duration, airline)
- Real-time results

### Booking Flow
1. Search flights
2. View results with price comparison
3. Select flight and seats
4. Complete booking
5. Redirect to Stripe payment

### Authentication
- Email/password login
- User registration
- JWT token management
- Protected routes

### Dashboard
- View booking history
- User profile information
- Account management

## Troubleshooting

### CORS Errors
Make sure `django-cors-headers` is installed and configured in Django settings.

### API Connection Issues
- Verify Django server is running on port 8000
- Check CORS settings in `AirplaneDJ/settings.py`
- Ensure API endpoints match in `frontend/src/services/api.js`

### Build Issues
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## Production Deployment

1. Build the React app: `npm run build`
2. Collect Django static files: `python manage.py collectstatic`
3. The React build will be served from `staticfiles/react/`
4. Django will serve the React app for all non-API routes

## License

Same as the main project.

