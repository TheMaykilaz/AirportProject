
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction
import stripe
from user.models import User
from .models import (
    Country,
    Airport,
    Airline,
    Airplane,
    Flight,
    FlightSeat,
    Ticket,
    TicketStatus,
    Order,
    OrderStatus,
    Payment
)
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializer,
    FlightSeatSerializer,
    TicketSerializer,
    PaymentSerializer,
    OrderPaymentCreateSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiExample
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly
from AirplaneDJ.settings import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def airlines(self, request, pk=None):
        airport = self.get_object()
        airlines = airport.airlines.all()
        serializer = AirlineSerializer(airlines, many=True)
        return Response(serializer.data)


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def airplanes(self, request, pk=None):
        airline = self.get_object()
        airplanes = airline.airplanes.all()
        serializer = AirplaneSerializer(airplanes, many=True)
        return Response(serializer.data)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["get"], permission_classes=[ReadOnly])
    def flights(self, request, pk=None):
        airplane = self.get_object()
        flights = airplane.flights.all()
        serializer = FlightSerializer(flights, many=True)
        return Response(serializer.data)

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        flight = self.get_object()
        status_value = request.data.get("status")
        if status_value not in dict(Flight.FlightStatus.choices):
            return Response(
                {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )

        flight.status = status_value
        flight.save(update_fields=["status"])
        return Response({"message": f"Flight status updated to {status_value}"})


class FlightSeatViewSet(viewsets.ModelViewSet):
    queryset = FlightSeat.objects.all()
    serializer_class = FlightSeatSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [ReadOnly()]
        return [IsAdmin()]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [ReadOnly()]
        elif self.action in ["create"]:
            return []  # будь-який автентифікований користувач може бронювати
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsSelfOrAdmin()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def cancel(self, request, pk=None):
        ticket = self.get_object()
        with transaction.atomic():
            ticket.status = TicketStatus.CANCELLED
            ticket.save(update_fields=["status"])

            seat = ticket.seat
            if seat.seat_status != FlightSeat.SeatStatus.AVAILABLE:
                seat.seat_status = FlightSeat.SeatStatus.AVAILABLE
                seat.locked_at = None
                seat.save(update_fields=["seat_status", "locked_at"])

        return Response({"message": f"Ticket {ticket.id} has been cancelled"})

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def use(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = TicketStatus.COMPLETED
        ticket.save(update_fields=["status"])
        return Response({"message": f"Ticket {ticket.id} has been used"})

    @action(detail=False, methods=["post"], permission_classes=[])
    def book(self, request):
        order_id = request.data.get("order_id")
        seat_numbers = request.data.get("seat_numbers", [])

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            tickets = Ticket.objects.book_tickets(order, seat_numbers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TestOrderViewSet(viewsets.ViewSet):
    def get_serializer_class(self):
        if self.action == "create_order":
            return OrderPaymentCreateSerializer
        return PaymentSerializer

    @extend_schema(
        request=OrderPaymentCreateSerializer,
        responses={201: PaymentSerializer},
        examples=[
            OpenApiExample(
                "Create order with seat numbers",
                value={
                    "flight_id": 1,
                    "seat_numbers": ["12A", "12B"]
                },
            )
        ]
    )
    @action(detail=False, methods=["post"], url_path="create_order")
    def create_order(self, request):
        serializer = OrderPaymentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        flight = serializer.validated_data['flight_id']
        seat_numbers = serializer.validated_data.get('seat_numbers', [])
        user = request.user if request.user.is_authenticated else None

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                flight=flight,
                status=OrderStatus.PROCESSING,
                total_price=0
            )

            try:
                tickets = Ticket.objects.book_tickets(order, seat_numbers)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={"amount": order.total_price}
            )
            if not created:
                payment.amount = order.total_price
                payment.save(update_fields=["amount"])

            try:
                intent = payment.create_stripe_payment_intent()
            except RuntimeError as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment_serializer = PaymentSerializer(payment)

        return Response({
            "order_id": order.id,
            "tickets": [t.id for t in tickets],
            "stripe_client_secret": intent.get("client_secret"),
            "payment": payment_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="confirm_payment")
    def confirm_payment(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        payment = order.payment
        payment.mark_succeeded()
        return Response({
            "order_status": order.status,
            "payment_status": payment.status
        })

    @action(detail=True, methods=["post"], url_path="cancel_order")
    def cancel_order(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        order.cancel(reason="Test cancel")
        return Response({
            "order_status": order.status,
            "tickets": [{"seat": t.seat.seat_number, "status": t.status} for t in order.tickets.all()]
        })

    @action(detail=True, methods=["get"], url_path="status")
    def status(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        payment = order.payment
        return Response({
            "order_id": order.id,
            "order_status": order.status,
            "payment_status": payment.status,
            "tickets": [{"seat": t.seat.seat_number, "status": t.status, "price": str(t.price)} for t in order.tickets.all()]
        })

    @action(detail=True, methods=["post"], url_path="create_payment_intent")
    def create_payment_intent(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        payment = order.payment
        intent = payment.create_stripe_payment_intent()
        return Response({
            "stripe_client_secret": intent["client_secret"],
            "payment_id": payment.id,
            "payment_status": payment.status
        })
