"""
Management command to populate the database with sample flight data.
Run with: python manage.py populate_sample_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from airport.models import Country, Airport, Airline, Airplane, Flight, FlightSeat


class Command(BaseCommand):
    help = 'Populate database with sample flight data (countries, airports, airlines, airplanes, and flights)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            try:
                FlightSeat.objects.all().delete()
            except Exception:
                pass
            try:
                Flight.objects.all().delete()
            except Exception:
                pass
            try:
                Airplane.objects.all().delete()
            except Exception:
                pass
            try:
                Airline.objects.all().delete()
            except Exception:
                pass
            try:
                Airport.objects.all().delete()
            except Exception:
                pass
            try:
                Country.objects.all().delete()
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS('Populating sample data...'))
        
        # Create Countries
        countries_data = [
            {'name': 'United States', 'code': 'US', 'slug': 'united-states'},
            {'name': 'United Kingdom', 'code': 'GB', 'slug': 'united-kingdom'},
            {'name': 'France', 'code': 'FR', 'slug': 'france'},
            {'name': 'Germany', 'code': 'DE', 'slug': 'germany'},
            {'name': 'Spain', 'code': 'ES', 'slug': 'spain'},
            {'name': 'Italy', 'code': 'IT', 'slug': 'italy'},
            {'name': 'Netherlands', 'code': 'NL', 'slug': 'netherlands'},
            {'name': 'Canada', 'code': 'CA', 'slug': 'canada'},
            {'name': 'Japan', 'code': 'JP', 'slug': 'japan'},
            {'name': 'Australia', 'code': 'AU', 'slug': 'australia'},
        ]
        
        countries = {}
        for country_data in countries_data:
            country, created = Country.objects.get_or_create(
                name=country_data['name'],
                defaults={'code': country_data['code'], 'slug': country_data['slug']}
            )
            countries[country_data['code']] = country
            if created:
                self.stdout.write(f'  Created country: {country.name}')

        # Create Airports
        airports_data = [
            # US Airports
            {'name': 'John F. Kennedy International Airport', 'code': 'JFK', 'city': 'New York', 
             'country': 'US', 'timezone': 'America/New_York'},
            {'name': 'Los Angeles International Airport', 'code': 'LAX', 'city': 'Los Angeles',
             'country': 'US', 'timezone': 'America/Los_Angeles'},
            {'name': 'Chicago O\'Hare International Airport', 'code': 'ORD', 'city': 'Chicago',
             'country': 'US', 'timezone': 'America/Chicago'},
            {'name': 'Miami International Airport', 'code': 'MIA', 'city': 'Miami',
             'country': 'US', 'timezone': 'America/New_York'},
            {'name': 'San Francisco International Airport', 'code': 'SFO', 'city': 'San Francisco',
             'country': 'US', 'timezone': 'America/Los_Angeles'},
            
            # UK Airports
            {'name': 'Heathrow Airport', 'code': 'LHR', 'city': 'London',
             'country': 'GB', 'timezone': 'Europe/London'},
            {'name': 'Gatwick Airport', 'code': 'LGW', 'city': 'London',
             'country': 'GB', 'timezone': 'Europe/London'},
            
            # European Airports
            {'name': 'Charles de Gaulle Airport', 'code': 'CDG', 'city': 'Paris',
             'country': 'FR', 'timezone': 'Europe/Paris'},
            {'name': 'Frankfurt Airport', 'code': 'FRA', 'city': 'Frankfurt',
             'country': 'DE', 'timezone': 'Europe/Berlin'},
            {'name': 'Amsterdam Airport Schiphol', 'code': 'AMS', 'city': 'Amsterdam',
             'country': 'NL', 'timezone': 'Europe/Amsterdam'},
            {'name': 'Madrid-Barajas Airport', 'code': 'MAD', 'city': 'Madrid',
             'country': 'ES', 'timezone': 'Europe/Madrid'},
            {'name': 'Rome Fiumicino Airport', 'code': 'FCO', 'city': 'Rome',
             'country': 'IT', 'timezone': 'Europe/Rome'},
            
            # Other
            {'name': 'Toronto Pearson International Airport', 'code': 'YYZ', 'city': 'Toronto',
             'country': 'CA', 'timezone': 'America/Toronto'},
            {'name': 'Narita International Airport', 'code': 'NRT', 'city': 'Tokyo',
             'country': 'JP', 'timezone': 'Asia/Tokyo'},
            {'name': 'Sydney Kingsford Smith Airport', 'code': 'SYD', 'city': 'Sydney',
             'country': 'AU', 'timezone': 'Australia/Sydney'},
        ]
        
        airports = {}
        for airport_data in airports_data:
            airport, created = Airport.objects.get_or_create(
                code=airport_data['code'],
                defaults={
                    'name': airport_data['name'],
                    'city': airport_data['city'],
                    'country': countries[airport_data['country']],
                    'timezone': airport_data['timezone'],
                }
            )
            airports[airport_data['code']] = airport
            if created:
                self.stdout.write(f'  Created airport: {airport.name} ({airport.code})')

        # Create Airlines
        airlines_data = [
            {'name': 'American Airlines', 'code': 'AA'},
            {'name': 'United Airlines', 'code': 'UA'},
            {'name': 'Delta Air Lines', 'code': 'DL'},
            {'name': 'British Airways', 'code': 'BA'},
            {'name': 'Lufthansa', 'code': 'LH'},
            {'name': 'Air France', 'code': 'AF'},
            {'name': 'KLM Royal Dutch Airlines', 'code': 'KL'},
            {'name': 'Iberia', 'code': 'IB'},
            {'name': 'Alitalia', 'code': 'AZ'},
            {'name': 'Japan Airlines', 'code': 'JL'},
            {'name': 'Qantas', 'code': 'QF'},
            {'name': 'Air Canada', 'code': 'AC'},
        ]
        
        airlines = {}
        for airline_data in airlines_data:
            airline, created = Airline.objects.get_or_create(
                code=airline_data['code'],
                defaults={'name': airline_data['name']}
            )
            airlines[airline_data['code']] = airline
            if created:
                self.stdout.write(f'  Created airline: {airline.name} ({airline.code})')
                # Add some airports to airlines
                if airline.code in ['AA', 'UA', 'DL']:
                    airline.airports.add(airports['JFK'], airports['LAX'], airports['ORD'])
                elif airline.code == 'BA':
                    airline.airports.add(airports['LHR'], airports['JFK'], airports['CDG'])
                elif airline.code == 'LH':
                    airline.airports.add(airports['FRA'], airports['JFK'], airports['LHR'])
                elif airline.code == 'AF':
                    airline.airports.add(airports['CDG'], airports['JFK'], airports['LHR'])

        # Create Airplanes with seat maps
        airplanes = []
        airplane_types = [
            {'manufacturer': 'Boeing', 'model': '737-800', 'capacity': 162},
            {'manufacturer': 'Boeing', 'model': '777-300ER', 'capacity': 365},
            {'manufacturer': 'Airbus', 'model': 'A320', 'capacity': 150},
            {'manufacturer': 'Airbus', 'model': 'A350-900', 'capacity': 325},
            {'manufacturer': 'Boeing', 'model': '787-9 Dreamliner', 'capacity': 290},
        ]
        
        for airline_code, airline in list(airlines.items())[:5]:  # Create planes for first 5 airlines
            for i, plane_type in enumerate(airplane_types):
                seat_map = self.generate_seat_map(plane_type['capacity'])
                registration = f"N{airline.id}{i+1:03d}"
                
                airplane, created = Airplane.objects.get_or_create(
                    registration=registration,
                    defaults={
                        'manufacturer': plane_type['manufacturer'],
                        'model': plane_type['model'],
                        'airline': airline,
                        'capacity': plane_type['capacity'],
                        'seat_map': seat_map,
                    }
                )
                airplanes.append(airplane)
                if created:
                    self.stdout.write(f'  Created airplane: {airline.code} {plane_type["manufacturer"]} {plane_type["model"]} ({registration})')

        # Create Flights
        self.stdout.write('Creating flights...')
        base_date = timezone.now().date()
        flight_routes = [
            # Popular routes
            ('JFK', 'LHR', 'BA', 7, 30),  # New York to London
            ('LHR', 'JFK', 'BA', 8, 0),
            ('LAX', 'JFK', 'AA', 5, 30),
            ('JFK', 'LAX', 'AA', 6, 0),
            ('JFK', 'CDG', 'AF', 7, 15),
            ('CDG', 'JFK', 'AF', 8, 30),
            ('FRA', 'JFK', 'LH', 8, 0),
            ('JFK', 'FRA', 'LH', 7, 45),
            ('JFK', 'AMS', 'KL', 7, 0),
            ('AMS', 'JFK', 'KL', 8, 15),
            ('LAX', 'LHR', 'BA', 10, 30),
            ('LHR', 'LAX', 'BA', 11, 0),
            ('SFO', 'CDG', 'AF', 11, 15),
            ('CDG', 'SFO', 'AF', 11, 30),
            ('ORD', 'FRA', 'LH', 8, 30),
            ('FRA', 'ORD', 'LH', 9, 0),
            ('MIA', 'LHR', 'BA', 9, 0),
            ('LHR', 'MIA', 'BA', 9, 30),
        ]
        
        flight_number_base = 100
        flights_created = 0
        
        for route_idx, route in enumerate(flight_routes):
            dep_code, arr_code, airline_code, duration_hours, duration_minutes = route
            airline = airlines[airline_code]
            departure_airport = airports[dep_code]
            arrival_airport = airports[arr_code]
            
            # Select an appropriate airplane for this airline
            airline_airplanes = [a for a in airplanes if a.airline == airline]
            if not airline_airplanes:
                continue
            
            # Create flights for the next 30 days
            for day_offset in range(30):
                flight_date = base_date + timedelta(days=day_offset)
                
                # Create morning and afternoon flights
                for flight_time_idx, hour in enumerate([8, 14, 20]):
                    departure_time = timezone.make_aware(
                        datetime.combine(flight_date, datetime.min.time().replace(hour=hour))
                    )
                    arrival_time = departure_time + timedelta(hours=duration_hours, minutes=duration_minutes)
                    
                    # Make flight number unique: route index + day offset + time index
                    flight_number = flight_number_base + (route_idx * 100) + (day_offset * 10) + flight_time_idx
                    
                    airplane = airline_airplanes[flight_number % len(airline_airplanes)]
                    
                    # Base price varies by route and date
                    base_price = Decimal('299.99') + Decimal(str(day_offset * 5))  # Price increases closer to date
                    if duration_hours > 8:
                        base_price += Decimal('200')  # Long haul flights cost more
                    
                    flight, created = Flight.objects.get_or_create(
                        airline=airline,
                        flight_number=f"{airline.code}{flight_number}",
                        departure_date=flight_date,
                        defaults={
                            'airplane': airplane,
                            'departure_airport': departure_airport,
                            'arrival_airport': arrival_airport,
                            'departure_time': departure_time,
                            'arrival_time': arrival_time,
                            'base_price': base_price,
                            'status': Flight.FlightStatus.SCHEDULED,
                        }
                    )
                    
                    if created:
                        flights_created += 1
                        # Create seats for this flight
                        self.create_flight_seats(flight, airplane)
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created:'))
        self.stdout.write(f'  - {Country.objects.count()} countries')
        self.stdout.write(f'  - {Airport.objects.count()} airports')
        self.stdout.write(f'  - {Airline.objects.count()} airlines')
        self.stdout.write(f'  - {Airplane.objects.count()} airplanes')
        self.stdout.write(f'  - {Flight.objects.count()} flights')
        self.stdout.write(f'  - {FlightSeat.objects.count()} flight seats')
        self.stdout.write(self.style.SUCCESS('\nDatabase populated successfully!'))

    def generate_seat_map(self, capacity):
        """Generate a seat map for an airplane"""
        seat_map = []
        rows = (capacity // 6) + 1  # Approximate rows (6 seats per row)
        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
        
        seat_num = 1
        for row in range(1, rows + 1):
            for letter in seat_letters:
                if seat_num > capacity:
                    break
                
                # Determine seat class based on row
                if row <= 3:
                    seat_class = 'first'
                elif row <= 8:
                    seat_class = 'business'
                elif row <= 15:
                    seat_class = 'premium_economy'
                else:
                    seat_class = 'economy'
                
                seat_map.append({
                    'seat_number': f"{row}{letter}",
                    'seat_class': seat_class
                })
                seat_num += 1
            
            if seat_num > capacity:
                break
        
        return seat_map

    def create_flight_seats(self, flight, airplane):
        """Create FlightSeat objects for a flight"""
        seats = []
        for seat_info in airplane.seat_map:
            seat = FlightSeat(
                flight=flight,
                seat_number=seat_info['seat_number'],
                seat_status=FlightSeat.SeatStatus.AVAILABLE
            )
            seats.append(seat)
        
        FlightSeat.objects.bulk_create(seats)

