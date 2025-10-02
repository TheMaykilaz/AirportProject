from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet, 
    stripe_webhook, 
    StripeTestPageView,
    PaymentSuccessView,
    PaymentCancelView
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='stripe_payments')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('test/', StripeTestPageView.as_view(), name='stripe-test-page'),
    path('success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('cancel/', PaymentCancelView.as_view(), name='payment-cancel'),
]
