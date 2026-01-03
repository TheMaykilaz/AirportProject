
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404, render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import date
from decimal import Decimal
from user.models import User
from .models import (
    Country,
    Airport,
    Airline,
    Airplane,
    Flight,
    FlightSeat
)
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializer,
    FlightSeatSerializer,
    FlightSearchResultSerializer,
    FlightSearchResponseSerializer
)
from .services import FlightSearchService
from drf_spectacular.utils import extend_schema, OpenApiExample
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def airlines(self, request, pk=None):
        airport = self.get_object()
        airlines = airport.airlines.all()
        serializer = AirlineSerializer(airlines, many=True)
        return Response(serializer.data)


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def airplanes(self, request, pk=None):
        airline = self.get_object()
        airplanes = airline.airplanes.all()
        serializer = AirplaneSerializer(airplanes, many=True)
        return Response(serializer.data)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def flights(self, request, pk=None):
        airplane = self.get_object()
        flights = airplane.flights.all()
        serializer = FlightSerializer(flights, many=True)
        return Response(serializer.data)

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]
    
    @extend_schema(
        summary="Search flights",
        description="Search for flights with various filters. Similar to aviasales.com functionality.",
        parameters=[
            {
                "name": "departure_airport_code",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "IATA code of departure airport (e.g., JFK, LHR)"
            },
            {
                "name": "arrival_airport_code",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "IATA code of arrival airport (e.g., JFK, LHR)"
            },
            {
                "name": "departure_city",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "City name for departure (alternative to airport code)"
            },
            {
                "name": "arrival_city",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "City name for arrival (alternative to airport code)"
            },
            {
                "name": "departure_date",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "format": "date"},
                "description": "Departure date (YYYY-MM-DD)"
            },
            {
                "name": "return_date",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "format": "date"},
                "description": "Return date for round trip (YYYY-MM-DD)"
            },
            {
                "name": "passengers",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "default": 1},
                "description": "Number of passengers"
            },
            {
                "name": "airline_id",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
                "description": "Filter by specific airline ID"
            },
            {
                "name": "min_price",
                "in": "query",
                "required": False,
                "schema": {"type": "number"},
                "description": "Minimum price filter"
            },
            {
                "name": "max_price",
                "in": "query",
                "required": False,
                "schema": {"type": "number"},
                "description": "Maximum price filter"
            },
            {
                "name": "max_duration_hours",
                "in": "query",
                "required": False,
                "schema": {"type": "number"},
                "description": "Maximum flight duration in hours"
            },
            {
                "name": "sort_by",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "enum": ["price", "duration", "departure_time"], "default": "price"},
                "description": "Sort field"
            },
            {
                "name": "order",
                "in": "query",
                "required": False,
                "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                "description": "Sort order"
            },
        ],
        responses={200: FlightSearchResponseSerializer}
    )
    @action(detail=False, methods=["get"], permission_classes=[ReadOnly])
    def search(self, request):
        """Search flights with filters - find cheapest tickets from different airlines"""
        # Parse query parameters
        departure_airport_code = request.query_params.get("departure_airport_code")
        arrival_airport_code = request.query_params.get("arrival_airport_code")
        departure_city = request.query_params.get("departure_city")
        arrival_city = request.query_params.get("arrival_city")
        departure_date_str = request.query_params.get("departure_date")
        return_date_str = request.query_params.get("return_date")
        passengers = int(request.query_params.get("passengers", 1))
        airline_id = request.query_params.get("airline_id")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        max_duration_hours = request.query_params.get("max_duration_hours")
        sort_by = request.query_params.get("sort_by", "price")
        order = request.query_params.get("order", "asc")
        
        # Parse dates
        departure_date = None
        if departure_date_str:
            try:
                departure_date = date.fromisoformat(departure_date_str)
            except ValueError:
                return Response(
                    {"error": "Invalid departure_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return_date = None
        if return_date_str:
            try:
                return_date = date.fromisoformat(return_date_str)
            except ValueError:
                return Response(
                    {"error": "Invalid return_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Parse prices
        min_price_decimal = None
        if min_price:
            try:
                min_price_decimal = Decimal(str(min_price))
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid min_price"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        max_price_decimal = None
        if max_price:
            try:
                max_price_decimal = Decimal(str(max_price))
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid max_price"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Parse duration
        max_duration = None
        if max_duration_hours:
            try:
                max_duration = float(max_duration_hours)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid max_duration_hours"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Parse airline_id
        airline_id_int = None
        if airline_id:
            try:
                airline_id_int = int(airline_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid airline_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate required parameters
        if not departure_airport_code and not departure_city:
            return Response(
                {"error": "Either departure_airport_code or departure_city is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not arrival_airport_code and not arrival_city:
            return Response(
                {"error": "Either arrival_airport_code or arrival_city is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform search
        try:
            search_results = FlightSearchService.search_flights(
                departure_airport_code=departure_airport_code,
                arrival_airport_code=arrival_airport_code,
                departure_city=departure_city,
                arrival_city=arrival_city,
                departure_date=departure_date,
                return_date=return_date,
                passengers=passengers,
                airline_id=airline_id_int,
                min_price=min_price_decimal,
                max_price=max_price_decimal,
                max_duration_hours=max_duration,
                sort_by=sort_by,
                order=order,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Serialize results
        serialized_results = []
        for result in search_results['results']:
            flight = result['flight']
            duration = flight.duration
            duration_formatted = str(duration).split('.')[0] if duration else "N/A"
            
            serialized_results.append({
                'flight_id': flight.id,
                'flight_number': flight.flight_number,
                'airline_name': result['airline_name'],
                'airline_code': result['airline_code'],
                'departure_airport_code': flight.departure_airport.code,
                'departure_airport_name': flight.departure_airport.name,
                'departure_city': flight.departure_airport.city,
                'arrival_airport_code': flight.arrival_airport.code,
                'arrival_airport_name': flight.arrival_airport.name,
                'arrival_city': flight.arrival_airport.city,
                'departure_time': flight.departure_time,
                'arrival_time': flight.arrival_time,
                'duration_hours': result['duration_hours'],
                'duration_formatted': duration_formatted,
                'min_price': result['min_price'],
                'max_price': result['max_price'],
                'base_price': flight.base_price,
                'available_seats': result['available_seats'],
                'status': flight.status,
                'airplane_model': flight.airplane.model,
            })
        
        # Serialize return results if any
        serialized_return_results = []
        if search_results.get('return_results'):
            for result in search_results['return_results']:
                flight = result['flight']
                duration = flight.duration
                duration_formatted = str(duration).split('.')[0] if duration else "N/A"
                
                serialized_return_results.append({
                    'flight_id': flight.id,
                    'flight_number': flight.flight_number,
                    'airline_name': result['airline_name'],
                    'airline_code': result['airline_code'],
                    'departure_airport_code': flight.departure_airport.code,
                    'departure_airport_name': flight.departure_airport.name,
                    'departure_city': flight.departure_airport.city,
                    'arrival_airport_code': flight.arrival_airport.code,
                    'arrival_airport_name': flight.arrival_airport.name,
                    'arrival_city': flight.arrival_airport.city,
                    'departure_time': flight.departure_time,
                    'arrival_time': flight.arrival_time,
                    'duration_hours': result['duration_hours'],
                    'duration_formatted': duration_formatted,
                    'min_price': result['min_price'],
                    'max_price': result['max_price'],
                    'base_price': flight.base_price,
                    'available_seats': result['available_seats'],
                    'status': flight.status,
                    'airplane_model': flight.airplane.model,
                })
        
        response_data = {
            'results': serialized_results,
            'total_count': search_results['total_count'],
            'price_stats': search_results.get('price_stats'),
            'search_params': search_results['search_params'],
        }
        
        if serialized_return_results:
            response_data['return_results'] = serialized_return_results
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Get cheapest flights",
        description="Get the cheapest flights for a specific route",
        parameters=[
            {
                "name": "departure_airport_code",
                "in": "query",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "arrival_airport_code",
                "in": "query",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "departure_date",
                "in": "query",
                "required": True,
                "schema": {"type": "string", "format": "date"},
            },
            {
                "name": "passengers",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "default": 1},
            },
            {
                "name": "limit",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "default": 10},
            },
        ]
    )
    @action(detail=False, methods=["get"], permission_classes=[ReadOnly])
    def cheapest(self, request):
        """Get the cheapest flights for a route"""
        departure_airport_code = request.query_params.get("departure_airport_code")
        arrival_airport_code = request.query_params.get("arrival_airport_code")
        departure_date_str = request.query_params.get("departure_date")
        passengers = int(request.query_params.get("passengers", 1))
        limit = int(request.query_params.get("limit", 10))
        
        if not all([departure_airport_code, arrival_airport_code, departure_date_str]):
            return Response(
                {"error": "departure_airport_code, arrival_airport_code, and departure_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            departure_date = date.fromisoformat(departure_date_str)
        except ValueError:
            return Response(
                {"error": "Invalid departure_date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cheapest_flights = FlightSearchService.get_cheapest_flights(
                departure_airport_code=departure_airport_code,
                arrival_airport_code=arrival_airport_code,
                departure_date=departure_date,
                passengers=passengers,
                limit=limit,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Serialize results
        serialized_results = []
        for result in cheapest_flights:
            flight = result['flight']
            duration = flight.duration
            duration_formatted = str(duration).split('.')[0] if duration else "N/A"
            
            serialized_results.append({
                'flight_id': flight.id,
                'flight_number': flight.flight_number,
                'airline_name': result['airline_name'],
                'airline_code': result['airline_code'],
                'departure_airport_code': flight.departure_airport.code,
                'departure_airport_name': flight.departure_airport.name,
                'departure_city': flight.departure_airport.city,
                'arrival_airport_code': flight.arrival_airport.code,
                'arrival_airport_name': flight.arrival_airport.name,
                'arrival_city': flight.arrival_airport.city,
                'departure_time': flight.departure_time,
                'arrival_time': flight.arrival_time,
                'duration_hours': result['duration_hours'],
                'duration_formatted': duration_formatted,
                'min_price': result['min_price'],
                'max_price': result['max_price'],
                'base_price': flight.base_price,
                'available_seats': result['available_seats'],
                'status': flight.status,
                'airplane_model': flight.airplane.model,
            })
        
        return Response({
            'results': serialized_results,
            'count': len(serialized_results),
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Compare airlines",
        description="Compare prices across different airlines for a route"
    )
    @action(detail=False, methods=["get"], permission_classes=[ReadOnly])
    def compare_airlines(self, request):
        """Compare prices across different airlines"""
        departure_airport_code = request.query_params.get("departure_airport_code")
        arrival_airport_code = request.query_params.get("arrival_airport_code")
        departure_date_str = request.query_params.get("departure_date")
        
        if not all([departure_airport_code, arrival_airport_code, departure_date_str]):
            return Response(
                {"error": "departure_airport_code, arrival_airport_code, and departure_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            departure_date = date.fromisoformat(departure_date_str)
        except ValueError:
            return Response(
                {"error": "Invalid departure_date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            comparison = FlightSearchService.compare_airlines(
                departure_airport_code=departure_airport_code,
                arrival_airport_code=arrival_airport_code,
                departure_date=departure_date,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(comparison, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def seat_map(self, request, pk=None):
        """Get seat map with availability and pricing"""
        from bookings.services import SeatMapService
        
        flight = self.get_object()
        seat_map_data = SeatMapService.get_available_seats(flight)
        
        return Response(seat_map_data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        flight = self.get_object()
        status_value = request.data.get("status")
        if status_value not in dict(Flight.FlightStatus.choices):
            return Response(
                {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )

        flight.status = status_value
        flight.save(update_fields=["status"])
        return Response({"message": f"Flight status updated to {status_value}"})


class FlightSeatViewSet(viewsets.ModelViewSet):
    queryset = FlightSeat.objects.all()
    serializer_class = FlightSeatSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]


class FlightSearchPageView(APIView):
    """Render the flight search page"""
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, 'flight_search.html')



