"""
Populate European countries (if missing) and airports with Ukrainian city names.
Run with: python manage.py populate_europe_ua [--clear]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from airport.models import Country, Airport


EU_COUNTRIES = [
    {"code": "PL", "name": "Польща", "slug": "poland"},
    {"code": "CZ", "name": "Чехія", "slug": "czech-republic"},
    {"code": "AT", "name": "Австрія", "slug": "austria"},
    {"code": "HU", "name": "Угорщина", "slug": "hungary"},
    {"code": "DE", "name": "Німеччина", "slug": "germany"},
    {"code": "ES", "name": "Іспанія", "slug": "spain"},
    {"code": "IT", "name": "Італія", "slug": "italy"},
    {"code": "NL", "name": "Нідерланди", "slug": "netherlands"},
    {"code": "FR", "name": "Франція", "slug": "france"},
    {"code": "GR", "name": "Греція", "slug": "greece"},
    {"code": "DK", "name": "Данія", "slug": "denmark"},
    {"code": "SE", "name": "Швеція", "slug": "sweden"},
]

AIRPORTS_UA = [
    {"code": "KRK", "name": "Аеропорт Краків-Баліце", "city": "Краків", "country": "PL", "timezone": "Europe/Warsaw"},
    {"code": "WAW", "name": "Аеропорт імені Фредеріка Шопена", "city": "Варшава", "country": "PL", "timezone": "Europe/Warsaw"},
    {"code": "PRG", "name": "Аеропорт Вацлава Гавела", "city": "Прага", "country": "CZ", "timezone": "Europe/Prague"},
    {"code": "VIE", "name": "Міжнародний аеропорт Відня", "city": "Відень", "country": "AT", "timezone": "Europe/Vienna"},
    {"code": "BUD", "name": "Аеропорт імені Ференца Ліста", "city": "Будапешт", "country": "HU", "timezone": "Europe/Budapest"},
    {"code": "BER", "name": "Аеропорт Берлін-Бранденбург", "city": "Берлін", "country": "DE", "timezone": "Europe/Berlin"},
    {"code": "MUC", "name": "Аеропорт Мюнхен", "city": "Мюнхен", "country": "DE", "timezone": "Europe/Berlin"},
    {"code": "BCN", "name": "Аеропорт Барселона-ель-Прат", "city": "Барселона", "country": "ES", "timezone": "Europe/Madrid"},
    {"code": "MAD", "name": "Аеропорт Мадрид-Барахас", "city": "Мадрид", "country": "ES", "timezone": "Europe/Madrid"},
    {"code": "FCO", "name": "Аеропорт Рим-Фіумічіно", "city": "Рим", "country": "IT", "timezone": "Europe/Rome"},
    {"code": "MXP", "name": "Аеропорт Мілан-Мальпенса", "city": "Мілан", "country": "IT", "timezone": "Europe/Rome"},
    {"code": "AMS", "name": "Аеропорт Амстердам Схіпхол", "city": "Амстердам", "country": "NL", "timezone": "Europe/Amsterdam"},
    {"code": "CDG", "name": "Аеропорт Шарль-де-Голль", "city": "Париж", "country": "FR", "timezone": "Europe/Paris"},
    {"code": "NCE", "name": "Аеропорт Ніцца-Лазурний Берег", "city": "Ніцца", "country": "FR", "timezone": "Europe/Paris"},
    {"code": "ATH", "name": "Аеропорт Афіни імені Елефтеріоса Венізелоса", "city": "Афіни", "country": "GR", "timezone": "Europe/Athens"},
    {"code": "CPH", "name": "Копенгагенський аеропорт", "city": "Копенгаген", "country": "DK", "timezone": "Europe/Copenhagen"},
    {"code": "ARN", "name": "Аеропорт Стокгольм-Арланда", "city": "Стокгольм", "country": "SE", "timezone": "Europe/Stockholm"},
]


class Command(BaseCommand):
    help = 'Populate European airports with Ukrainian city names (creates countries if needed)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true', help='Clear only airports created by this command (by IATA codes listed)'
        )

    def handle(self, *args, **options):
        if options['clear']:
            codes = [a["code"] for a in AIRPORTS_UA]
            deleted = Airport.objects.filter(code__in=codes).delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} airport records.'))

        # Ensure countries exist (by code); keep existing name if country already exists
        countries = {}
        for c in EU_COUNTRIES:
            country, _ = Country.objects.get_or_create(
                code=c["code"], defaults={"name": c["name"], "slug": c["slug"]}
            )
            countries[c["code"]] = country

        created_count = 0
        for ap in AIRPORTS_UA:
            country = countries[ap["country"]]
            airport, created = Airport.objects.get_or_create(
                code=ap["code"],
                defaults={
                    "name": ap["name"],
                    "city": ap["city"],
                    "country": country,
                    "timezone": ap["timezone"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Створено аеропорт: {airport.name} ({airport.code}) — {airport.city}")
        self.stdout.write(self.style.SUCCESS(f"Готово. Створено нових аеропортів: {created_count}"))
