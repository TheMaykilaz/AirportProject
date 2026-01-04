from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HotelViewSet, RoomTypeViewSet, HotelBookingViewSet, HotelsSearchView

router = DefaultRouter()
router.register(r'hotels', HotelViewSet, basename='hotel')
router.register(r'room-types', RoomTypeViewSet, basename='room-type')
router.register(r'bookings', HotelBookingViewSet, basename='hotel-booking')

urlpatterns = [
    path('', include(router.urls)),
]
