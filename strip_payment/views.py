import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample

from airport.models import Order
from airport.models import Payment
from .serializers import PaymentSerializer
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly
from AirplaneDJ.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

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


@csrf_exempt
@permission_classes([AllowAny])
@api_view(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return Response(status=400)
    except stripe.error.SignatureVerificationError:
        return Response(status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent["id"])
            payment.mark_succeeded()
        except Payment.DoesNotExist:
            pass

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent["id"])
            payment.mark_failed()
        except Payment.DoesNotExist:
            pass

    return Response(status=200)
