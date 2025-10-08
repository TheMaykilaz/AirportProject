from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, TicketViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
]
