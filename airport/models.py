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


class OrderStatus(models.TextChoices):
    PROCESSING = "processing", "Processing"
    CONFIRMED = "confirmed", "Confirmed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Order(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    flight = models.ForeignKey(Flight, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PROCESSING)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["flight"]),
        ]

    def __str__(self):
        return f"Order {self.id} by {self.user} for {self.flight} ({self.get_status_display()})"

    def mark_confirmed(self):
        self.status = OrderStatus.CONFIRMED
        self.save(update_fields=["status"])

    def mark_failed(self):
        self.status = OrderStatus.FAILED
        self.save(update_fields=["status"])

    def confirm(self):
        self.mark_confirmed()

    def fail_and_release(self, reason=""):
        with transaction.atomic():
            Ticket.objects.release_by_order(self)
            self.mark_failed()

    def cancel(self, reason=""):
        with transaction.atomic():
            Ticket.objects.cancel_by_order(self)
            self.status = OrderStatus.CANCELLED
            self.save(update_fields=["status"])


class TicketStatus(models.TextChoices):
    BOOKED = "booked", "Booked"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class TicketManager(models.Manager):
    SEAT_CLASS_MULTIPLIERS = {
        "economy": Decimal("1.00"),
        "business": Decimal("1.75"),
        "first": Decimal("3.00"),
    }

    def _calculate_price(self, flight, seat_class):
        base = flight.base_price
        mult = self.SEAT_CLASS_MULTIPLIERS.get(seat_class, Decimal("1.00"))
        return (base * mult).quantize(Decimal("0.01"))

    def book_tickets(self, order, seat_numbers):
        if order.status != OrderStatus.PROCESSING:
            raise ValidationError("Order is not in processing state.")

        flight = order.flight
        airplane = flight.airplane
        airplane_seats = {s["seat_number"]: s["seat_class"] for s in airplane.seat_map}

        for seat_num in seat_numbers:
            if seat_num not in airplane_seats:
                raise ValidationError(f"Seat {seat_num} does not exist on this airplane.")

        created_tickets = []
        total_price = Decimal('0')
        now = timezone.now()

        with transaction.atomic():
            flight = Flight.objects.select_for_update().get(pk=flight.pk)

            existing_seats = FlightSeat.objects.filter(
                flight=flight,
                seat_number__in=seat_numbers
            ).exclude(seat_status=FlightSeat.SeatStatus.AVAILABLE)

            if existing_seats.exists():
                raise ValidationError("One or more seats are no longer available.")

            new_seats = []
            for seat_num in seat_numbers:
                new_seats.append(
                    FlightSeat(
                        flight=flight,
                        seat_number=seat_num,
                        seat_status=FlightSeat.SeatStatus.RESERVED,
                        locked_at=now,
                    )
                )

            FlightSeat.objects.bulk_create(new_seats)

            for seat_num in seat_numbers:
                seat_class = airplane_seats[seat_num]
                price = self._calculate_price(flight, seat_class)
                total_price += price

                flight_seat = FlightSeat.objects.get(flight=flight, seat_number=seat_num)
                ticket = self.create(
                    order=order,
                    seat=flight_seat,
                    price=price,
                    status=TicketStatus.BOOKED,
                )
                created_tickets.append(ticket)

            order.total_price = total_price
            # Order remains in PROCESSING until payment succeeds

        return created_tickets

    def book_ticket(self, order, seat_number):
        return self.book_tickets(order, [seat_number])[0]

    def release_by_order(self, order):
        with transaction.atomic():
            tickets = self.filter(order=order)
            seat_ids = tickets.values_list('seat_id', flat=True)

            FlightSeat.objects.filter(id__in=seat_ids).update(
                seat_status=FlightSeat.SeatStatus.AVAILABLE,
                locked_at=None
            )
            tickets.update(status=TicketStatus.CANCELLED)

    def cancel_by_order(self, order, reason=""):
        with transaction.atomic():
            tickets = self.filter(order=order)
            seat_ids = tickets.values_list('seat_id', flat=True)

            FlightSeat.objects.filter(id__in=seat_ids).update(
                seat_status=FlightSeat.SeatStatus.AVAILABLE,
                locked_at=None
            )
            tickets.update(status=TicketStatus.CANCELLED)


class Ticket(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets", null = True)
    seat = models.ForeignKey(FlightSeat, on_delete=models.PROTECT, related_name="tickets")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.BOOKED)

    objects = TicketManager()

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name="ticket_price_non_negative"),
        ]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["seat"]),
        ]

    def __str__(self):
        return f"Ticket {self.id} for {self.order.user} - {self.seat} ({self.status})"

class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def create_stripe_payment_intent(self, currency="usd"):
        try:
            import stripe
            from AirplaneDJ.settings import STRIPE_SECRET_KEY
        except Exception:
            stripe = None
            STRIPE_SECRET_KEY = None

        if stripe is None or not STRIPE_SECRET_KEY:
            raise RuntimeError("Stripe not configured")

        stripe.api_key = STRIPE_SECRET_KEY


        try:
            amount_int = int(float(self.amount) * 100)
        except Exception:
            raise ValueError("Invalid amount for Stripe PaymentIntent")

        if amount_int < 50:  # для USD мінімум 50 cents
            raise ValueError("Amount too small for Stripe PaymentIntent")

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_int,
                currency=currency,
                metadata={"order_id": str(self.order.id)},
                payment_method_types=["card"],
            )
        except stripe.error.InvalidRequestError as e:
            raise ValueError(f"Stripe error: {str(e)}")

        self.stripe_payment_intent_id = intent["id"]
        self.save(update_fields=["stripe_payment_intent_id"])
        return intent

    def mark_succeeded(self):
        self.status = PaymentStatus.SUCCEEDED
        self.save(update_fields=["status"])
        # On success, finalize order and seats
        from django.utils import timezone
        Ticket.objects.filter(order=self.order).update(status=TicketStatus.BOOKED)
        FlightSeat.objects.filter(
            id__in=Ticket.objects.filter(order=self.order).values_list("seat_id", flat=True)
        ).update(seat_status=FlightSeat.SeatStatus.BOOKED, locked_at=timezone.now())
        self.order.mark_confirmed()

    def mark_failed(self):
        self.status = PaymentStatus.FAILED
        self.save(update_fields=["status"])
        # Release seats and fail order
        self.order.fail_and_release()