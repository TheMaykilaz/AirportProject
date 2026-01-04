# Hotels API Documentation

This document describes the Hotels API endpoints for booking hotels/apartments near airports, similar to booking.com functionality.

## Base URL
All endpoints are prefixed with `/api/hotels/`

## Endpoints

### 1. List/Search Hotels

**GET** `/api/hotels/hotels/`

List all active hotels with optional filters.

**Query Parameters:**
- `airport_code` (optional): Filter by airport IATA code (e.g., "JFK")
- `city` (optional): Filter by city name
- `country` (optional): Filter by country name
- `max_distance_km` (optional): Maximum distance from airport in kilometers
- `min_star_rating` (optional): Minimum star rating (1-5)
- `amenities` (optional): Filter by amenities (can be repeated, e.g., `?amenities=wifi&amenities=pool`)

**Example:**
```
GET /api/hotels/hotels/?airport_code=JFK&max_distance_km=10&min_star_rating=4
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Airport Hotel",
    "description": "Comfortable hotel near airport",
    "address": "123 Airport Road",
    "city": "New York",
    "country": "USA",
    "nearest_airport_code": "JFK",
    "nearest_airport_name": "John F. Kennedy International Airport",
    "distance_from_airport_km": "5.00",
    "star_rating": 4,
    "amenities": ["wifi", "pool", "gym", "parking"],
    "room_count": 10,
    "min_price_per_night": "99.99"
  }
]
```

### 2. Advanced Hotel Search

**POST** `/api/hotels/hotels/search/`

Advanced search with availability checking.

**Request Body:**
```json
{
  "airport_code": "JFK",
  "city": "New York",
  "max_distance_km": 10,
  "min_star_rating": 4,
  "check_in_date": "2025-12-31",
  "check_out_date": "2026-01-02",
  "number_of_guests": 2,
  "amenities": ["wifi", "pool"]
}
```

**Response:** Same as list hotels endpoint

### 3. Get Hotel Details

**GET** `/api/hotels/hotels/{id}/`

Get detailed information about a specific hotel.

### 4. Get Available Rooms

**GET** `/api/hotels/hotels/{id}/rooms/`

Get available rooms for a hotel.

**Query Parameters:**
- `check_in_date` (optional): Check-in date (YYYY-MM-DD)
- `check_out_date` (optional): Check-out date (YYYY-MM-DD)
- `number_of_guests` (optional): Number of guests

**Example:**
```
GET /api/hotels/hotels/1/rooms/?check_in_date=2025-12-31&check_out_date=2026-01-02&number_of_guests=2
```

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 1,
    "hotel_name": "Airport Hotel",
    "room_type": {
      "id": 1,
      "name": "Double Room",
      "max_occupancy": 2,
      "bed_type": "1 King Bed"
    },
    "room_number": "101",
    "base_price_per_night": "99.99",
    "is_available": true,
    "floor": 1,
    "view_type": "city"
  }
]
```

### 5. Create Hotel Booking

**POST** `/api/hotels/bookings/create_booking/`

Create a new hotel booking. Requires authentication.

**Request Body:**
```json
{
  "hotel_id": 1,
  "room_id": 1,
  "check_in_date": "2025-12-31",
  "check_out_date": "2026-01-02",
  "number_of_guests": 2,
  "guest_name": "John Doe",
  "guest_email": "john@example.com",
  "guest_phone": "+1234567890",
  "special_requests": "Late check-in please"
}
```

**Response:**
```json
{
  "id": 1,
  "hotel_name": "Airport Hotel",
  "room_type_name": "Double Room",
  "room_number": "101",
  "check_in_date": "2025-12-31",
  "check_out_date": "2026-01-02",
  "number_of_nights": 2,
  "number_of_guests": 2,
  "price_per_night": "99.99",
  "total_price": "199.98",
  "status": "pending"
}
```

### 6. List User Bookings

**GET** `/api/hotels/bookings/`

Get all bookings for the authenticated user.

### 7. Get Booking Details

**GET** `/api/hotels/bookings/{id}/`

Get details of a specific booking.

### 8. Cancel Booking

**POST** `/api/hotels/bookings/{id}/cancel/`

Cancel a booking.

**Request Body:**
```json
{
  "reason": "Change of plans"
}
```

### 9. Confirm Booking

**POST** `/api/hotels/bookings/{id}/confirm/`

Confirm a booking (typically after payment). Requires admin or booking owner.

### 10. Room Types

**GET** `/api/hotels/room-types/`

List all available room types.

## Integration with Payment

After creating a hotel booking, you can integrate it with Stripe payment similar to flight bookings:

1. Create hotel booking: `POST /api/hotels/bookings/create_booking/`
2. Create payment session: `POST /api/payments/create_checkout_session/` with `order_id` (you may need to adapt the payment system to support hotel bookings)
3. After successful payment, confirm booking: `POST /api/hotels/bookings/{id}/confirm/`

## Authentication

Most endpoints require authentication. Include JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Example Workflow

1. **Search for hotels near airport:**
   ```
   GET /api/hotels/hotels/?airport_code=JFK&max_distance_km=10
   ```

2. **Check available rooms:**
   ```
   GET /api/hotels/hotels/1/rooms/?check_in_date=2025-12-31&check_out_date=2026-01-02&number_of_guests=2
   ```

3. **Create booking:**
   ```
   POST /api/hotels/bookings/create_booking/
   {
     "hotel_id": 1,
     "room_id": 1,
     "check_in_date": "2025-12-31",
     "check_out_date": "2026-01-02",
     "number_of_guests": 2,
     "guest_name": "John Doe",
     "guest_email": "john@example.com"
   }
   ```

4. **Process payment and confirm booking** (integration with existing payment system)

