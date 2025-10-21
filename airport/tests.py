from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from airport.models import Country, Airport, Airline, Airplane, Flight, FlightSeat


class CountryModelTest(TestCase):
    """Test Country model"""

    def test_create_country(self):
        """Test creating a country"""
        country = Country.objects.create(name='United States', code='US')
        self.assertEqual(country.name, 'United States')
        self.assertEqual(country.code, 'US')

    def test_country_code_uppercase(self):
        """Test country code is converted to uppercase"""
        country = Country.objects.create(name='United Kingdom', code='gb')
        country.clean()
        self.assertEqual(country.code, 'GB')


class AirportModelTest(TestCase):
    """Test Airport model"""

    def setUp(self):
        self.country = Country.objects.create(name='United States', code='US')

    def test_create_airport(self):
        """Test creating an airport"""
        airport = Airport.objects.create(
            name='John F. Kennedy International Airport',
            country=self.country,
            code='JFK',
            city='New York',
            timezone='America/New_York'
        )
        self.assertEqual(airport.code, 'JFK')
        self.assertEqual(airport.city, 'New York')

    def test_airport_code_uppercase(self):
        """Test airport code is converted to uppercase"""
        airport = Airport.objects.create(
            name='Los Angeles International',
            country=self.country,
            code='lax',
            city='Los Angeles'
        )
        airport.clean()
        self.assertEqual(airport.code, 'LAX')


class AirlineModelTest(TestCase):
    """Test Airline model"""

    def test_create_airline(self):
        """Test creating an airline"""
        airline = Airline.objects.create(name='American Airlines', code='AA')
        self.assertEqual(airline.name, 'American Airlines')
        self.assertEqual(airline.code, 'AA')

    def test_airline_code_uppercase(self):
        """Test airline code is converted to uppercase"""
        airline = Airline.objects.create(name='Delta Air Lines', code='dl')
        airline.clean()
        self.assertEqual(airline.code, 'DL')


class AirplaneModelTest(TestCase):
    """Test Airplane model"""

    def setUp(self):
        self.airline = Airline.objects.create(name='American Airlines', code='AA')

    def test_create_airplane(self):
        """Test creating an airplane"""
        airplane = Airplane.objects.create(
            manufacturer='Boeing',
            model='737-800',
            registration='N123AA',
            airline=self.airline,
            capacity=180
        )
        self.assertEqual(airplane.manufacturer, 'Boeing')
        self.assertEqual(airplane.capacity, 180)

    def test_airplane_registration_uppercase(self):
        """Test registration is converted to uppercase"""
        airplane = Airplane.objects.create(
            manufacturer='Airbus',
            model='A320',
            registration='n456aa',
            airline=self.airline,
            capacity=150
        )
        airplane.clean()
        self.assertEqual(airplane.registration, 'N456AA')


class FlightModelTest(TestCase):
    """Test Flight model"""

    def setUp(self):
        self.country = Country.objects.create(name='United States', code='US')
        self.jfk = Airport.objects.create(
            name='JFK Airport',
            country=self.country,
            code='JFK',
            city='New York'
        )
        self.lax = Airport.objects.create(
            name='LAX Airport',
            country=self.country,
            code='LAX',
            city='Los Angeles'
        )
        self.airline = Airline.objects.create(name='American Airlines', code='AA')
        self.airplane = Airplane.objects.create(
            manufacturer='Boeing',
            model='737',
            registration='N123AA',
            airline=self.airline,
            capacity=180
        )

    def test_create_flight(self):
        """Test creating a flight"""
        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=5)
        
        flight = Flight.objects.create(
            airline=self.airline,
            flight_number='AA100',
            airplane=self.airplane,
            departure_airport=self.jfk,
            arrival_airport=self.lax,
            departure_time=departure,
            arrival_time=arrival,
            departure_date=departure.date(),
            base_price=Decimal('299.99')
        )
        self.assertEqual(flight.flight_number, 'AA100')
        self.assertEqual(flight.base_price, Decimal('299.99'))

    def test_flight_duration(self):
        """Test flight duration calculation"""
        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=5)
        
        flight = Flight.objects.create(
            airline=self.airline,
            flight_number='AA100',
            airplane=self.airplane,
            departure_airport=self.jfk,
            arrival_airport=self.lax,
            departure_time=departure,
            arrival_time=arrival,
            departure_date=departure.date(),
            base_price=Decimal('299.99')
        )
        self.assertEqual(flight.duration, timedelta(hours=5))

    def test_flight_is_active(self):
        """Test is_active property"""
        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=5)
        
        flight = Flight.objects.create(
            airline=self.airline,
            flight_number='AA100',
            airplane=self.airplane,
            departure_airport=self.jfk,
            arrival_airport=self.lax,
            departure_time=departure,
            arrival_time=arrival,
            departure_date=departure.date(),
            base_price=Decimal('299.99'),
            status=Flight.FlightStatus.SCHEDULED
        )
        self.assertTrue(flight.is_active)


class FlightSeatModelTest(TestCase):
    """Test FlightSeat model"""

    def setUp(self):
        self.country = Country.objects.create(name='United States', code='US')
        self.jfk = Airport.objects.create(
            name='JFK Airport',
            country=self.country,
            code='JFK',
            city='New York'
        )
        self.lax = Airport.objects.create(
            name='LAX Airport',
            country=self.country,
            code='LAX',
            city='Los Angeles'
        )
        self.airline = Airline.objects.create(name='American Airlines', code='AA')
        self.airplane = Airplane.objects.create(
            manufacturer='Boeing',
            model='737',
            registration='N123AA',
            airline=self.airline,
            capacity=180
        )
        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=5)
        
        self.flight = Flight.objects.create(
            airline=self.airline,
            flight_number='AA100',
            airplane=self.airplane,
            departure_airport=self.jfk,
            arrival_airport=self.lax,
            departure_time=departure,
            arrival_time=arrival,
            departure_date=departure.date(),
            base_price=Decimal('299.99')
        )

    def test_create_flight_seat(self):
        """Test creating a flight seat"""
        seat = FlightSeat.objects.create(
            flight=self.flight,
            seat_number='12A',
            seat_status=FlightSeat.SeatStatus.AVAILABLE
        )
        self.assertEqual(seat.seat_number, '12A')
        self.assertTrue(seat.is_available)

    def test_seat_is_available(self):
        """Test is_available property"""
        seat = FlightSeat.objects.create(
            flight=self.flight,
            seat_number='12A',
            seat_status=FlightSeat.SeatStatus.AVAILABLE
        )
        self.assertTrue(seat.is_available)

    def test_seat_is_not_available_when_booked(self):
        """Test seat is not available when booked"""
        seat = FlightSeat.objects.create(
            flight=self.flight,
            seat_number='12A',
            seat_status=FlightSeat.SeatStatus.BOOKED
        )
        self.assertFalse(seat.is_available)
