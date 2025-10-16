from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from user.models import User


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True, help_text="ISO 3166-1 alpha-2 code (e.g., US, GB)", default="XX")
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def clean(self):
        if self.code:
            self.code = self.code.upper()

    def __str__(self):
        return f"{self.name} ({self.code})"


class Airport(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="airports")
    code = models.CharField(max_length=3, unique=True, db_index=True, help_text="IATA code (e.g., JFK, LHR)")
    city = models.CharField(max_length=100, help_text="City where airport is located", default="Unknown")
    timezone = models.CharField(max_length=50, default="UTC", help_text="Airport timezone (e.g., America/New_York)")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_airport_name_per_country")
        ]
        ordering = ["name"]

    def clean(self):
        if self.code:
            self.code = self.code.upper()

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.city}, {self.country.code}"


class Airline(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True, help_text="IATA airline code (e.g., AA, BA)", default="XXX")
    airports = models.ManyToManyField(Airport, related_name="airlines", blank=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if self.code:
            self.code = self.code.upper()

    def __str__(self):
        return f"{self.name} ({self.code})"


class Airplane(models.Model):
    class SeatClass(models.TextChoices):
        ECONOMY = "economy", "Economy"
        PREMIUM_ECONOMY = "premium_economy", "Premium Economy"
        BUSINESS = "business", "Business"
        FIRST = "first", "First Class"

    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    registration = models.CharField(max_length=10, unique=True, help_text="Aircraft registration (e.g., N123AA)", default="N000XX")
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="airplanes")

    capacity = models.PositiveIntegerField(help_text="Total number of seats")
    seat_map = models.JSONField(
        help_text="List of seat definitions with seat_number and seat_class", 
        default=list,
        blank=True
    )

    class Meta:
        indexes = [models.Index(fields=["airline"])]
        constraints = [
            models.UniqueConstraint(fields=["airline", "registration"], name="unique_registration_per_airline")
        ]

    def clean(self):
        if self.registration:
            self.registration = self.registration.upper()
        
        if self.seat_map:
            seat_nums = [s.get("seat_number") for s in self.seat_map if isinstance(s, dict)]
            
            if len(seat_nums) != self.capacity:
                raise ValidationError("Number of seats in seat_map must equal capacity.")
            
            if len(set(seat_nums)) != len(seat_nums):
                raise ValidationError("Duplicate seat numbers in seat_map.")
            
            valid_classes = [choice[0] for choice in self.SeatClass.choices]
            for seat in self.seat_map:
                if isinstance(seat, dict):
                    seat_class = seat.get("seat_class", "economy")
                    if seat_class not in valid_classes:
                        raise ValidationError(f"Invalid seat_class '{seat_class}' for seat {seat.get('seat_number')}")

    def seat_class(self, seat_number):
        """Get seat class for a specific seat number"""
        for seat in self.seat_map:
            if isinstance(seat, dict) and seat.get("seat_number") == seat_number:
                return seat.get("seat_class", "economy")
        return "economy"  # Default fallback

    def get_seat_count_by_class(self):
        """Get count of seats by class"""
        counts = {choice[0]: 0 for choice in self.SeatClass.choices}
        for seat in self.seat_map:
            if isinstance(seat, dict):
                seat_class = seat.get("seat_class", "economy")
                counts[seat_class] = counts.get(seat_class, 0) + 1
        return counts

    def __str__(self):
        return f"{self.airline.code} {self.manufacturer} {self.model} ({self.registration})"


