from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "amount",
            "currency",
            "stripe_payment_intent_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["stripe_payment_intent_id", "status", "created_at", "updated_at"]
