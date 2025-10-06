
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction
from user.models import User
from .models import (
    Country,
    Airport,
    Airline,
    Airplane,
    Flight,
    FlightSeat
)
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializer,
    FlightSeatSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiExample
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



