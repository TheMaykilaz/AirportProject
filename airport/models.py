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
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="airports")
    code = models.CharField(max_length=3, unique=True, db_index=True, help_text="IATA code")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_airport_name_per_country")
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Airline(models.Model):
    name = models.CharField(max_length=100, unique=True)
    airports = models.ManyToManyField(Airport, related_name="airlines")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Airplane(models.Model):
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="airplanes")

    capacity = models.PositiveIntegerField(help_text="Total number of seats")
    seat_map = models.JSONField(help_text="List of seat definitions", default=list)

    class Meta:
        indexes = [models.Index(fields=["airline"])]

    def clean(self):
        seat_nums = [s.get("seat_number") for s in self.seat_map]
        if len(seat_nums) != self.capacity:
            raise ValidationError("seat_map entries length must equal capacity.")
        if len(set(seat_nums)) != len(seat_nums):
            raise ValidationError("Duplicate seat_number in seat_map.")
        for s in self.seat_map:
            if s.get("seat_class") not in ("economy", "business", "first"):
                raise ValidationError(f"Invalid seat_class for {s.get('seat_number')}")

    def seat_class(self, seat_number):
        for s in self.seat_map:
            if s["seat_number"] == seat_number:
                return s["seat_class"]
        raise KeyError(f"Seat {seat_number} not present in airplane seat map")

    def __str__(self):
        return f"{self.airline.name} - {self.manufacturer} {self.model} ({self.capacity} seats)"


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

    departure_time = models.DateTimeField(help_text="UTC datetime", db_index=True)
    arrival_time = models.DateTimeField(help_text="UTC datetime")
    departure_date = models.DateField(
        help_text="date for unique flight instances",
        db_index=True,
        default=timezone.now
    )

    status = models.CharField(max_length=15, choices=FlightStatus.choices, default=FlightStatus.SCHEDULED,
                              db_index=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base ticket price")

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

    def __str__(self):
        return f"{self.airline.name} {self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code} on {self.departure_date}"


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
        return self.flight.airplane.seat_class(self.seat_number)

    def __str__(self):
        return f"{self.flight} - Seat {self.seat_number} ({self.seat_status})"

