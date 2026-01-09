"""
Populate European hotels with Ukrainian names/details and rooms near known airports.
Run with: python manage.py populate_hotels_europe_ua [--clear]
Requires that the corresponding airports exist (e.g., via populate_europe_ua).
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from airport.models import Airport
from hotels.models import Hotel, RoomType, Room


ROOM_TYPES = [
    {
        'name': 'Одномісний номер',
        'description': 'Затишний одномісний номер з одним ліжком',
        'max_occupancy': 1,
        'bed_type': '1 односпальне ліжко',
        'room_size_sqm': Decimal('16.00'),
        'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom']
    },
    {
        'name': 'Двомісний номер',
        'description': 'Просторий номер для двох гостей',
        'max_occupancy': 2,
        'bed_type': '1 двоспальне ліжко',
        'room_size_sqm': Decimal('22.00'),
        'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'minibar']
    },
    {
        'name': 'Номер Твін',
        'description': 'Номер з двома окремими ліжками',
        'max_occupancy': 2,
        'bed_type': '2 односпальні ліжка',
        'room_size_sqm': Decimal('22.00'),
        'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom']
    },
    {
        'name': 'Люкс',
        'description': 'Розкішний номер з вітальнею',
        'max_occupancy': 2,
        'bed_type': '1 двоспальне ліжко',
        'room_size_sqm': Decimal('40.00'),
        'amenities': ['wifi', 'tv', 'air_conditioning', 'private_bathroom', 'minibar', 'sofa']
    },
]

HOTELS_EU_UA = [
    # Poland
    {
        'name': 'Готель Балiце Краків',
        'city': 'Краків', 'country': 'Польща', 'postal_code': '32-083',
        'address': 'вул. Лотнічa 1', 'airport_code': 'KRK', 'distance_km': Decimal('3.2'),
        'star_rating': 4,
        'amenities': ['wifi', 'parking', 'shuttle', 'restaurant', 'bar'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 20, 'base_price': Decimal('85.00')},
            {'type': 'Люкс', 'count': 5, 'base_price': Decimal('150.00')},
        ],
    },
    {
        'name': 'Варшава Аеропорт Отель',
        'city': 'Варшава', 'country': 'Польща', 'postal_code': '02-625',
        'address': 'вул. Жвірки і Вігури 1', 'airport_code': 'WAW', 'distance_km': Decimal('1.1'),
        'star_rating': 3,
        'amenities': ['wifi', 'parking', 'breakfast', 'shuttle'],
        'rooms': [
            {'type': 'Одномісний номер', 'count': 15, 'base_price': Decimal('65.00')},
            {'type': 'Двомісний номер', 'count': 25, 'base_price': Decimal('75.00')},
        ],
    },
    # Czech Republic
    {
        'name': 'Прага Аеропорт Готель',
        'city': 'Прага', 'country': 'Чехія', 'postal_code': '160 08',
        'address': 'K Letišti 1', 'airport_code': 'PRG', 'distance_km': Decimal('2.0'),
        'star_rating': 4,
        'amenities': ['wifi', 'gym', 'parking', 'restaurant', 'bar'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 30, 'base_price': Decimal('90.00')},
            {'type': 'Номер Твін', 'count': 20, 'base_price': Decimal('90.00')},
            {'type': 'Люкс', 'count': 6, 'base_price': Decimal('180.00')},
        ],
    },
    # Austria
    {
        'name': 'Відень Аеропорт Інн',
        'city': 'Відень', 'country': 'Австрія', 'postal_code': '1300',
        'address': 'Flughafenstrasse 1', 'airport_code': 'VIE', 'distance_km': Decimal('0.9'),
        'star_rating': 3,
        'amenities': ['wifi', 'parking', 'shuttle', 'breakfast'],
        'rooms': [
            {'type': 'Одномісний номер', 'count': 18, 'base_price': Decimal('80.00')},
            {'type': 'Двомісний номер', 'count': 22, 'base_price': Decimal('95.00')},
        ],
    },
    # Hungary
    {
        'name': 'Будапешт Аеропорт Сіті',
        'city': 'Будапешт', 'country': 'Угорщина', 'postal_code': '1185',
        'address': 'Ferihegyi 2', 'airport_code': 'BUD', 'distance_km': Decimal('1.6'),
        'star_rating': 4,
        'amenities': ['wifi', 'spa', 'parking', 'restaurant', 'bar'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 28, 'base_price': Decimal('88.00')},
            {'type': 'Люкс', 'count': 8, 'base_price': Decimal('170.00')},
        ],
    },
    # Germany
    {
        'name': 'Берлін Бранденбург Готель',
        'city': 'Берлін', 'country': 'Німеччина', 'postal_code': '12529',
        'address': 'Willy-Brandt-Platz 1', 'airport_code': 'BER', 'distance_km': Decimal('0.6'),
        'star_rating': 4,
        'amenities': ['wifi', 'gym', 'parking', 'restaurant', 'bar', 'conference_room'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 35, 'base_price': Decimal('110.00')},
            {'type': 'Люкс', 'count': 10, 'base_price': Decimal('220.00')},
        ],
    },
    {
        'name': 'Мюнхен Аеропорт Лодж',
        'city': 'Мюнхен', 'country': 'Німеччина', 'postal_code': '85356',
        'address': 'Nordallee 1', 'airport_code': 'MUC', 'distance_km': Decimal('1.3'),
        'star_rating': 3,
        'amenities': ['wifi', 'parking', 'breakfast', 'shuttle'],
        'rooms': [
            {'type': 'Одномісний номер', 'count': 20, 'base_price': Decimal('85.00')},
            {'type': 'Номер Твін', 'count': 18, 'base_price': Decimal('95.00')},
        ],
    },
    # Spain
    {
        'name': 'Барселона Ель-Прат Готель',
        'city': 'Барселона', 'country': 'Іспанія', 'postal_code': '08820',
        'address': 'C/ Aérea 1', 'airport_code': 'BCN', 'distance_km': Decimal('2.2'),
        'star_rating': 4,
        'amenities': ['wifi', 'pool', 'parking', 'restaurant', 'bar'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 26, 'base_price': Decimal('100.00')},
            {'type': 'Люкс', 'count': 6, 'base_price': Decimal('190.00')},
        ],
    },
    {
        'name': 'Мадрид Барахас Інн',
        'city': 'Мадрид', 'country': 'Іспанія', 'postal_code': '28042',
        'address': 'Av. de la Hispanidad 1', 'airport_code': 'MAD', 'distance_km': Decimal('2.8'),
        'star_rating': 3,
        'amenities': ['wifi', 'parking', 'breakfast', 'shuttle'],
        'rooms': [
            {'type': 'Одномісний номер', 'count': 22, 'base_price': Decimal('78.00')},
            {'type': 'Двомісний номер', 'count': 24, 'base_price': Decimal('90.00')},
        ],
    },
    # Italy
    {
        'name': 'Рим Фіумічіно Хотел',
        'city': 'Рим', 'country': 'Італія', 'postal_code': '00054',
        'address': 'Via Aeroporto di Fiumicino 1', 'airport_code': 'FCO', 'distance_km': Decimal('1.9'),
        'star_rating': 4,
        'amenities': ['wifi', 'gym', 'parking', 'restaurant', 'bar'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 34, 'base_price': Decimal('105.00')},
            {'type': 'Люкс', 'count': 10, 'base_price': Decimal('210.00')},
        ],
    },
    # Netherlands
    {
        'name': 'Амстердам Схіпхол Сіті',
        'city': 'Амстердам', 'country': 'Нідерланди', 'postal_code': '1118',
        'address': 'Evert van de Beekstraat 1', 'airport_code': 'AMS', 'distance_km': Decimal('0.7'),
        'star_rating': 4,
        'amenities': ['wifi', 'parking', 'restaurant', 'bar', 'conference_room'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 32, 'base_price': Decimal('115.00')},
            {'type': 'Номер Твін', 'count': 20, 'base_price': Decimal('115.00')},
        ],
    },
    # France
    {
        'name': 'Париж Шарль-де-Голль Готель',
        'city': 'Париж', 'country': 'Франція', 'postal_code': '95700',
        'address': 'Rue de Paris 1', 'airport_code': 'CDG', 'distance_km': Decimal('1.4'),
        'star_rating': 4,
        'amenities': ['wifi', 'spa', 'parking', 'restaurant', 'bar'],
        'rooms': [
            {'type': 'Двомісний номер', 'count': 40, 'base_price': Decimal('130.00')},
            {'type': 'Люкс', 'count': 12, 'base_price': Decimal('260.00')},
        ],
    },
]


class Command(BaseCommand):
    help = 'Populate European hotels (Ukrainian names) near known airports with room types and rooms.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear created hotels, rooms and (optionally) room types')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Видалення існуючих номерів та готелів (Європа UA)...'))
            Room.objects.all().delete()
            Hotel.objects.all().delete()

        # Ensure RoomTypes exist (by Ukrainian name)
        room_types = {}
        for rt in ROOM_TYPES:
            obj, _ = RoomType.objects.get_or_create(name=rt['name'], defaults=rt)
            room_types[rt['name']] = obj

        airports = {a.code: a for a in Airport.objects.filter(code__in=[h['airport_code'] for h in HOTELS_EU_UA])}
        created_hotels = 0
        created_rooms = 0

        for h in HOTELS_EU_UA:
            airport = airports.get(h['airport_code'])
            if not airport:
                self.stdout.write(self.style.WARNING(f"  Пропуск: {h['name']} (немає аеропорту {h['airport_code']})"))
                continue

            rooms_info = h.pop('rooms')
            distance_km = h.pop('distance_km')
            airport_code = h.pop('airport_code')

            hotel, created = Hotel.objects.get_or_create(
                name=h['name'], city=h['city'],
                defaults={
                    **h,
                    'nearest_airport': airport,
                    'distance_from_airport_km': distance_km,
                    'images': [],
                    'amenities': h.get('amenities', []),
                }
            )
            if created:
                created_hotels += 1
                self.stdout.write(f"  Створено готель: {hotel.name} — {hotel.city}")

                room_number = 101
                for info in rooms_info:
                    rt = room_types[info['type']]
                    for i in range(info['count']):
                        # simple rotating views
                        view_types = ['city', 'airport', 'garden', 'none']
                        view_type = view_types[(room_number - 101) % len(view_types)]
                        Room.objects.create(
                            hotel=hotel,
                            room_type=rt,
                            room_number=str(room_number),
                            base_price_per_night=info['base_price'],
                            floor=(room_number - 101) // 20 + 1,
                            view_type=view_type,
                            is_available=True,
                        )
                        room_number += 1
                        created_rooms += 1

        self.stdout.write(self.style.SUCCESS('\nГотово. Створено:'))
        self.stdout.write(f'  - {created_hotels} готелів')
        self.stdout.write(f'  - {created_rooms} номерів')
