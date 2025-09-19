from rest_framework import serializers
from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from django.contrib.auth import get_user_model

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "slug"]


class AirportSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = Airport
        fields = ["id", "name", "city", "country", "country_id", "slug"]


class AirlineSerializer(serializers.ModelSerializer):
    airport = serializers.StringRelatedField(read_only=True)
    airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="airport", write_only=True
    )

    class Meta:
        model = Airline
        fields = ["id", "name", "airport", "airport_id", "slug"]


class AirplaneSerializer(serializers.ModelSerializer):
    airline = serializers.StringRelatedField(read_only=True)
    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.all(), source="airline", write_only=True
    )

    class Meta:
        model = Airplane
        fields = ["id", "name", "airline", "airline_id"]


class FlightSerializer(serializers.ModelSerializer):
    airplane = serializers.StringRelatedField(read_only=True)
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source="airplane", write_only=True
    )
    origin = serializers.StringRelatedField(read_only=True)
    origin_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="origin", write_only=True
    )
    destination = serializers.StringRelatedField(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="destination", write_only=True
    )

    class Meta:
        model = Flight
        fields = [
            "id", "airplane", "airplane_id", "origin", "origin_id", "destination", "destination_id", "departure_time", "arrival_time", "status",
        ]


class TicketSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=None, source="user", write_only=True
    )
    flight = serializers.StringRelatedField(read_only=True)
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source="flight", write_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            "id", "flight", "flight_id", "user", "user_id", "seat_number", "status", "booked_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.fields["user_id"].queryset = get_user_model().objects.all()
