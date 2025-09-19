from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly

from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializer,
    TicketSerializer,
)

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [ReadOnly()]
        return [IsAdmin()]


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
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
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
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
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
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
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [ReadOnly()]
        return [IsAdmin()]

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        flight = self.get_object()
        status_value = request.data.get("status")
        if status_value not in dict(Flight.Status.choices):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        flight.status = status_value
        flight.save()
        return Response({"message": f"Flight status updated to {status_value}"})


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [ReadOnly()]
        elif self.action in ["create"]:
            return []  # any authenticated user can book
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsSelfOrAdmin()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def cancel(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = Ticket.Status.CANCELLED
        ticket.save()
        return Response({"message": f"Ticket {ticket.id} has been cancelled"})

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def use(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = Ticket.Status.USED
        ticket.save()
        return Response({"message": f"Ticket {ticket.id} has been used"})
