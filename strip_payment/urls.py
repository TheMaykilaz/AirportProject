from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, stripe_webhook, test_checkout

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='strip_payments')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('test/checkout/', test_checkout, name='stripe-test-checkout'),
]
