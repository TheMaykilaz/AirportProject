# React + Django Integration Guide

This guide explains how to set up and run the React frontend with the Django backend.

## Quick Start

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Install Django CORS Package

```bash
# In the project root
pip install django-cors-headers
```

The package is already added to `requirements.txt`, so you can also run:

```bash
pip install -r requirements.txt
```

### 3. Run Django Backend

```bash
# In the project root
python manage.py runserver
```

Django will run on `http://localhost:8000`

### 4. Run React Frontend

```bash
# In the frontend directory
cd frontend
npm run dev
```

React will run on `http://localhost:5173`

## Development Workflow

### Option 1: Separate Servers (Recommended for Development)

- Django: `http://localhost:8000` (API)
- React: `http://localhost:5173` (Frontend)

The React dev server proxies API requests to Django automatically.

### Option 2: Django Serves React (Production-like)

1. Build React: `cd frontend && npm run build`
2. Collect static files: `python manage.py collectstatic`
3. Access React app through Django: `http://localhost:8000`

## API Endpoints

The React app uses these Django API endpoints:

- **Authentication**: `/api/users/auth/`
- **Flights**: `/api/airport/flights/`
- **Bookings**: `/api/bookings/`
- **Payments**: `/api/payments/`

## CORS Configuration

CORS is configured in `AirplaneDJ/settings.py` to allow:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative React dev server)

## Building for Production

1. **Build React app**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Collect static files**:
   ```bash
   python manage.py collectstatic
   ```

3. **Deploy**: The React build is in `staticfiles/react/` and Django will serve it automatically.

## Troubleshooting

### CORS Errors
- Ensure `django-cors-headers` is in `INSTALLED_APPS`
- Check `CORS_ALLOWED_ORIGINS` in settings.py
- Verify `CorsMiddleware` is in `MIDDLEWARE`

### API Connection Issues
- Verify Django is running on port 8000
- Check browser console for errors
- Verify API endpoints in `frontend/src/services/api.js`

### Build Errors
- Clear `node_modules`: `rm -rf node_modules && npm install`
- Check Node.js version (18+ required)
- Verify all dependencies in `package.json`

## Features

✅ Modern React UI with Material-UI
✅ Flight search and booking
✅ User authentication
✅ Responsive design
✅ API integration with Django REST Framework
✅ Token-based authentication with auto-refresh

## Next Steps

1. Customize the UI theme in `frontend/src/main.jsx`
2. Add more features to the React app
3. Configure environment variables for different environments
4. Set up CI/CD for automated deployments

