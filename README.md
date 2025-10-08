# Airport Project - Django REST API

A comprehensive flight booking system with Stripe payment integration, Google OAuth, and email verification.

## Features

- ✈️ Flight management (airports, airlines, airplanes, routes, flights)
- 🎫 Ticket booking with seat selection
- 💳 Stripe Checkout integration for payments
- 🔐 JWT authentication + Google OAuth
- 📧 Email verification
- 📚 Interactive API documentation (Swagger/ReDoc)
- 🐳 Docker containerization

## Quick Start with Docker

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### 1. Clone and setup
```bash
cd AirportProject
```

### 2. Configure environment (optional)
If you want to use Stripe or Google OAuth, copy `.env.docker` to `.env` and add your keys:
```bash
cp .env.docker .env
# Edit .env with your actual Stripe keys
```

### 3. Start the application
```bash
docker-compose up --build
```

This single command will:
- ✅ Build the Docker image
- ✅ Start PostgreSQL database
- ✅ Run database migrations
- ✅ Create a superuser (admin@airport.com / admin123)
- ✅ Start the Django server on http://localhost:8000

### 4. Access the application

- **API Documentation (Swagger)**: http://localhost:8000/swagger/
- **API Documentation (ReDoc)**: http://localhost:8000/redoc/
- **Admin Panel**: http://localhost:8000/admin/
  - Email: `admin@airport.com`
  - Password: `admin123`

## API Endpoints

### Authentication
- `POST /api/token/` - Get JWT access token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/users/register/` - Register new user
- `GET /api/users/me/` - Get current user profile

### Airport Management
- `GET /api/airport/countries/` - List countries
- `GET /api/airport/airports/` - List airports
- `GET /api/airport/airlines/` - List airlines
- `GET /api/airport/airplanes/` - List airplanes
- `GET /api/airport/flights/` - List flights

### Booking
- `POST /api/airport/test-order/create_order/` - Create order with tickets
- `GET /api/airport/orders/` - List user orders
- `GET /api/airport/tickets/` - List user tickets

### Payments
- `POST /api/payments/payments/create_checkout_session/` - Create Stripe Checkout session
- `POST /api/payments/webhook/` - Stripe webhook endpoint

## Testing the Full Flow

### 1. Get Authentication Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@airport.com", "password": "admin123"}'
```

### 2. Create Test Data via Swagger
1. Go to http://localhost:8000/swagger/
2. Click **Authorize** and enter: `Bearer YOUR_TOKEN`
3. Create in order:
   - Country → Airport → Airline → Airplane → Flight

### 3. Create Order and Book Tickets
```bash
curl -X POST http://localhost:8000/api/airport/test-order/create_order/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": 1,
    "seat_numbers": ["1A", "1B"]
  }'
```

### 4. Create Checkout Session
```bash
curl -X POST http://localhost:8000/api/payments/payments/create_checkout_session/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order": 1}'
```

### 5. Complete Payment
- Open the `checkout_url` from the response
- Use test card: `4242 4242 4242 4242`
- Any future expiry, any CVC

## Stripe Webhook Testing

### Option 1: Using Stripe CLI (Recommended)
```bash
# Install Stripe CLI
stripe login

# Forward webhooks to Docker container
stripe listen --forward-to http://localhost:8000/api/payments/webhook/

# Copy the webhook secret (whsec_...) and add to .env
# Restart: docker-compose restart web
```

### Option 2: Using ngrok
```bash
# Expose local server
ngrok http 8000

# Add the ngrok URL to Stripe Dashboard webhooks
# https://your-ngrok-url.ngrok.io/api/payments/webhook/
```

## Docker Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web

# Rebuild after code changes
docker-compose up --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser manually
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test
```

## Project Structure

```
AirportProject/
├── AirplaneDJ/          # Django project settings
├── airport/             # Main app (flights, bookings)
├── user/                # User authentication
├── stripe_payment/      # Payment integration
├── templates/           # HTML templates
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Multi-container setup
├── entrypoint.sh        # Startup script
├── requirements.txt     # Python dependencies
└── manage.py            # Django management
```

## Environment Variables

Key variables in `docker-compose.yml`:

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `DB_*` - Database credentials
- `STRIPE_*` - Stripe API keys
- `GOOGLE_*` - Google OAuth credentials
- `EMAIL_*` - Email configuration

## Troubleshooting

### Database connection issues
```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### View container logs
```bash
docker-compose logs -f web
docker-compose logs -f db
```

### Reset database
```bash
docker-compose down -v  # Remove volumes
docker-compose up --build
```

## Production Deployment

For production:
1. Change `SECRET_KEY` to a secure random value
2. Set `DEBUG=False`
3. Update `ALLOWED_HOSTS` in settings.py
4. Use strong database passwords
5. Configure proper email backend
6. Set up SSL/TLS certificates
7. Use environment-specific `.env` file

## License

This project is for educational purposes.
