from decimal import Decimal
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
    FlightSeat,
    Ticket,
    TicketStatus,
    TicketManager,
    Payment,
    PaymentStatus
)

User = get_user_model()


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
        fields = [
            "id",
            "manufacturer",
            "model",
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
            "status",
            "base_price",
            "flight_seats",
            "departure_date",
        ]


class TicketSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    seat = serializers.StringRelatedField(read_only=True)
    seat_id = serializers.PrimaryKeyRelatedField(
        queryset=FlightSeat.objects.all(), source="seat", write_only=True
    )

    flight = serializers.StringRelatedField(read_only=True)
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source="flight", write_only=True
    )

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # price обчислюється автоматично
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "order",
            "flight",
            "flight_id",
            "seat",
            "seat_id",
            "status",
            "price",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        flight = attrs.get("flight")
        seat = attrs.get("seat")

        if seat and flight and seat.flight_id != flight.id:
            raise serializers.ValidationError("Selected seat does not belong to the provided flight.")

        if flight and flight.status in [Flight.FlightStatus.DEPARTED, Flight.FlightStatus.CANCELLED]:
            raise serializers.ValidationError(
                f"Cannot create ticket: flight status is '{flight.get_status_display()}'."
            )

        if flight and seat:
            exists = Ticket.objects.filter(
                flight=flight,
                seat=seat,
                status__in=[TicketStatus.BOOKED],
            ).exists()
            if exists:
                raise serializers.ValidationError("This seat is already booked for this flight.")

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        seat = validated_data["seat"]
        flight = validated_data["flight"]

        # Обчислюємо ціну по класу місця
        seat_class = seat.seat_class()
        multiplier = TicketManager.SEAT_CLASS_MULTIPLIERS.get(seat_class, Decimal("1.00"))
        validated_data["price"] = (flight.base_price * multiplier).quantize(Decimal("0.01"))

        try:
            with transaction.atomic():
                ticket = super().create(validated_data)

                if ticket.status == TicketStatus.BOOKED:
                    seat.seat_status = FlightSeat.SeatStatus.BOOKED
                    seat.save(update_fields=["seat_status"])

                return ticket
        except IntegrityError:
            raise serializers.ValidationError(
                {"non_field_errors": ["Database integrity error. Possibly duplicate booking."]}
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, "message_dict") else str(e))

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "amount", "status", "stripe_payment_intent_id", "created_at", "updated_at"]
        read_only_fields = ["status", "stripe_payment_intent_id", "created_at", "updated_at"]

class OrderPaymentCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    flight_id = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())
    seat_numbers = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )