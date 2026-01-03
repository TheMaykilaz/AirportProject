from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    Country,
    Airport,
    Airline,
    Airplane,
    Flight,
    FlightSeat
)

User = get_user_model()
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "slug"]


class AirportSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city", "timezone", "country", "country_id"]


class AirlineSerializer(serializers.ModelSerializer):
    airports = AirportSerializer(many=True, read_only=True)
    airport_ids = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), many=True, source="airports", write_only=True
    )

    class Meta:
        model = Airline
        fields = ["id", "name", "code", "airports", "airport_ids"]


class AirplaneSerializer(serializers.ModelSerializer):
    airline = serializers.StringRelatedField(read_only=True)
    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.all(), source="airline", write_only=True
    )

    class Meta:
        model = Airplane
        fields = [
            "id",
            "manufacturer",
            "model",
            "registration",
            "airline",
            "airline_id",
            "capacity",
            "seat_map",
        ]


class FlightSeatSerializer(serializers.ModelSerializer):
    flight = serializers.StringRelatedField(read_only=True)
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source="flight", write_only=True
    )

    class Meta:
        model = FlightSeat
        fields = "__all__"


class FlightSerializer(serializers.ModelSerializer):
    airline = serializers.StringRelatedField(read_only=True)
    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.all(), source="airline", write_only=True
    )

    airplane = serializers.StringRelatedField(read_only=True)
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source="airplane", write_only=True
    )

    departure_airport = serializers.StringRelatedField(read_only=True)
    departure_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="departure_airport", write_only=True
    )

    arrival_airport = serializers.StringRelatedField(read_only=True)
    arrival_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="arrival_airport", write_only=True
    )

    flight_seats = FlightSeatSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = [
            "id",
            "airline",
            "airline_id",
            "flight_number",
            "airplane",
            "airplane_id",
            "departure_airport",
            "departure_airport_id",
            "arrival_airport",
            "arrival_airport_id",
            "departure_time",
            "arrival_time",
            "departure_date",
            "status",
            "base_price",
            "gate",
            "actual_departure",
            "actual_arrival",
            "flight_seats",
        ]


class FlightSearchResultSerializer(serializers.Serializer):
    """Serializer for flight search results with pricing information"""
    flight_id = serializers.IntegerField()
    flight_number = serializers.CharField()
    airline_name = serializers.CharField()
    airline_code = serializers.CharField()
    departure_airport_code = serializers.CharField()
    departure_airport_name = serializers.CharField()
    departure_city = serializers.CharField()
    arrival_airport_code = serializers.CharField()
    arrival_airport_name = serializers.CharField()
    arrival_city = serializers.CharField()
    departure_time = serializers.DateTimeField()
    arrival_time = serializers.DateTimeField()
    duration_hours = serializers.FloatField(allow_null=True)
    duration_formatted = serializers.CharField()
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    available_seats = serializers.IntegerField()
    status = serializers.CharField()
    airplane_model = serializers.CharField()


class FlightSearchResponseSerializer(serializers.Serializer):
    """Serializer for complete search response"""
    results = FlightSearchResultSerializer(many=True)
    return_results = FlightSearchResultSerializer(many=True, required=False)
    total_count = serializers.IntegerField()
    price_stats = serializers.DictField(required=False, allow_null=True)
    search_params = serializers.DictField()