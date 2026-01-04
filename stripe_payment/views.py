import stripe
import logging
import time
import json
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample

from bookings.models import Order, OrderStatus
from .models import Payment, PaymentStatus, Coupon, CouponStatus
from .serializers import PaymentSerializer, CouponSerializer
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly
from AirplaneDJ.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PUBLISHABLE_KEY

stripe.api_key = STRIPE_SECRET_KEY
endpoint_secret = STRIPE_WEBHOOK_SECRET

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    @extend_schema(
        examples=[
            OpenApiExample(
                "Create Payment",
                value={"order": 123},
                request_only=True,
            ),
            OpenApiExample(
                "Create Payment Response",
                value={
                    "payment_id": 10,
                    "order_id": 123,
                    "client_secret": "pi_12345_secret_abc",
                },
                response_only=True,
            ),
        ]
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data.get("order").id if hasattr(serializer.validated_data.get("order"), "id") else request.data.get("order")
        order = get_object_or_404(Order, id=order_id, user=request.user)

        coupon = serializer.validated_data.get("coupon")
        discount_amount = 0
        final_amount = order.total_price

        # Apply coupon if provided
        if coupon:
            if not coupon.is_usable():
                return Response({"error": "Coupon is not valid or usable"}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate discount (up to the coupon balance or order total, whichever is smaller)
            discount_amount = min(coupon.balance, order.total_price)
            final_amount = order.total_price - discount_amount

            # Validate minimum payment amount
            if final_amount < 0.50:  # Stripe minimum is $0.50
                return Response({"error": "Payment amount too small after coupon application"}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            order=order,
            coupon=coupon,
            amount=final_amount,
            discount_amount=discount_amount
        )

        # Deduct from coupon balance if coupon was used
        if coupon and discount_amount > 0:
            try:
                coupon.deduct_amount(discount_amount)
            except ValueError as e:
                payment.delete()  # Clean up payment if coupon deduction fails
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        intent = payment.create_stripe_payment_intent()
        return Response({
            "payment_id": payment.id,
            "order_id": order.id,
            "coupon_applied": coupon.id if coupon else None,
            "discount_amount": str(discount_amount),
            "final_amount": str(final_amount),
            "client_secret": intent.get("client_secret"),
        }, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Mark payment succeeded (test)")
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        payment.mark_succeeded()
        return Response({"message": f"Payment {payment.id} succeeded"})

    @extend_schema(summary="Mark payment failed (test)")
    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        payment = self.get_object()
        payment.mark_failed()
        return Response({"message": f"Payment {payment.id} failed"})

    @extend_schema(
        summary="Create Stripe Checkout Session",
        description="Creates a Stripe Checkout session and returns the URL to redirect to Stripe's hosted payment page"
    )
    @action(detail=False, methods=["post"])
    def create_checkout_session(self, request):
        """Create a Stripe Checkout Session for hosted payment page"""
        order_id = request.data.get("order")
        if not order_id:
            return Response({"error": "order is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Get or create payment record
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={"amount": order.total_price}
        )
        if not created:
            # Update amount if payment already exists
            payment.amount = order.total_price
            payment.save()
        
        # Get the domain from the request
        domain = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
        
        try:
            # Create Stripe Checkout Session with 30-minute expiration
            expires_at = int(time.time()) + (30 * 60)  # 30 minutes from now
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Flight Order #{order.id}',
                            'description': f'Payment for flight booking',
                        },
                        'unit_amount': int(payment.amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=domain + f'/api/payments/success/?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=domain + f'/api/payments/cancel/?order_id={order.id}',
                expires_at=expires_at,
                metadata={
                    'payment_id': payment.id,
                    'order_id': order.id,
                }
            )
            
            # Store the checkout session ID
            payment.stripe_payment_intent_id = checkout_session.payment_intent
            payment.save()
            
            return Response({
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id,
                "payment_id": payment.id,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            payment.delete()  # Clean up if checkout session creation fails
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CouponViewSet(viewsets.ModelViewSet):
    serializer_class = CouponSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Coupon.objects.all()
        return Coupon.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsSelfOrAdmin()]
        elif self.action in ["create"]:
            return [IsAdmin()]  # Only admins can create coupons
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        # Allow admin to assign coupon to any user
        user = serializer.validated_data.get('user', self.request.user)
        serializer.save(user=user)


logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Improved Stripe webhook handler with better error handling and logging
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event_id = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        event_id = event.get("id")
        event_type = event.get("type")
        
        logger.info(f"Received Stripe webhook: {event_type} (ID: {event_id})")
        
    except ValueError as e:
        logger.error(f"Webhook error - Invalid payload: {e}")
        return Response({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook error - Invalid signature: {e}")
        return Response({"error": "Invalid signature"}, status=400)
    
    # Handle different event types
    try:
        if event_type == "payment_intent.succeeded":
            return _handle_payment_succeeded(event)
        elif event_type == "payment_intent.payment_failed":
            return _handle_payment_failed(event)
        elif event_type == "payment_intent.canceled":
            return _handle_payment_cancelled(event)
        elif event_type == "checkout.session.completed":
            return _handle_checkout_completed(event)
        elif event_type == "checkout.session.expired":
            return _handle_checkout_expired(event)
        elif event_type == "coupon.created":
            return _handle_coupon_created(event)
        elif event_type == "coupon.updated":
            return _handle_coupon_updated(event)
        elif event_type == "coupon.deleted":
            return _handle_coupon_deleted(event)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return Response({"status": "ignored", "event_type": event_type}, status=200)
            
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {str(e)}", exc_info=True)
        return Response({"error": "Internal server error"}, status=500)


def _handle_payment_succeeded(event):
    """Handle successful payment intent"""
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    amount_received = payment_intent.get("amount_received", 0)

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )

            # Validation: Check if order is still in processing state
            if payment.order.status != OrderStatus.PROCESSING:
                logger.warning(f"Order {payment.order.id} not in processing state: {payment.order.status}")
                return Response({"error": "Order not in valid state for payment"}, status=400)

            # Validation: Check amount matches
            if amount_received != int(payment.amount * 100):
                logger.error(f"Amount mismatch for payment {payment.id}: expected {int(payment.amount * 100)}, received {amount_received}")
                return Response({"error": "Amount mismatch"}, status=400)

            # Prevent duplicate processing
            if payment.status == PaymentStatus.SUCCEEDED:
                logger.info(f"Payment {payment.id} already processed as succeeded")
                return Response({"status": "already_processed"}, status=200)

            # Mark payment as succeeded and confirm booking
            payment.mark_succeeded()
            logger.info(f"Payment {payment.id} marked as succeeded, order {payment.order.id} confirmed")

            return Response({
                "status": "success",
                "payment_id": payment.id,
                "order_id": payment.order.id
            }, status=200)

    except Payment.DoesNotExist:
        logger.warning(f"Payment not found for intent: {payment_intent_id}")
        return Response({"error": "Payment not found"}, status=404)
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        return Response({"error": "Processing failed"}, status=500)


def _handle_payment_failed(event):
    """Handle failed payment intent"""
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    failure_reason = payment_intent.get("last_payment_error", {}).get("message", "Unknown")

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )

            # Validation: Check if order is still in processing state
            if payment.order.status != OrderStatus.PROCESSING:
                logger.warning(f"Order {payment.order.id} not in processing state: {payment.order.status}")
                return Response({"error": "Order not in valid state for payment"}, status=400)

            # Prevent duplicate processing
            if payment.status == PaymentStatus.FAILED:
                logger.info(f"Payment {payment.id} already processed as failed")
                return Response({"status": "already_processed"}, status=200)

            # Mark payment as failed and handle order
            payment.mark_failed()
            logger.error(f"Payment {payment.id} failed: {failure_reason}")

            return Response({
                "status": "success",
                "payment_id": payment.id,
                "order_id": payment.order.id,
                "failure_reason": failure_reason
            }, status=200)

    except Payment.DoesNotExist:
        logger.warning(f"Payment not found for failed intent: {payment_intent_id}")
        return Response({"error": "Payment not found"}, status=404)
    except Exception as e:
        logger.error(f"Error processing payment failure: {str(e)}")
        return Response({"error": "Processing failed"}, status=500)


def _handle_payment_cancelled(event):
    """Handle cancelled payment intent"""
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    cancellation_reason = payment_intent.get("cancellation_reason", "Unknown")

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )

            # Validation: Check if order is still in processing state
            if payment.order.status != OrderStatus.PROCESSING:
                logger.warning(f"Order {payment.order.id} not in processing state: {payment.order.status}")
                return Response({"error": "Order not in valid state for payment"}, status=400)

            # Prevent duplicate processing
            if payment.status == PaymentStatus.CANCELLED:
                logger.info(f"Payment {payment.id} already processed as cancelled")
                return Response({"status": "already_processed"}, status=200)

            # Mark payment as cancelled and handle order
            payment.mark_cancelled()
            logger.info(f"Payment {payment.id} cancelled: {cancellation_reason}")

            return Response({
                "status": "success",
                "payment_id": payment.id,
                "order_id": payment.order.id,
                "cancellation_reason": cancellation_reason
            }, status=200)

    except Payment.DoesNotExist:
        logger.warning(f"Payment not found for cancelled intent: {payment_intent_id}")
        return Response({"error": "Payment not found"}, status=404)
    except Exception as e:
        logger.error(f"Error processing payment cancellation: {str(e)}")
        return Response({"error": "Processing failed"}, status=500)


def _handle_checkout_completed(event):
    """Handle completed checkout session"""
    session = event["data"]["object"]
    payment_intent_id = session.get("payment_intent")
    
    if payment_intent_id:
        logger.info(f"Checkout session completed for payment intent: {payment_intent_id}")
        # The payment_intent.succeeded event will handle the actual confirmation
    
    return Response({"status": "success"}, status=200)


def _handle_checkout_expired(event):
    """Handle expired checkout session"""
    session = event["data"]["object"]
    payment_intent_id = session.get("payment_intent")

    if payment_intent_id:
        try:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(stripe_payment_intent_id=payment_intent_id)

                # Validation: Only cancel if payment is still pending
                if payment.status != PaymentStatus.PENDING:
                    logger.info(f"Checkout expired but payment {payment.id} status is {payment.status}, not cancelling")
                    return Response({"status": "ignored"}, status=200)

                # Validation: Check if order is still processing
                if payment.order.status != OrderStatus.PROCESSING:
                    logger.warning(f"Order {payment.order.id} not in processing state during checkout expiry: {payment.order.status}")
                    return Response({"error": "Order not in valid state"}, status=400)

                payment.mark_cancelled()
                logger.info(f"Checkout expired, cancelled payment {payment.id} and order {payment.order.id}")
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for expired checkout: {payment_intent_id}")

    return Response({"status": "success"}, status=200)


def _handle_coupon_created(event):
    """Handle coupon creation from Stripe"""
    from user.models import User

    coupon_data = event["data"]["object"]
    coupon_id = coupon_data["id"]

    try:
        # Check if coupon already exists
        coupon, created = Coupon.objects.get_or_create(
            stripe_coupon_id=coupon_id,
            defaults={
                'user': User.objects.first(),  # Assign to first user for testing - in production, this should be handled differently
                'balance': Decimal(str(coupon_data.get("amount_off", 0))) / 100,  # Convert cents to dollars
                'original_amount': Decimal(str(coupon_data.get("amount_off", 0))) / 100,
                'status': CouponStatus.ACTIVE,
                'description': f"Stripe coupon: {coupon_data.get('name', '')}",
            }
        )

        if created:
            logger.info(f"Created coupon {coupon.id} from Stripe coupon {coupon_id}")
        else:
            logger.info(f"Coupon {coupon.id} already exists for Stripe coupon {coupon_id}")

        return Response({"status": "success", "coupon_id": coupon.id}, status=200)

    except Exception as e:
        logger.error(f"Error processing coupon creation: {str(e)}")
        return Response({"error": "Processing failed"}, status=500)


def _handle_coupon_updated(event):
    """Handle coupon updates from Stripe"""
    coupon_data = event["data"]["object"]
    coupon_id = coupon_data["id"]

    try:
        coupon = Coupon.objects.get(stripe_coupon_id=coupon_id)

        # Update coupon details
        coupon.balance = Decimal(str(coupon_data.get("amount_off", 0))) / 100
        coupon.status = CouponStatus.ACTIVE if not coupon_data.get("deleted", False) else CouponStatus.CANCELLED
        coupon.save()

        logger.info(f"Updated coupon {coupon.id} from Stripe")
        return Response({"status": "success", "coupon_id": coupon.id}, status=200)

    except Coupon.DoesNotExist:
        logger.warning(f"Coupon not found for Stripe coupon {coupon_id}")
        return Response({"error": "Coupon not found"}, status=404)
    except Exception as e:
        logger.error(f"Error processing coupon update: {str(e)}")
        return Response({"error": "Processing failed"}, status=500)


def _handle_coupon_deleted(event):
    """Handle coupon deletion from Stripe"""
    coupon_data = event["data"]["object"]
    coupon_id = coupon_data["id"]

    try:
        coupon = Coupon.objects.get(stripe_coupon_id=coupon_id)
        coupon.status = CouponStatus.CANCELLED
        coupon.save()

        logger.info(f"Marked coupon {coupon.id} as cancelled (deleted in Stripe)")
        return Response({"status": "success", "coupon_id": coupon.id}, status=200)

    except Coupon.DoesNotExist:
        logger.warning(f"Coupon not found for deleted Stripe coupon {coupon_id}")
        return Response({"error": "Coupon not found"}, status=404)
    except Exception as e:
        logger.error(f"Error processing coupon deletion: {str(e)}")
        return Response({"error": "Processing failed"}, status=500)


class StripeTestPageView(View):
    """Render the Stripe test payment page"""
    def get(self, request):
        return render(request, 'stripe_test.html', {
            'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY
        })


class PaymentSuccessView(View):
    """Handle successful payment redirect from Stripe Checkout"""
    def get(self, request):
        session_id = request.GET.get('session_id')
        order = None
        user_email = None
        
        try:
            # Retrieve Stripe session to get order information
            if session_id:
                session = stripe.checkout.Session.retrieve(session_id)
                
                # Get order_id from metadata
                order_id = session.metadata.get('order_id')
                if order_id:
                    order = Order.objects.select_related(
                        'user', 
                        'flight',
                        'flight__arrival_airport',
                        'flight__departure_airport',
                        'flight__airline'
                    ).prefetch_related('tickets').get(id=order_id)
                    user_email = order.user.email if order.user else None
        except Exception as e:
            logger.error(f"Error retrieving order info for session {session_id}: {e}")
        
        return render(request, 'payment_success.html', {
            'session_id': session_id,
            'order': order,
            'user_email': user_email
        })


class PaymentCancelView(View):
    """Handle cancelled payment redirect from Stripe Checkout"""
    def get(self, request):
        order_id = request.GET.get('order_id')
        return render(request, 'payment_cancel.html', {
            'order_id': order_id
        })


@api_view(["POST"])
@permission_classes([AllowAny])
def test_webhook(request, event_type):
    """Test webhook handler without signature verification"""
    # Get the latest payment for testing
    try:
        payment = Payment.objects.filter(status=PaymentStatus.PENDING).latest('created_at')
        payment_intent_id = payment.stripe_payment_intent_id
    except Payment.DoesNotExist:
        return Response({"error": "No pending payments found for testing"}, status=400)

    mock_events = {
        "payment_intent.succeeded": {
            "id": "evt_test_webhook",
            "object": "event",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": payment_intent_id,
                    "amount_received": int(payment.amount * 100)  # Match payment amount in cents
                }
            }
        },
        "payment_intent.canceled": {
            "id": "evt_test_webhook",
            "object": "event",
            "type": "payment_intent.canceled",
            "data": {
                "object": {
                    "id": payment_intent_id,
                    "cancellation_reason": "requested_by_customer"
                }
            }
        },
        "coupon.created": {
            "id": "evt_test_webhook",
            "object": "event",
            "type": "coupon.created",
            "data": {
                "object": {
                    "id": "coupon_test_123",
                    "amount_off": 50000,  # $500.00 in cents
                    "name": "Test Compensation Coupon"
                }
            }
        }
    }

    if event_type not in mock_events:
        return Response({"error": "Invalid event type. Use: payment_intent.succeeded, payment_intent.canceled, or coupon.created"}, status=400)

    # Call the actual webhook handler
    mock_request = type('MockRequest', (), {
        'body': json.dumps(mock_events[event_type]).encode(),
        'META': {},
        'method': 'POST'
    })()

    return stripe_webhook(mock_request)
