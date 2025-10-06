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
    """Simplified ticket manager - complex logic moved to services"""
    
    def cancel_by_order(self, order, reason=""):
        """Cancel all tickets for an order"""
        from .services import BookingService
        BookingService.cancel_booking(order, reason)


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
