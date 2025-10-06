import stripe
from django.conf import settings
from django.db import models
from bookings.models import Order, TimeStampedModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Payment(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="usd")
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id} ({self.status})"

    def create_stripe_payment_intent(self):

        stripe.api_key = settings.STRIPE_SECRET_KEY

        intent = stripe.PaymentIntent.create(
            amount=int(self.amount * 100),  # Stripe works in cents
            currency=self.currency,
            metadata={"order_id": str(self.order.id)},
        )
        self.stripe_payment_intent_id = intent["id"]
        self.save(update_fields=["stripe_payment_intent_id"])
        return intent

    def mark_succeeded(self):
        self.status = PaymentStatus.SUCCEEDED
        self.save(update_fields=["status"])
        self.order.mark_confirmed()

    def mark_failed(self):
        self.status = PaymentStatus.FAILED
        self.save(update_fields=["status"])
        self.order.mark_failed()
