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


class OrderStatus(models.TextChoices):
    PROCESSING = "processing", "Processing"
    CONFIRMED = "confirmed", "Confirmed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Order(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    flight = models.ForeignKey('airport.Flight', on_delete=models.PROTECT, related_name="orders")
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
            Ticket.objects.cancel_by_order(self)
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
        from airport.models import Flight, FlightSeat
        
        if order.status != OrderStatus.PROCESSING:
            raise ValidationError("Order is not in processing state.")

        flight = order.flight
        airplane = flight.airplane

        # Build seat map - handle both dict and string formats
        airplane_seats = {}
        for s in airplane.seat_map:
            if isinstance(s, dict):
                seat_number = s.get("seat_number")
                seat_class = s.get("seat_class", "economy")
            else:
                seat_number = str(s)
                seat_class = "economy"
            airplane_seats[seat_number] = seat_class

        for seat_num in seat_numbers:
            if seat_num not in airplane_seats:
                raise ValidationError(f"Seat {seat_num} does not exist on this airplane.")
        
        created_tickets = []
        total_price = Decimal("0")
        now = timezone.now()

        with transaction.atomic():
            # Lock flight for concurrent booking
            flight = Flight.objects.select_for_update().get(pk=flight.pk)

            # Check that seats are still available
            busy_seats = FlightSeat.objects.filter(
                flight=flight,
                seat_number__in=seat_numbers
            ).exclude(seat_status=FlightSeat.SeatStatus.AVAILABLE)

            if busy_seats.exists():
                taken = [s.seat_number for s in busy_seats]
                raise ValidationError(f"Seats already booked or reserved: {', '.join(taken)}")

            # Create FlightSeat objects if they don't exist
            existing = set(
                FlightSeat.objects.filter(flight=flight, seat_number__in=seat_numbers)
                .values_list("seat_number", flat=True)
            )

            new_seats = [
                FlightSeat(
                    flight=flight,
                    seat_number=seat_num,
                    seat_status=FlightSeat.SeatStatus.RESERVED,
                    locked_at=now,
                )
                for seat_num in seat_numbers if seat_num not in existing
            ]
            if new_seats:
                FlightSeat.objects.bulk_create(new_seats)

            # Create tickets
            seats = FlightSeat.objects.filter(flight=flight, seat_number__in=seat_numbers)
            seat_map = {s.seat_number: s for s in seats}

            for seat_num in seat_numbers:
                seat_class = airplane_seats[seat_num]
                price = self._calculate_price(flight, seat_class)
                total_price += price

                ticket = self.create(
                    order=order,
                    seat=seat_map[seat_num],
                    price=price,
                    status=TicketStatus.BOOKED,
                )
                created_tickets.append(ticket)

            # Update order total price
            order.total_price = total_price
            order.save(update_fields=["total_price"])

        return created_tickets

    def book_ticket(self, order, seat_number):
        return self.book_tickets(order, [seat_number])[0]

    def cancel_by_order(self, order, reason=""):
        from airport.models import FlightSeat
        
        with transaction.atomic():
            tickets = self.filter(order=order)
            seat_ids = tickets.values_list("seat_id", flat=True)

            FlightSeat.objects.filter(id__in=seat_ids).update(
                seat_status=FlightSeat.SeatStatus.AVAILABLE,
                locked_at=None
            )
            tickets.update(status=TicketStatus.CANCELLED)


class Ticket(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")
    seat = models.ForeignKey('airport.FlightSeat', on_delete=models.PROTECT, related_name="tickets")
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
