from decimal import Decimal
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Order, Ticket, TicketStatus, TicketManager
from airport.models import Flight, FlightSeat

User = get_user_model()


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    flight = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'flight', 'status', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


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

    # Price is calculated automatically
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

        # Calculate price by seat class
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


class OrderCreateSerializer(serializers.Serializer):
    flight_id = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())
    seat_numbers = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
