# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CountryViewSet,
    AirportViewSet,
    AirlineViewSet,
    AirplaneViewSet,
    FlightViewSet,
    FlightSeatViewSet,
    FlightSearchPageView,
)

router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airplanes", AirplaneViewSet, basename="airplane")
router.register(r"flights", FlightViewSet, basename="flight")
router.register(r"seats", FlightSeatViewSet, basename="flightseat")

urlpatterns = [
    path("", include(router.urls)),
    path("search/", FlightSearchPageView.as_view(), name="flight-search-page"),
]
