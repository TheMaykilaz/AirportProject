from django.db import models
from django.conf import settings
from django.utils.text import slugify


User = settings.AUTH_USER_MODEL



class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    country = models.ForeignKey(Country, related_name="airports", on_delete=models.CASCADE)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    class Meta:
        unique_together = ("name", "city", "country")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city}-{self.country.name}")
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} ({self.city}, {self.country.name})"


class Airline(models.Model):
    name = models.CharField(max_length=150)
    airport = models.ForeignKey(Airport, related_name="airlines", on_delete=models.CASCADE)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    class Meta:
        unique_together = ("name", "airport")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.airport.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.airport.name})"


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    airline = models.ForeignKey(Airline, related_name="airplanes", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.airline.name}"


class Flight(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        BOARDING = "boarding", "Boarding"
        DEPARTED = "departed", "Departed"
        DELAYED = "delayed", "Delayed"
        CANCELLED = "cancelled", "Cancelled"

    airplane = models.ForeignKey(Airplane, related_name="flights", on_delete=models.CASCADE)
    origin = models.ForeignKey(Airport, related_name="departing_flights", on_delete=models.CASCADE)
    destination = models.ForeignKey(Airport, related_name="arriving_flights", on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        ordering = ["departure_time"]

    def __str__(self):
        return f"{self.origin.city} → {self.destination.city} [{self.status}]"



class Ticket(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"
        USED = "used", "Used"

    flight = models.ForeignKey(Flight, related_name="tickets", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="tickets", on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("flight", "seat_number")


    def __str__(self):
        return f"Ticket {self.seat_number} - {self.user} ({self.status})"
