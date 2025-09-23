from decimal import Decimal
from django.db import models, transaction, IntegrityError
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='airports')
    code = models.CharField(max_length=4, unique=True, help_text="IATA/ICAO airport code (e.g., JFK, EGLL)")

    class Meta:
        constraints = [
            # в одній країні не може бути двох аеропортів з однаковою назвою.
            models.UniqueConstraint(fields=['name', 'country'], name='unique_airport_name_per_country')
        ]
        ordering = ['name']

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Airline(models.Model):
    name = models.CharField(max_length=100, unique=True)
    airports = models.ManyToManyField(Airport, related_name='airlines')  # airports this airline services (simplified)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


#Літак належить авіакомпанії TEST
class Airplane(models.Model):
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='airplanes')
    # Optionally add registration/tail number (string) here if you need unique plane identification.

    def __str__(self) -> str:
        return f"{self.airline.name} - {self.manufacturer} {self.model}"

#TEST

class Seat(models.Model):
    class SeatClass(models.TextChoices):
        ECONOMY = 'economy', 'Economy'
        BUSINESS = 'business', 'Business'
        FIRST = 'first', 'First Class'

    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name='seats')
    row_number = models.PositiveIntegerField(help_text="Row number, e.g., 1, 12, 23")
    seat_letter = models.CharField(max_length=1, help_text="Seat letter, e.g., A, B, C")
    seat_class = models.CharField(max_length=10, choices=SeatClass.choices, default=SeatClass.ECONOMY)
    is_window = models.BooleanField(default=False)
    is_aisle = models.BooleanField(default=False)
    is_exit_row = models.BooleanField(default=False)

    class Meta:
        constraints = [
            #не можна мати два однакових сидіння в одному літаку.
            models.UniqueConstraint(fields=['airplane', 'row_number', 'seat_letter'], name='unique_seat_per_airplane')
        ]
        ordering = ['row_number', 'seat_letter']

    @property
    def seat_number(self) -> str:
        return f"{self.row_number}{self.seat_letter}"

    def __str__(self) -> str:
        # Include airline and airplane model so listings are unambiguous.
        return f"{self.airplane.airline.name} / {self.airplane.model} - Seat {self.seat_number}"



class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    def __str__(self) -> str:
        return self.username



class Flight(TimeStampedModel):
    class FlightStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        BOARDING = 'boarding', 'Boarding'
        DEPARTED = 'departed', 'Departed'
        DELAYED = 'delayed', 'Delayed'
        CANCELLED = 'cancelled', 'Cancelled'

   
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name='flights')
    flight_number = models.CharField(max_length=10)  # uniqueness enforced per airline via constraint below

    airplane = models.ForeignKey(Airplane, on_delete=models.PROTECT, related_name='flights')
    departure_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='departing_flights')
    arrival_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='arriving_flights')
    departure_time = models.DateTimeField(help_text="UTC datetime")
    arrival_time = models.DateTimeField(help_text="UTC datetime")
    status = models.CharField(max_length=15, choices=FlightStatus.choices, default=FlightStatus.SCHEDULED)


    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Store Decimal values using Decimal('123.45') in code")
    currency_code = models.CharField(
        max_length=3,
        choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')],
        default='USD'
    )

    class Meta:
        ordering = ['departure_time']
        constraints = [
            models.CheckConstraint(check=models.Q(departure_time__lt=models.F('arrival_time')), name='arrival_after_departure'),
            models.UniqueConstraint(fields=['airline', 'flight_number'], name='unique_flight_number_per_airline'),
            models.CheckConstraint(check=models.Q(base_price__gte=0), name='base_price_non_negative'),
        ]

    def clean(self):
        # 1) Basic origin/destination sanity
        if self.departure_airport == self.arrival_airport:
            raise ValidationError("Departure and arrival airports cannot be the same.")

        # 2) Ensure the airplane belongs to the same airline as provided on the flight record
        if self.airplane.airline_id != self.airline_id:
            raise ValidationError("Airplane's airline must match Flight.airline.")

        # 3) Confirm airline services both endpoints (simplified; replace with more complex route model if needed)
        if not self.airline.airports.filter(pk=self.departure_airport.pk).exists():
            raise ValidationError(f"{self.airline.name} does not operate from {self.departure_airport.name}.")
        if not self.airline.airports.filter(pk=self.arrival_airport.pk).exists():
            raise ValidationError(f"{self.airline.name} does not operate to {self.arrival_airport.name}.")

        # 4) Optional: prevent scheduling flights in the past when creating new flights (business rule)
        # Use timezone-aware now
        now = timezone.now()
        # Only enforce for new records (you may allow adjusting past flights when editing historical data)
        if not self.pk and self.departure_time < now:
            raise ValidationError("Departure time cannot be in the past.")

    def __str__(self) -> str:
        return f"{self.airline.name} {self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code}"



class Ticket(TimeStampedModel):
    class TicketStatus(models.TextChoices):
        PENDING = 'pending', 'Payment Pending'
        BOOKED = 'booked', 'Booked'
        CANCELLED = 'cancelled', 'Cancelled'
        USED = 'used', 'Used (Passenger Boarded)'

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name='tickets')
    status = models.CharField(max_length=15, choices=TicketStatus.choices, default=TicketStatus.PENDING)
    final_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Use Decimal in code when assigning values.")
    payment_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(check=models.Q(final_price__gte=0), name="ticket_price_non_negative"),
            # Prevent simultaneous active (pending/booked) tickets for the same seat on the same flight.
            models.UniqueConstraint(
                fields=['flight', 'seat'],
                condition=models.Q(status__in=['pending', 'booked']),
                name='unique_active_ticket_per_seat_on_flight'
            )
        ]

    def clean(self):
        # 1. Ensure the selected seat belongs to the flight's airplane
        if self.seat.airplane_id != self.flight.airplane_id:
            raise ValidationError("Selected seat does not belong to the flight's airplane.")

        # 2. Prevent booking for departed/cancelled flights
        if self.flight.status in [Flight.FlightStatus.DEPARTED, Flight.FlightStatus.CANCELLED]:
            raise ValidationError(f"Cannot book ticket: flight is '{self.flight.get_status_display()}'.")

        # 3. Optional pre-check: provide friendly error before hitting DB constraint (race possible)
        if self.pk is None and self.status in [self.TicketStatus.PENDING, self.TicketStatus.BOOKED]:
            if Ticket.objects.filter(
                flight=self.flight,
                seat=self.seat,
                status__in=[self.TicketStatus.PENDING, self.TicketStatus.BOOKED]
            ).exists():
                raise ValidationError("This seat is already booked or reserved for this flight.")

    def __str__(self) -> str:
        return f"Ticket for {self.user.username} on {self.flight.airline.name} {self.flight.flight_number} ({self.seat.seat_number})"
