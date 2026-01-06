"""
Management command to populate the database with sample hotel data.
Run with: python manage.py populate_hotels
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from airport.models import Airport
from hotels.models import Hotel, RoomType, Room


class Command(BaseCommand):
    help = 'Populate database with sample hotel data (hotels, room types, and rooms)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing hotel data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing hotel data...'))
            try:
                Room.objects.all().delete()
            except Exception:
                pass
            try:
                Hotel.objects.all().delete()
            except Exception:
                pass
            try:
                RoomType.objects.all().delete()
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS('Populating hotel data...'))

        # Get airports (we'll create hotels near these airports)
        airports = Airport.objects.all()
        if not airports.exists():
            self.stdout.write(self.style.WARNING('No airports found. Please run populate_sample_data first.'))
            return

        # Create Room Types
        self.stdout.write('Creating room types...')
        room_types_data = [
            {
                'name': 'Single Room',
                'description': 'Comfortable single room with one bed',
                'max_occupancy': 1,
                'bed_type': '1 Single Bed',
                'room_size_sqm': Decimal('18.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom']
            },
            {
                'name': 'Double Room',
                'description': 'Spacious double room perfect for couples',
                'max_occupancy': 2,
                'bed_type': '1 King Bed',
                'room_size_sqm': Decimal('25.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'minibar']
            },
            {
                'name': 'Twin Room',
                'description': 'Room with two separate beds',
                'max_occupancy': 2,
                'bed_type': '2 Twin Beds',
                'room_size_sqm': Decimal('24.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom']
            },
            {
                'name': 'Triple Room',
                'description': 'Room suitable for three guests',
                'max_occupancy': 3,
                'bed_type': '1 King Bed + 1 Single Bed',
                'room_size_sqm': Decimal('30.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'sofa']
            },
            {
                'name': 'Family Room',
                'description': 'Large room perfect for families',
                'max_occupancy': 4,
                'bed_type': '2 Double Beds',
                'room_size_sqm': Decimal('35.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'sofa', 'extra_bed']
            },
            {
                'name': 'Suite',
                'description': 'Luxurious suite with separate living area',
                'max_occupancy': 2,
                'bed_type': '1 King Bed',
                'room_size_sqm': Decimal('50.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'minibar', 'sofa', 'balcony', 'jacuzzi']
            },
            {
                'name': 'Executive Suite',
                'description': 'Premium suite with business amenities',
                'max_occupancy': 2,
                'bed_type': '1 King Bed',
                'room_size_sqm': Decimal('60.00'),
                'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'minibar', 'sofa', 'balcony', 'work_desk', 'printer']
            },
        ]

        room_types = {}
        for rt_data in room_types_data:
            room_type, created = RoomType.objects.get_or_create(
                name=rt_data['name'],
                defaults=rt_data
            )
            room_types[rt_data['name']] = room_type
            if created:
                self.stdout.write(f'  Created room type: {room_type.name}')

        # Create Hotels near airports
        self.stdout.write('Creating hotels...')
        
        hotels_data = [
            # Hotels near JFK (New York)
            {
                'name': 'JFK Airport Hotel & Suites',
                'description': 'Modern hotel just 2 minutes from JFK Airport. Perfect for business travelers and layovers.',
                'address': '150-20 140th Street, Jamaica, NY 11430',
                'city': 'New York',
                'country': 'United States',
                'postal_code': '11430',
                'airport_code': 'JFK',
                'distance_km': Decimal('2.5'),
                'phone': '+1-718-555-0100',
                'email': 'info@jfkhotel.com',
                'website': 'https://www.jfkhotel.com',
                'star_rating': 4,
                'amenities': ['wifi', 'pool', 'gym', 'parking', 'shuttle', 'restaurant', 'bar', 'conference_room', 'business_center'],
                'rooms': [
                    {'type': 'Double Room', 'count': 20, 'base_price': Decimal('120.00')},
                    {'type': 'Suite', 'count': 5, 'base_price': Decimal('250.00')},
                    {'type': 'Executive Suite', 'count': 3, 'base_price': Decimal('350.00')},
                ]
            },
            {
                'name': 'Comfort Inn JFK Airport',
                'description': 'Affordable comfort near JFK with free airport shuttle service.',
                'address': '144-10 135th Avenue, Jamaica, NY 11436',
                'city': 'New York',
                'country': 'United States',
                'postal_code': '11436',
                'airport_code': 'JFK',
                'distance_km': Decimal('3.8'),
                'phone': '+1-718-555-0200',
                'email': 'reservations@comfortjfk.com',
                'website': 'https://www.comfortjfk.com',
                'star_rating': 3,
                'amenities': ['wifi', 'parking', 'shuttle', 'breakfast', 'laundry'],
                'rooms': [
                    {'type': 'Single Room', 'count': 15, 'base_price': Decimal('85.00')},
                    {'type': 'Double Room', 'count': 25, 'base_price': Decimal('95.00')},
                    {'type': 'Twin Room', 'count': 10, 'base_price': Decimal('95.00')},
                ]
            },
            
            # Hotels near LHR (London)
            {
                'name': 'Heathrow Airport Marriott',
                'description': 'Luxury hotel connected to Heathrow Terminal 5. World-class amenities and service.',
                'address': 'Heathrow Airport, Longford, TW6 2GD',
                'city': 'London',
                'country': 'United Kingdom',
                'postal_code': 'TW6 2GD',
                'airport_code': 'LHR',
                'distance_km': Decimal('0.5'),
                'phone': '+44-20-5555-0100',
                'email': 'info@marriottlhr.com',
                'website': 'https://www.marriottlhr.com',
                'star_rating': 5,
                'amenities': ['wifi', 'pool', 'gym', 'spa', 'parking', 'restaurant', 'bar', 'conference_room', 'business_center', 'room_service'],
                'rooms': [
                    {'type': 'Double Room', 'count': 50, 'base_price': Decimal('180.00')},
                    {'type': 'Suite', 'count': 15, 'base_price': Decimal('400.00')},
                    {'type': 'Executive Suite', 'count': 10, 'base_price': Decimal('600.00')},
                ]
            },
            {
                'name': 'Premier Inn Heathrow Airport',
                'description': 'Budget-friendly hotel with excellent transport links to Heathrow.',
                'address': 'Bath Road, Longford, UB7 0EQ',
                'city': 'London',
                'country': 'United Kingdom',
                'postal_code': 'UB7 0EQ',
                'airport_code': 'LHR',
                'distance_km': Decimal('4.2'),
                'phone': '+44-20-5555-0200',
                'email': 'bookings@premierlhr.com',
                'website': 'https://www.premierlhr.com',
                'star_rating': 3,
                'amenities': ['wifi', 'parking', 'shuttle', 'restaurant', 'bar'],
                'rooms': [
                    {'type': 'Single Room', 'count': 20, 'base_price': Decimal('65.00')},
                    {'type': 'Double Room', 'count': 40, 'base_price': Decimal('75.00')},
                    {'type': 'Family Room', 'count': 10, 'base_price': Decimal('110.00')},
                ]
            },
            
            # Hotels near CDG (Paris)
            {
                'name': 'Hilton Paris Charles de Gaulle',
                'description': 'Elegant hotel minutes from CDG Airport. French luxury meets modern convenience.',
                'address': 'Roissypôle, 95700 Roissy-en-France',
                'city': 'Paris',
                'country': 'France',
                'postal_code': '95700',
                'airport_code': 'CDG',
                'distance_km': Decimal('1.2'),
                'phone': '+33-1-5555-0100',
                'email': 'reservations@hiltoncdg.com',
                'website': 'https://www.hiltoncdg.com',
                'star_rating': 4,
                'amenities': ['wifi', 'pool', 'gym', 'spa', 'parking', 'restaurant', 'bar', 'conference_room', 'business_center'],
                'rooms': [
                    {'type': 'Double Room', 'count': 60, 'base_price': Decimal('150.00')},
                    {'type': 'Suite', 'count': 12, 'base_price': Decimal('320.00')},
                    {'type': 'Executive Suite', 'count': 8, 'base_price': Decimal('450.00')},
                ]
            },
            {
                'name': 'Ibis Styles Paris CDG',
                'description': 'Modern and colorful hotel near CDG with free shuttle service.',
                'address': '1 Rue de la Haye, 95700 Roissy-en-France',
                'city': 'Paris',
                'country': 'France',
                'postal_code': '95700',
                'airport_code': 'CDG',
                'distance_km': Decimal('3.5'),
                'phone': '+33-1-5555-0200',
                'email': 'contact@ibiscdg.com',
                'website': 'https://www.ibiscdg.com',
                'star_rating': 3,
                'amenities': ['wifi', 'parking', 'shuttle', 'breakfast', 'bar'],
                'rooms': [
                    {'type': 'Single Room', 'count': 18, 'base_price': Decimal('70.00')},
                    {'type': 'Double Room', 'count': 35, 'base_price': Decimal('80.00')},
                    {'type': 'Twin Room', 'count': 12, 'base_price': Decimal('80.00')},
                ]
            },
            
            # Hotels near FRA (Frankfurt)
            {
                'name': 'Sheraton Frankfurt Airport Hotel',
                'description': 'Premium hotel directly connected to Frankfurt Airport terminals.',
                'address': 'Hugo-Eckener-Ring 15, 60549 Frankfurt',
                'city': 'Frankfurt',
                'country': 'Germany',
                'postal_code': '60549',
                'airport_code': 'FRA',
                'distance_km': Decimal('0.3'),
                'phone': '+49-69-5555-0100',
                'email': 'info@sheratonfra.com',
                'website': 'https://www.sheratonfra.com',
                'star_rating': 5,
                'amenities': ['wifi', 'pool', 'gym', 'spa', 'parking', 'restaurant', 'bar', 'conference_room', 'business_center', 'room_service'],
                'rooms': [
                    {'type': 'Double Room', 'count': 80, 'base_price': Decimal('160.00')},
                    {'type': 'Suite', 'count': 20, 'base_price': Decimal('380.00')},
                    {'type': 'Executive Suite', 'count': 12, 'base_price': Decimal('550.00')},
                ]
            },
            {
                'name': 'Holiday Inn Express Frankfurt Airport',
                'description': 'Comfortable and convenient hotel with free breakfast near Frankfurt Airport.',
                'address': 'Amelia-Mary-Earhart-Straße 10, 60549 Frankfurt',
                'city': 'Frankfurt',
                'country': 'Germany',
                'postal_code': '60549',
                'airport_code': 'FRA',
                'distance_km': Decimal('2.8'),
                'phone': '+49-69-5555-0200',
                'email': 'reservations@hiexpressfra.com',
                'website': 'https://www.hiexpressfra.com',
                'star_rating': 3,
                'amenities': ['wifi', 'parking', 'shuttle', 'breakfast', 'bar'],
                'rooms': [
                    {'type': 'Single Room', 'count': 25, 'base_price': Decimal('75.00')},
                    {'type': 'Double Room', 'count': 45, 'base_price': Decimal('85.00')},
                    {'type': 'Twin Room', 'count': 15, 'base_price': Decimal('85.00')},
                ]
            },
            
            # Hotels near LAX (Los Angeles)
            {
                'name': 'Hyatt Regency Los Angeles Airport',
                'description': 'Stylish hotel with stunning views, just minutes from LAX.',
                'address': '6225 W Century Blvd, Los Angeles, CA 90045',
                'city': 'Los Angeles',
                'country': 'United States',
                'postal_code': '90045',
                'airport_code': 'LAX',
                'distance_km': Decimal('1.5'),
                'phone': '+1-310-555-0100',
                'email': 'info@hyattlax.com',
                'website': 'https://www.hyattlax.com',
                'star_rating': 4,
                'amenities': ['wifi', 'pool', 'gym', 'spa', 'parking', 'restaurant', 'bar', 'conference_room', 'business_center'],
                'rooms': [
                    {'type': 'Double Room', 'count': 70, 'base_price': Decimal('140.00')},
                    {'type': 'Suite', 'count': 18, 'base_price': Decimal('300.00')},
                    {'type': 'Executive Suite', 'count': 10, 'base_price': Decimal('420.00')},
                ]
            },
            {
                'name': 'Best Western Plus LAX',
                'description': 'Affordable hotel with free airport shuttle and complimentary breakfast.',
                'address': '6300 W Century Blvd, Los Angeles, CA 90045',
                'city': 'Los Angeles',
                'country': 'United States',
                'postal_code': '90045',
                'airport_code': 'LAX',
                'distance_km': Decimal('2.2'),
                'phone': '+1-310-555-0200',
                'email': 'bookings@bwpluslax.com',
                'website': 'https://www.bwpluslax.com',
                'star_rating': 3,
                'amenities': ['wifi', 'pool', 'parking', 'shuttle', 'breakfast', 'gym'],
                'rooms': [
                    {'type': 'Single Room', 'count': 22, 'base_price': Decimal('90.00')},
                    {'type': 'Double Room', 'count': 38, 'base_price': Decimal('100.00')},
                    {'type': 'Family Room', 'count': 8, 'base_price': Decimal('140.00')},
                ]
            },
            
            # Hotels near SFO (San Francisco)
            {
                'name': 'Grand Hyatt San Francisco Airport',
                'description': 'Luxury hotel with bay views, connected to SFO via AirTrain.',
                'address': '1331 Old Bayshore Hwy, Burlingame, CA 94010',
                'city': 'San Francisco',
                'country': 'United States',
                'postal_code': '94010',
                'airport_code': 'SFO',
                'distance_km': Decimal('1.8'),
                'phone': '+1-650-555-0100',
                'email': 'reservations@ghsfo.com',
                'website': 'https://www.ghsfo.com',
                'star_rating': 5,
                'amenities': ['wifi', 'pool', 'gym', 'spa', 'parking', 'restaurant', 'bar', 'conference_room', 'business_center', 'room_service'],
                'rooms': [
                    {'type': 'Double Room', 'count': 55, 'base_price': Decimal('170.00')},
                    {'type': 'Suite', 'count': 15, 'base_price': Decimal('350.00')},
                    {'type': 'Executive Suite', 'count': 8, 'base_price': Decimal('480.00')},
                ]
            },
            
            # Hotels near MIA (Miami)
            {
                'name': 'Miami Airport Hotel',
                'description': 'Tropical paradise hotel near Miami International Airport.',
                'address': '1101 NW 57th Ave, Miami, FL 33126',
                'city': 'Miami',
                'country': 'United States',
                'postal_code': '33126',
                'airport_code': 'MIA',
                'distance_km': Decimal('2.5'),
                'phone': '+1-305-555-0100',
                'email': 'info@miamiairporthotel.com',
                'website': 'https://www.miamiairporthotel.com',
                'star_rating': 4,
                'amenities': ['wifi', 'pool', 'gym', 'parking', 'shuttle', 'restaurant', 'bar', 'beach_access'],
                'rooms': [
                    {'type': 'Double Room', 'count': 50, 'base_price': Decimal('130.00')},
                    {'type': 'Suite', 'count': 12, 'base_price': Decimal('280.00')},
                    {'type': 'Family Room', 'count': 10, 'base_price': Decimal('180.00')},
                ]
            },
            
            # Hotels near ORD (Chicago)
            {
                'name': 'Hilton Chicago O\'Hare Airport',
                'description': 'Convenient hotel located within O\'Hare Airport complex.',
                'address': 'O\'Hare International Airport, Chicago, IL 60666',
                'city': 'Chicago',
                'country': 'United States',
                'postal_code': '60666',
                'airport_code': 'ORD',
                'distance_km': Decimal('0.8'),
                'phone': '+1-773-555-0100',
                'email': 'info@hiltonord.com',
                'website': 'https://www.hiltonord.com',
                'star_rating': 4,
                'amenities': ['wifi', 'pool', 'gym', 'parking', 'restaurant', 'bar', 'conference_room', 'business_center'],
                'rooms': [
                    {'type': 'Double Room', 'count': 65, 'base_price': Decimal('145.00')},
                    {'type': 'Suite', 'count': 15, 'base_price': Decimal('310.00')},
                    {'type': 'Executive Suite', 'count': 10, 'base_price': Decimal('440.00')},
                ]
            },
        ]

        hotels_created = 0
        rooms_created = 0

        for hotel_data in hotels_data:
            # Find airport by code
            airport = airports.filter(code=hotel_data['airport_code']).first()
            if not airport:
                self.stdout.write(self.style.WARNING(f'  Skipping hotel {hotel_data["name"]} - airport {hotel_data["airport_code"]} not found'))
                continue

            # Extract rooms data
            rooms_info = hotel_data.pop('rooms')
            
            # Extract distance before creating hotel
            distance_km = hotel_data.pop('distance_km')
            
            # Create hotel
            hotel, created = Hotel.objects.get_or_create(
                name=hotel_data['name'],
                city=hotel_data['city'],
                defaults={
                    **{k: v for k, v in hotel_data.items() if k != 'airport_code'},
                    'nearest_airport': airport,
                    'distance_from_airport_km': distance_km,
                }
            )
            
            if created:
                hotels_created += 1
                self.stdout.write(f'  Created hotel: {hotel.name} ({hotel.city})')
                
                # Create rooms for this hotel
                room_number = 101
                for room_info in rooms_info:
                    room_type = room_types[room_info['type']]
                    for i in range(room_info['count']):
                        # Determine floor (every 20 rooms = new floor)
                        floor = (room_number - 101) // 20 + 1
                        
                        # Determine view type (alternate)
                        view_types = ['city', 'airport', 'garden', 'none']
                        view_type = view_types[(room_number - 101) % len(view_types)]
                        
                        Room.objects.create(
                            hotel=hotel,
                            room_type=room_type,
                            room_number=str(room_number),
                            base_price_per_night=room_info['base_price'],
                            floor=floor,
                            view_type=view_type,
                            is_available=True
                        )
                        room_number += 1
                        rooms_created += 1

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created:'))
        self.stdout.write(f'  - {hotels_created} hotels')
        self.stdout.write(f'  - {rooms_created} rooms')
        self.stdout.write(self.style.SUCCESS('\nHotel data populated successfully!'))

