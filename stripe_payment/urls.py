from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    CouponViewSet,
    stripe_webhook,
    test_webhook,
    StripeTestPageView,
    PaymentSuccessView,
    PaymentCancelView,
    create_hotel_checkout_session,
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='stripe_payments')
router.register(r'coupons', CouponViewSet, basename='coupons')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('test-webhook/<str:event_type>/', test_webhook, name='test-webhook'),
    path('test/', StripeTestPageView.as_view(), name='stripe-test-page'),
    path('success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('cancel/', PaymentCancelView.as_view(), name='payment-cancel'),
    path('hotel-checkout/', create_hotel_checkout_session, name='hotel-checkout'),
]
