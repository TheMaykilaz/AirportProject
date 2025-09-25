
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    Country,
    Airport,
    Airline,
    Airplane,
    Flight,
    FlightSeat,
    Ticket,
    Order,
    TicketStatus,
    Order,
    OrderStatus
)
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializer,
    FlightSeatSerializer,
    TicketSerializer,
)
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly

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
    @action(detail=False, methods=["post"])
    def create_order(self, request):
        user = request.user if request.user.is_authenticated else None
        flight_id = request.data.get("flight_id")
        seat_numbers = request.data.get("seat_numbers", [])

        if not flight_id:
            return Response({"error": "flight_id is required"}, status=400)

        try:
            flight = Flight.objects.get(id=flight_id)
        except Flight.DoesNotExist:
            return Response({"error": "Flight not found"}, status=404)

        # Створюємо Order
        order = Order.objects.create(
            user=user,
            flight=flight,
            status=OrderStatus.PROCESSING,
            total_price=0
        )

        # Бронюємо квитки через TicketManager
        try:
            tickets = Ticket.objects.book_tickets(order, seat_numbers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)

        serializer = TicketSerializer(tickets, many=True)
        return Response({
            "order_id": order.id,
            "tickets": serializer.data
        }, status=201)

    @action(detail=False, methods=["get"])
    def test_order(self, request):
        orders = Order.objects.all()[:5]
        data = []
        for o in orders:
            data.append({
                "order_id": o.id,
                "user": str(o.user),
                "flight": str(o.flight),
                "status": o.status,
                "total_price": o.total_price,
                "tickets": [str(t) for t in o.tickets.all()]
            })
        return Response(data)
