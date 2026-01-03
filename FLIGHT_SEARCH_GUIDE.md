# Flight Search System - Aviasales-like Functionality

This document describes the flight search and booking system similar to aviasales.com that has been implemented.

## Features

### 1. Flight Search
- **Multi-airline search**: Search flights across all airlines in the system
- **Price comparison**: Automatically compares prices and shows cheapest options first
- **Flexible search options**:
  - Search by airport code (e.g., JFK, LHR) or city name
  - Filter by date, number of passengers
  - Filter by price range, duration, airline
  - Sort by price, duration, or departure time
  - Round trip support

### 2. Price Comparison
- Shows minimum and maximum prices for each flight
- Displays price statistics (cheapest, most expensive, average)
- Compares prices across different airlines
- Shows available seats count

### 3. Booking Integration
- Seamless integration with existing booking system
- Automatic seat selection (or manual selection via seat map)
- Integration with Stripe payment system
- Real-time seat availability checking

## API Endpoints

### Search Flights
```
GET /api/airport/flights/search/
```

**Query Parameters:**
- `departure_airport_code` (optional): IATA code (e.g., "JFK")
- `arrival_airport_code` (optional): IATA code (e.g., "LHR")
- `departure_city` (optional): City name (alternative to airport code)
- `arrival_city` (optional): City name (alternative to airport code)
- `departure_date` (optional): Date in YYYY-MM-DD format
- `return_date` (optional): Return date for round trip
- `passengers` (optional, default: 1): Number of passengers
- `airline_id` (optional): Filter by specific airline
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter
- `max_duration_hours` (optional): Maximum flight duration
- `sort_by` (optional, default: "price"): Sort field (price, duration, departure_time)
- `order` (optional, default: "asc"): Sort order (asc, desc)

**Example:**
```
GET /api/airport/flights/search/?departure_airport_code=JFK&arrival_airport_code=LHR&departure_date=2024-12-25&passengers=2&sort_by=price&order=asc
```

### Get Cheapest Flights
```
GET /api/airport/flights/cheapest/
```

**Query Parameters:**
- `departure_airport_code` (required)
- `arrival_airport_code` (required)
- `departure_date` (required): Date in YYYY-MM-DD format
- `passengers` (optional, default: 1)
- `limit` (optional, default: 10): Maximum number of results

**Example:**
```
GET /api/airport/flights/cheapest/?departure_airport_code=JFK&arrival_airport_code=LHR&departure_date=2024-12-25&limit=5
```

### Compare Airlines
```
GET /api/airport/flights/compare_airlines/
```

**Query Parameters:**
- `departure_airport_code` (required)
- `arrival_airport_code` (required)
- `departure_date` (required): Date in YYYY-MM-DD format

**Example:**
```
GET /api/airport/flights/compare_airlines/?departure_airport_code=JFK&arrival_airport_code=LHR&departure_date=2024-12-25
```

## Frontend Interface

### Access the Search Page
Navigate to: `/api/airport/search/`

The search page provides:
- User-friendly flight search form
- Real-time flight results with price comparison
- Visual flight cards showing:
  - Airline information
  - Departure and arrival times
  - Flight duration
  - Price (cheapest available)
  - Available seats
- One-click booking integration
- Round trip support
- Price statistics display

## Booking Flow

1. **Search Flights**: User searches for flights using the search interface
2. **Select Flight**: User clicks "Book Now" on a flight
3. **Create Booking**: System creates an order and reserves seats
4. **Payment**: User is redirected to Stripe Checkout
5. **Confirmation**: After successful payment, booking is confirmed

## Integration with Existing Systems

### Booking System
- Uses existing `BookingService` for creating orders
- Integrates with `SeatReservationService` for seat management
- Uses `PricingService` for price calculations

### Payment System
- Integrates with existing Stripe payment endpoints
- Uses `PaymentViewSet.create_checkout_session` for payment processing
- Automatically confirms booking after successful payment

## Service Architecture

### FlightSearchService
Located in `airport/services.py`, provides:
- `search_flights()`: Main search function with all filters
- `get_cheapest_flights()`: Get cheapest flights for a route
- `compare_airlines()`: Compare prices across airlines

### Key Features:
- Automatic seat availability checking
- Price calculation based on seat class
- Expired reservation cleanup
- Efficient database queries with select_related and prefetch_related

## Example Usage

### Python/Django Shell
```python
from airport.services import FlightSearchService
from datetime import date

# Search for flights
results = FlightSearchService.search_flights(
    departure_airport_code="JFK",
    arrival_airport_code="LHR",
    departure_date=date(2024, 12, 25),
    passengers=2,
    sort_by="price",
    order="asc"
)

# Get cheapest flights
cheapest = FlightSearchService.get_cheapest_flights(
    departure_airport_code="JFK",
    arrival_airport_code="LHR",
    departure_date=date(2024, 12, 25),
    limit=5
)

# Compare airlines
comparison = FlightSearchService.compare_airlines(
    departure_airport_code="JFK",
    arrival_airport_code="LHR",
    departure_date=date(2024, 12, 25)
)
```

### JavaScript/Frontend
```javascript
// Search flights
const response = await fetch('/api/airport/flights/search/?departure_airport_code=JFK&arrival_airport_code=LHR&departure_date=2024-12-25&passengers=2&sort_by=price');
const data = await response.json();

// Display results
data.results.forEach(flight => {
    console.log(`${flight.airline_name}: $${flight.min_price}`);
});
```

## Response Format

### Search Results
```json
{
    "results": [
        {
            "flight_id": 1,
            "flight_number": "AA100",
            "airline_name": "American Airlines",
            "airline_code": "AA",
            "departure_airport_code": "JFK",
            "departure_airport_name": "John F. Kennedy International Airport",
            "departure_city": "New York",
            "arrival_airport_code": "LHR",
            "arrival_airport_name": "London Heathrow Airport",
            "arrival_city": "London",
            "departure_time": "2024-12-25T10:00:00Z",
            "arrival_time": "2024-12-25T22:00:00Z",
            "duration_hours": 7.5,
            "duration_formatted": "7:30:00",
            "min_price": "299.99",
            "max_price": "1199.96",
            "base_price": "299.99",
            "available_seats": 45,
            "status": "scheduled",
            "airplane_model": "Boeing 777"
        }
    ],
    "return_results": [...],  // If round trip
    "total_count": 10,
    "price_stats": {
        "min": "299.99",
        "max": "1199.96",
        "average": "649.98"
    },
    "search_params": {
        "departure_airport_code": "JFK",
        "arrival_airport_code": "LHR",
        "departure_date": "2024-12-25",
        "passengers": 2
    }
}
```

## Notes

- All prices are in USD
- Flight search automatically filters out cancelled and departed flights
- Seat availability is checked in real-time
- Expired reservations (older than 30 minutes) are automatically cleaned up
- The system supports multiple seat classes with different pricing multipliers:
  - Economy: 1.0x base price
  - Premium Economy: 1.5x base price
  - Business: 2.5x base price
  - First Class: 4.0x base price

## Future Enhancements

Potential improvements:
- Multi-city trips
- Flexible date search (show prices for +/-3 days)
- Price alerts
- Save search preferences
- Advanced filters (stops, aircraft type, etc.)
- Mobile app API support

