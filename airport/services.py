"""
Flight search and comparison services
"""
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db.models import Q, Min, Max, Count
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import List, Dict, Optional, Tuple
from .models import Flight, Airport, Airline, FlightSeat
from bookings.services import PricingService, SeatReservationService


class FlightSearchService:
    """Service for searching and comparing flights across multiple airlines"""
    
    @classmethod
    def search_flights(
        cls,
        departure_airport_code: Optional[str] = None,
        arrival_airport_code: Optional[str] = None,
        departure_city: Optional[str] = None,
        arrival_city: Optional[str] = None,
        departure_date: Optional[date] = None,
        return_date: Optional[date] = None,
        passengers: int = 1,
        airline_id: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        max_duration_hours: Optional[float] = None,
        sort_by: str = "price",  # price, duration, departure_time
        order: str = "asc",  # asc, desc
    ) -> Dict:
        """
        Search flights with various filters and return sorted results
        
        Args:
            departure_airport_code: IATA code of departure airport (e.g., 'JFK')
            arrival_airport_code: IATA code of arrival airport (e.g., 'LHR')
            departure_city: City name for departure (alternative to airport code)
            arrival_city: City name for arrival (alternative to airport code)
            departure_date: Date of departure
            return_date: Date of return (for round trips)
            passengers: Number of passengers
            airline_id: Filter by specific airline
            min_price: Minimum price filter
            max_price: Maximum price filter
            max_duration_hours: Maximum flight duration in hours
            sort_by: Sort field (price, duration, departure_time)
            order: Sort order (asc, desc)
        
        Returns:
            Dictionary with search results and metadata
        """
        # Build base query
        queryset = Flight.objects.select_related(
            'airline', 'airplane', 'departure_airport', 'arrival_airport'
        ).prefetch_related('seats')
        
        # Filter by airports or cities
        if departure_airport_code:
            queryset = queryset.filter(departure_airport__code__iexact=departure_airport_code)
        elif departure_city:
            queryset = queryset.filter(departure_airport__city__icontains=departure_city)
        
        if arrival_airport_code:
            queryset = queryset.filter(arrival_airport__code__iexact=arrival_airport_code)
        elif arrival_city:
            queryset = queryset.filter(arrival_airport__city__icontains=arrival_city)
        
        # Filter by date
        if departure_date:
            queryset = queryset.filter(departure_date=departure_date)
        else:
            # Default to today and future flights
            queryset = queryset.filter(departure_date__gte=timezone.now().date())
        
        # Filter by airline
        if airline_id:
            queryset = queryset.filter(airline_id=airline_id)
        
        # Filter by status (only active flights)
        queryset = queryset.filter(
            status__in=[Flight.FlightStatus.SCHEDULED, Flight.FlightStatus.BOARDING, Flight.FlightStatus.DELAYED]
        )
        
        # Get flights and calculate prices
        flights = list(queryset)
        
        # Calculate prices and filter by price range
        flight_results = []
        for flight in flights:
            # Clean up expired reservations
            SeatReservationService._cleanup_expired_reservations(flight)
            
            # Get available seats count
            available_seats = flight.get_available_seat_count()
            
            # Check if enough seats available
            if available_seats < passengers:
                continue
            
            # Calculate minimum price (economy class)
            min_price_for_flight = flight.base_price
            
            # Calculate maximum price (first class)
            max_price_for_flight = flight.base_price * Decimal("4.00")
            
            # Filter by price range
            if min_price and max_price_for_flight < min_price:
                continue
            if max_price and min_price_for_flight > max_price:
                continue
            
            # Calculate duration
            duration = flight.duration
            duration_hours = duration.total_seconds() / 3600 if duration else None
            
            # Filter by duration
            if max_duration_hours and duration_hours and duration_hours > max_duration_hours:
                continue
            
            # Build result
            result = {
                'flight': flight,
                'min_price': min_price_for_flight,
                'max_price': max_price_for_flight,
                'duration_hours': duration_hours,
                'available_seats': available_seats,
                'airline_name': flight.airline.name,
                'airline_code': flight.airline.code,
            }
            flight_results.append(result)
        
        # Sort results
        reverse_order = (order.lower() == "desc")
        
        if sort_by == "price":
            flight_results.sort(key=lambda x: x['min_price'], reverse=reverse_order)
        elif sort_by == "duration":
            flight_results.sort(
                key=lambda x: x['duration_hours'] if x['duration_hours'] else float('inf'),
                reverse=reverse_order
            )
        elif sort_by == "departure_time":
            flight_results.sort(
                key=lambda x: x['flight'].departure_time,
                reverse=reverse_order
            )
        
        # Handle return flights if return_date is provided
        return_flights = []
        if return_date:
            return_results = cls.search_flights(
                departure_airport_code=arrival_airport_code,
                arrival_airport_code=departure_airport_code,
                departure_date=return_date,
                passengers=passengers,
                airline_id=airline_id,
                min_price=min_price,
                max_price=max_price,
                max_duration_hours=max_duration_hours,
                sort_by=sort_by,
                order=order,
            )
            return_flights = return_results.get('results', [])
        
        # Calculate price statistics
        if flight_results:
            prices = [r['min_price'] for r in flight_results]
            price_stats = {
                'min': min(prices),
                'max': max(prices),
                'average': sum(prices) / len(prices),
            }
        else:
            price_stats = None
        
        return {
            'results': flight_results,
            'return_results': return_flights,
            'total_count': len(flight_results),
            'price_stats': price_stats,
            'search_params': {
                'departure_airport_code': departure_airport_code,
                'arrival_airport_code': arrival_airport_code,
                'departure_city': departure_city,
                'arrival_city': arrival_city,
                'departure_date': departure_date.isoformat() if departure_date else None,
                'return_date': return_date.isoformat() if return_date else None,
                'passengers': passengers,
            }
        }
    
    @classmethod
    def get_cheapest_flights(
        cls,
        departure_airport_code: str,
        arrival_airport_code: str,
        departure_date: date,
        passengers: int = 1,
        limit: int = 10,
    ) -> List[Dict]:
        """Get the cheapest flights for a route"""
        results = cls.search_flights(
            departure_airport_code=departure_airport_code,
            arrival_airport_code=arrival_airport_code,
            departure_date=departure_date,
            passengers=passengers,
            sort_by="price",
            order="asc",
        )
        return results['results'][:limit]
    
    @classmethod
    def compare_airlines(
        cls,
        departure_airport_code: str,
        arrival_airport_code: str,
        departure_date: date,
    ) -> Dict:
        """Compare prices across different airlines for a route"""
        results = cls.search_flights(
            departure_airport_code=departure_airport_code,
            arrival_airport_code=arrival_airport_code,
            departure_date=departure_date,
            sort_by="price",
            order="asc",
        )
        
        # Group by airline
        airline_comparison = {}
        for result in results['results']:
            airline_code = result['airline_code']
            airline_name = result['airline_name']
            
            if airline_code not in airline_comparison:
                airline_comparison[airline_code] = {
                    'airline_code': airline_code,
                    'airline_name': airline_name,
                    'flights': [],
                    'cheapest_price': result['min_price'],
                    'count': 0,
                }
            
            airline_comparison[airline_code]['flights'].append(result)
            airline_comparison[airline_code]['count'] += 1
            if result['min_price'] < airline_comparison[airline_code]['cheapest_price']:
                airline_comparison[airline_code]['cheapest_price'] = result['min_price']
        
        return {
            'airlines': list(airline_comparison.values()),
            'total_airlines': len(airline_comparison),
            'cheapest_overall': results['price_stats']['min'] if results['price_stats'] else None,
        }

