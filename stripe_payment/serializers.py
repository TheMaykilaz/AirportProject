from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Payment, Coupon, CouponStatus


class PaymentSerializer(serializers.ModelSerializer):
    coupon = serializers.PrimaryKeyRelatedField(
        queryset=Coupon.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "coupon",
            "amount",
            "discount_amount",
            "currency",
            "stripe_payment_intent_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["amount", "discount_amount", "stripe_payment_intent_id", "status", "created_at", "updated_at"]


class CouponSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        required=False,
        default=serializers.CurrentUserDefault()
    )
    is_usable = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "user",
            "balance",
            "original_amount",
            "stripe_coupon_id",
            "status",
            "expires_at",
            "description",
            "is_usable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["stripe_coupon_id", "created_at", "updated_at"]

    def get_is_usable(self, obj):
        return obj.is_usable()
