import stripe
from django.conf import settings
from django.db import models
from django.utils import timezone
from bookings.models import Order, TimeStampedModel
from user.models import User


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Payment(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
        """Mark payment as succeeded and confirm the booking"""
        from bookings.services import BookingService
        
        self.status = PaymentStatus.SUCCEEDED
        self.save(update_fields=["status"])
        
        # Use BookingService to properly confirm the booking
        try:
            BookingService.confirm_booking(self.order)
        except Exception as e:
            # Log error but don't fail the payment - manual intervention needed
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to confirm booking for payment {self.id}: {str(e)}")

    def mark_failed(self):
        """Mark payment as failed and handle order cancellation"""
        from bookings.services import BookingService
        
        self.status = PaymentStatus.FAILED
        self.save(update_fields=["status"])
        
        # Cancel the booking to release seats
        try:
            BookingService.cancel_booking(self.order, reason="Payment failed")
        except Exception as e:
            # Log error but continue - seats will be released by timeout
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to cancel booking for payment {self.id}: {str(e)}")

    def mark_cancelled(self):
        """Mark payment as cancelled"""
        self.status = PaymentStatus.CANCELLED
        self.save(update_fields=["status"])

        # Cancel the order to release seats
        try:
            self.order.cancel(reason="Payment cancelled")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to cancel order for payment {self.id}: {str(e)}")


class CouponStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    USED = "used", "Used"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class Coupon(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="coupons")
    balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Remaining coupon balance")
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Original coupon amount")
    stripe_coupon_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe coupon ID")
    status = models.CharField(
        max_length=20, choices=CouponStatus.choices, default=CouponStatus.ACTIVE
    )
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Coupon expiry date")
    description = models.TextField(blank=True, help_text="Coupon description/reason")

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Coupon {self.id} for {self.user} - ${self.balance} ({self.status})"

    def is_expired(self):
        """Check if coupon is expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def is_usable(self):
        """Check if coupon can be used"""
        return (
            self.status == CouponStatus.ACTIVE
            and self.balance > 0
            and not self.is_expired()
        )

    def deduct_amount(self, amount):
        """Deduct amount from coupon balance"""
        if amount > self.balance:
            raise ValueError("Insufficient coupon balance")
        self.balance -= amount
        if self.balance == 0:
            self.status = CouponStatus.USED
        self.save(update_fields=["balance", "status"])
        return amount