class Flight(TimeStampedModel):
    class FlightStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        BOARDING = "boarding", "Boarding"
        DEPARTED = "departed", "Departed"
        DELAYED = "delayed", "Delayed"
        CANCELLED = "cancelled", "Cancelled"

    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="flights")
    flight_number = models.CharField(max_length=10, db_index=True)

    airplane = models.ForeignKey(Airplane, on_delete=models.PROTECT, related_name="flights")
    departure_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="departing_flights")
    arrival_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="arriving_flights")

    departure_time = models.DateTimeField(help_text="Scheduled departure time (UTC)", db_index=True)
    arrival_time = models.DateTimeField(help_text="Scheduled arrival time (UTC)")
    departure_date = models.DateField(
        help_text="Flight date for grouping and searching",
        db_index=True
    )

    status = models.CharField(max_length=15, choices=FlightStatus.choices, default=FlightStatus.SCHEDULED,
                              db_index=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base economy class price")
    
    # Optional fields for better flight management
    gate = models.CharField(max_length=10, blank=True, help_text="Departure gate")
    actual_departure = models.DateTimeField(null=True, blank=True, help_text="Actual departure time")
    actual_arrival = models.DateTimeField(null=True, blank=True, help_text="Actual arrival time")

    class Meta:
        ordering = ["departure_time"]
        constraints = [
            models.CheckConstraint(check=models.Q(departure_time__lt=models.F("arrival_time")),
                                   name="arrival_after_departure"),
            models.UniqueConstraint(fields=["airline", "flight_number", "departure_date"],
                                    name="unique_flight_number_per_airline_per_day"),
            models.CheckConstraint(check=models.Q(base_price__gte=0), name="base_price_non_negative"),
        ]
        indexes = [
            models.Index(fields=["airline", "flight_number"]),
            models.Index(fields=["departure_airport", "arrival_airport"]),
        ]

    def clean(self):
        if self.departure_airport_id == self.arrival_airport_id:
            raise ValidationError("Departure and arrival airports cannot be the same.")
        if self.airplane_id and self.airline_id and self.airplane.airline_id != self.airline_id:
            raise ValidationError("Airplane's airline must match Flight.airline.")
        if self.departure_time and self.arrival_time and self.departure_time >= self.arrival_time:
            raise ValidationError("Arrival time must be after departure time.")
        
        # Auto-set departure_date from departure_time if not provided
        if self.departure_time and not self.departure_date:
            self.departure_date = self.departure_time.date()

    @property
    def duration(self):
        """Calculate flight duration"""
        if self.departure_time and self.arrival_time:
            return self.arrival_time - self.departure_time
        return None

    @property
    def is_delayed(self):
        """Check if flight is delayed"""
        return self.status == self.FlightStatus.DELAYED

    @property
    def is_active(self):
        """Check if flight is still active (not departed, cancelled)"""
        return self.status in [self.FlightStatus.SCHEDULED, self.FlightStatus.BOARDING, self.FlightStatus.DELAYED]

    def get_available_seat_count(self):
        """Get count of available seats"""
        return self.seats.filter(seat_status=FlightSeat.SeatStatus.AVAILABLE).count()

    def get_occupancy_rate(self):
        """Get flight occupancy rate as percentage"""
        total_seats = self.airplane.capacity
        booked_seats = self.seats.filter(
            seat_status__in=[FlightSeat.SeatStatus.BOOKED, FlightSeat.SeatStatus.RESERVED]
        ).count()
        return (booked_seats / total_seats * 100) if total_seats > 0 else 0

    def __str__(self):
        return f"{self.airline.code} {self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code} on {self.departure_date}"


class FlightSeat(models.Model):
    class SeatStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=10, help_text="Seat number like 12A", db_index=True)
    seat_status = models.CharField(max_length=10, choices=SeatStatus.choices, default=SeatStatus.AVAILABLE,
                                   db_index=True)
    locked_at = models.DateTimeField(null=True, blank=True, help_text="When seat was reserved/locked")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["flight", "seat_number"], name="unique_seat_per_flight_sparse"),
        ]
        indexes = [models.Index(fields=["flight", "seat_status"])]

    def seat_class(self):
        """Get the class of this seat"""
        return self.flight.airplane.seat_class(self.seat_number)

    @property
    def is_available(self):
        """Check if seat is available for booking"""
        return self.seat_status == self.SeatStatus.AVAILABLE

    @property
    def is_reserved(self):
        """Check if seat is currently reserved"""
        return self.seat_status == self.SeatStatus.RESERVED

    def __str__(self):
        return f"{self.flight.airline.code} {self.flight.flight_number} - Seat {self.seat_number} ({self.seat_status})"

