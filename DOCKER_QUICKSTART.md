# 🐳 Docker Quick Start Guide

## One-Command Setup

```bash
docker-compose up --build
```

That's it! The application will be ready at **http://localhost:8000**

## What Happens Automatically

✅ PostgreSQL database starts  
✅ Database migrations run  
✅ Superuser created: `admin@airport.com` / `admin123`  
✅ Django server starts on port 8000  

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Swagger API Docs** | http://localhost:8000/swagger/ | - |
| **ReDoc API Docs** | http://localhost:8000/redoc/ | - |
| **Admin Panel** | http://localhost:8000/admin/ | admin@airport.com / admin123 |

## Quick Test Flow

### 1. Get Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@airport.com", "password": "admin123"}'
```

Copy the `access` token from response.

### 2. Test API (via Swagger)
1. Open http://localhost:8000/swagger/
2. Click **Authorize** button (top right)
3. Enter: `Bearer YOUR_ACCESS_TOKEN`
4. Click **Authorize** then **Close**

### 3. Create Test Data
Create in this order via Swagger:

1. **Country** (`POST /api/airport/countries/`)
   ```json
   {"name": "USA", "slug": "usa"}
   ```

2. **Airport** (`POST /api/airport/airports/`)
   ```json
   {"name": "JFK Airport", "code": "JFK", "country_id": 1}
   ```

3. **Airline** (`POST /api/airport/airlines/`)
   ```json
   {"name": "Test Airlines", "airport_ids": [1]}
   ```

4. **Airplane** (`POST /api/airport/airplanes/`)
   ```json
   {
     "manufacturer": "Boeing",
     "model": "737",
     "airline_id": 1,
     "capacity": 6,
     "seat_map": [
       {"seat_number": "1A", "seat_class": "first"},
       {"seat_number": "1B", "seat_class": "first"},
       {"seat_number": "2A", "seat_class": "business"},
       {"seat_number": "2B", "seat_class": "business"},
       {"seat_number": "3A", "seat_class": "economy"},
       {"seat_number": "3B", "seat_class": "economy"}
     ]
   }
   ```

5. **Flight** (`POST /api/airport/flights/`)
   ```json
   {
     "airline_id": 1,
     "flight_number": "TA100",
     "airplane_id": 1,
     "departure_airport_id": 1,
     "arrival_airport_id": 1,
     "departure_time": "2025-12-01T10:00:00Z",
     "arrival_time": "2025-12-01T14:00:00Z",
     "base_price": "100.00"
   }
   ```

### 4. Book Tickets
```bash
curl -X POST http://localhost:8000/api/airport/test-order/create_order/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": 1,
    "seat_numbers": ["1A", "1B"]
  }'
```

### 5. Create Payment Checkout
```bash
curl -X POST http://localhost:8000/api/payments/payments/create_checkout_session/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order": 1}'
```

Open the `checkout_url` from response and use test card: **4242 4242 4242 4242**

## Stripe Webhook Setup

### Option 1: Stripe CLI (Best for testing)
```bash
# Install and login
stripe login

# Forward webhooks
stripe listen --forward-to http://localhost:8000/api/payments/webhook/

# Copy the webhook secret (whsec_...)
# Add to docker-compose.yml under STRIPE_WEBHOOK_SECRET
# Restart: docker-compose restart web
```

### Option 2: Update .env
```bash
# Edit docker-compose.yml or create .env file
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret

# Restart
docker-compose restart web
```

## Useful Commands

```bash
# Start in background
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f web

# Restart after .env changes
docker-compose restart web

# Access Django shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Create another superuser
docker-compose exec web python manage.py createsuperuser

# Reset everything (⚠️ deletes data)
docker-compose down -v
docker-compose up --build
```

## Troubleshooting

### Port 8000 already in use
Edit `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change to 8001
```

### Database connection error
```bash
# Wait for database to be ready
docker-compose logs db

# Restart services
docker-compose restart
```

### See what's happening
```bash
# Web server logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db
```

### Fresh start
```bash
docker-compose down -v  # Remove all data
docker-compose up --build  # Rebuild and start
```

## Next Steps

- Read full documentation in `README.md`
- Explore API at http://localhost:8000/swagger/
- Check webhook logs in terminal when completing payments
- Add your Stripe keys for real payment testing

## Need Help?

Check the terminal output - the entrypoint script shows:
- ✅ Database connection status
- ✅ Migration results
- ✅ Superuser creation
- ✅ Server startup

All logs are visible with `docker-compose logs -f web`
