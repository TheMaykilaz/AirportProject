import stripe
import logging
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

from bookings.models import Order
from .models import Payment, PaymentStatus
from .serializers import PaymentSerializer
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

        payment = Payment.objects.create(order=order, amount=order.total_price)
        intent = payment.create_stripe_payment_intent()
        return Response({
            "payment_id": payment.id,
            "order_id": order.id,
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
            # Create Stripe Checkout Session
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
        elif event_type == "checkout.session.completed":
            return _handle_checkout_completed(event)
        elif event_type == "checkout.session.expired":
            return _handle_checkout_expired(event)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return Response({"status": "ignored", "event_type": event_type}, status=200)
            
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {str(e)}", exc_info=True)
        return Response({"error": "Internal server error"}, status=500)


def _handle_payment_succeeded(event):
    """Handle successful payment intent"""
    payment_intent_id = event["data"]["object"]["id"]
    
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
            
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
    payment_intent_id = event["data"]["object"]["id"]
    failure_reason = event["data"]["object"].get("last_payment_error", {}).get("message", "Unknown")
    
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent_id
            )
            
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
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            if payment.status == PaymentStatus.PENDING:
                payment.mark_cancelled()
                logger.info(f"Checkout expired, cancelled payment {payment.id} and order {payment.order.id}")
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for expired checkout: {payment_intent_id}")
    
    return Response({"status": "success"}, status=200)


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
        return render(request, 'payment_success.html', {
            'session_id': session_id
        })


class PaymentCancelView(View):
    """Handle cancelled payment redirect from Stripe Checkout"""
    def get(self, request):
        order_id = request.GET.get('order_id')
        return render(request, 'payment_cancel.html', {
            'order_id': order_id
        })
