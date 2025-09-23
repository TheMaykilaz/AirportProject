from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Country, Airport, Airline, Airplane, Seat, Flight, Ticket



class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]

class AirportSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "country", "country_id"]


class AirlineSerializer(serializers.ModelSerializer):
    airports = AirportSerializer(many=True, read_only=True)
    airport_ids = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), many=True, source="airports", write_only=True
    )

    class Meta:
        model = Airline
        fields = ["id", "name", "airports", "airport_ids"]

class AirplaneSerializer(serializers.ModelSerializer):
    airline = serializers.StringRelatedField(read_only=True)
    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.all(), source="airline", write_only=True
    )

    class Meta:
        model = Airplane
        fields = ["id", "manufacturer", "model", "airline", "airline_id"]


class SeatSerializer(serializers.ModelSerializer):
    airplane = serializers.StringRelatedField(read_only=True)
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source="airplane", write_only=True
    )

    seat_number = serializers.CharField(source="seat_number", read_only=True)

    class Meta:
        model = Seat
        fields = [
            "id",
            "airplane",
            "airplane_id",
            "row_number",
            "seat_letter",
            "seat_number",
            "seat_class",
            "is_window",
            "is_aisle",
            "is_exit_row",
        ]



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
            "status",
            "base_price",
            "currency_code",
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

    seat = serializers.StringRelatedField(read_only=True)
    seat_id = serializers.PrimaryKeyRelatedField(
        queryset=Seat.objects.all(), source="seat", write_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "flight",
            "flight_id",
            "user",
            "user_id",
            "seat",
            "seat_id",
            "status",
            "final_price",
            "payment_id",
            "created_at",
        ]

   
