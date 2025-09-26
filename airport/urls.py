# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet,
    AirportViewSet,
    AirlineViewSet,
    AirplaneViewSet,
    FlightViewSet,
    TicketViewSet,
    FlightSeatViewSet,
    TestOrderViewSet,
)

router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airplanes", AirplaneViewSet, basename="airplane")
router.register(r"flights", FlightViewSet, basename="flight")
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"seats", FlightSeatViewSet, basename="flightseat")
router.register(r"test-order", TestOrderViewSet, basename="test-order")

urlpatterns = [
    path("", include(router.urls)),
]
