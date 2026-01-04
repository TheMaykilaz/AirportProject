from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Min, F
from django.utils import timezone
from django.views import View
from django.shortcuts import render
from datetime import date, timedelta
from decimal import Decimal

from .models import Hotel, RoomType, Room, HotelBooking
from .serializers import (
    HotelSerializer, RoomSerializer, RoomTypeSerializer,
    HotelBookingSerializer, HotelBookingCreateSerializer,
    HotelSearchSerializer
)
from AirplaneDJ.permissions import IsSelfOrAdmin


class HotelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for hotels - read-only for listing and details"""
    serializer_class = HotelSerializer
    permission_classes = [AllowAny]  # Allow anyone to search hotels
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True).select_related('nearest_airport')
        
        # Filter by airport code
        airport_code = self.request.query_params.get('airport_code', None)
        if airport_code:
            queryset = queryset.filter(nearest_airport__code__iexact=airport_code)
        
        # Filter by city
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by country
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        # Filter by max distance
        max_distance = self.request.query_params.get('max_distance_km', None)
        if max_distance:
            try:
                max_distance = float(max_distance)
                queryset = queryset.filter(distance_from_airport_km__lte=max_distance)
            except ValueError:
                pass
        
        # Filter by min star rating
        min_stars = self.request.query_params.get('min_star_rating', None)
        if min_stars:
            try:
                min_stars = int(min_stars)
                queryset = queryset.filter(star_rating__gte=min_stars)
            except ValueError:
                pass
        
        # Filter by amenities
        amenities = self.request.query_params.getlist('amenities')
        if amenities:
            for amenity in amenities:
                queryset = queryset.filter(amenities__contains=[amenity])
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def search(self, request):
        """Advanced hotel search with availability checking"""
        search_serializer = HotelSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)
        
        data = search_serializer.validated_data
        queryset = Hotel.objects.filter(is_active=True).select_related('nearest_airport')
        
        # Apply filters
        if airport_code := data.get('airport_code'):
            queryset = queryset.filter(nearest_airport__code__iexact=airport_code)
        
        if city := data.get('city'):
            queryset = queryset.filter(city__icontains=city)
        
        if country := data.get('country'):
            queryset = queryset.filter(country__icontains=country)
        
        if max_distance := data.get('max_distance_km'):
            queryset = queryset.filter(distance_from_airport_km__lte=max_distance)
        
        if min_stars := data.get('min_star_rating'):
            queryset = queryset.filter(star_rating__gte=min_stars)
        
        if amenities := data.get('amenities'):
            for amenity in amenities:
                queryset = queryset.filter(amenities__contains=[amenity])
        
        # Check availability if dates provided
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        number_of_guests = data.get('number_of_guests')
        
        if check_in and check_out:
            # Get hotels with available rooms for the dates
            available_hotel_ids = []
            for hotel in queryset:
                available_rooms = hotel.rooms.filter(is_available=True)
                
                if number_of_guests:
                    available_rooms = available_rooms.filter(
                        room_type__max_occupancy__gte=number_of_guests
                    )
                
                # Check for conflicting bookings
                for room in available_rooms:
                    conflicting = HotelBooking.objects.filter(
                        room=room,
                        status__in=[
                            HotelBooking.BookingStatus.PENDING,
                            HotelBooking.BookingStatus.CONFIRMED,
                            HotelBooking.BookingStatus.CHECKED_IN
                        ]
                    ).filter(
                        Q(check_in_date__lt=check_out) & Q(check_out_date__gt=check_in)
                    )
                    
                    if not conflicting.exists():
                        available_hotel_ids.append(hotel.id)
                        break
            
            queryset = queryset.filter(id__in=available_hotel_ids)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def rooms(self, request, pk=None):
        """Get available rooms for a hotel"""
        hotel = self.get_object()
        check_in = request.query_params.get('check_in_date')
        check_out = request.query_params.get('check_out_date')
        number_of_guests = request.query_params.get('number_of_guests')
        
        rooms = hotel.rooms.filter(is_available=True)
        
        if number_of_guests:
            try:
                number_of_guests = int(number_of_guests)
                rooms = rooms.filter(room_type__max_occupancy__gte=number_of_guests)
            except ValueError:
                pass
        
        # Filter by availability for dates
        if check_in and check_out:
            try:
                check_in_date = date.fromisoformat(check_in)
                check_out_date = date.fromisoformat(check_out)
                
                available_room_ids = []
                for room in rooms:
                    conflicting = HotelBooking.objects.filter(
                        room=room,
                        status__in=[
                            HotelBooking.BookingStatus.PENDING,
                            HotelBooking.BookingStatus.CONFIRMED,
                            HotelBooking.BookingStatus.CHECKED_IN
                        ]
                    ).filter(
                        Q(check_in_date__lt=check_out_date) & Q(check_out_date__gt=check_in_date)
                    )
                    
                    if not conflicting.exists():
                        available_room_ids.append(room.id)
                
                rooms = rooms.filter(id__in=available_room_ids)
            except ValueError:
                pass
        
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)


class RoomTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for room types"""
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    permission_classes = [AllowAny]


class HotelBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for hotel bookings"""
    serializer_class = HotelBookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return HotelBooking.objects.all().select_related('hotel', 'room', 'user')
        return HotelBooking.objects.filter(user=self.request.user).select_related('hotel', 'room')
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsSelfOrAdmin()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_booking(self, request):
        """Create a hotel booking"""
        create_serializer = HotelBookingCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        
        validated_data = create_serializer.validated_data
        room = validated_data['room']
        
        # Get price per night
        price_per_night = room.base_price_per_night
        
        # Create booking
        booking = HotelBooking.objects.create(
            user=request.user,
            hotel=validated_data['hotel'],
            room=room,
            check_in_date=validated_data['check_in_date'],
            check_out_date=validated_data['check_out_date'],
            number_of_guests=validated_data['number_of_guests'],
            price_per_night=price_per_night,
            guest_name=validated_data['guest_name'],
            guest_email=validated_data['guest_email'],
            guest_phone=validated_data.get('guest_phone', ''),
            special_requests=validated_data.get('special_requests', ''),
            status=HotelBooking.BookingStatus.PENDING
        )
        
        serializer = HotelBookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsSelfOrAdmin])
    def cancel(self, request, pk=None):
        """Cancel a hotel booking"""
        booking = self.get_object()
        
        if booking.status in [HotelBooking.BookingStatus.CANCELLED, HotelBooking.BookingStatus.CHECKED_OUT]:
            return Response(
                {"error": "Booking cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        booking.cancel(reason=reason)
        
        serializer = HotelBookingSerializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsSelfOrAdmin])
    def confirm(self, request, pk=None):
        """Confirm a hotel booking (after payment)"""
        booking = self.get_object()
        
        if booking.status != HotelBooking.BookingStatus.PENDING:
            return Response(
                {"error": "Only pending bookings can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = HotelBooking.BookingStatus.CONFIRMED
        booking.save(update_fields=['status'])
        
        serializer = HotelBookingSerializer(booking)
        return Response(serializer.data)


class HotelsSearchView(View):
    """Display hotels search page (similar to Aviasales/Booking.com)"""
    def get(self, request):
        airport_code = request.GET.get('airport_code', '')
        max_distance = request.GET.get('max_distance_km', '10')
        min_star_rating = request.GET.get('min_star_rating', '')
        city = request.GET.get('city', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        amenities = request.GET.getlist('amenities')
        
        # Get hotels
        hotels = Hotel.objects.filter(is_active=True).select_related('nearest_airport').prefetch_related('rooms')
        
        if airport_code:
            hotels = hotels.filter(nearest_airport__code__iexact=airport_code)
        
        if city:
            hotels = hotels.filter(city__icontains=city)
        
        if max_distance:
            try:
                max_distance = float(max_distance)
                hotels = hotels.filter(distance_from_airport_km__lte=max_distance)
            except ValueError:
                pass
        
        if min_star_rating:
            try:
                min_star_rating = int(min_star_rating)
                hotels = hotels.filter(star_rating__gte=min_star_rating)
            except ValueError:
                pass
        
        # Filter by amenities
        if amenities:
            for amenity in amenities:
                hotels = hotels.filter(amenities__contains=[amenity])
        
        # Annotate with min price
        hotels = hotels.annotate(
            min_price=Min('rooms__base_price_per_night')
        ).distinct()
        
        # Filter by price range
        if min_price:
            try:
                min_price = float(min_price)
                hotels = hotels.filter(min_price__gte=min_price)
            except ValueError:
                pass
        
        if max_price:
            try:
                max_price = float(max_price)
                hotels = hotels.filter(min_price__lte=max_price)
            except ValueError:
                pass
        
        # Get airport name if airport_code is provided
        airport_name = None
        if airport_code:
            from airport.models import Airport
            try:
                airport = Airport.objects.get(code__iexact=airport_code)
                airport_name = airport.name
            except Airport.DoesNotExist:
                pass
        
        return render(request, 'hotels_search.html', {
            'hotels': hotels,
            'airport_code': airport_code,
            'airport_name': airport_name,
            'max_distance': max_distance,
            'min_star_rating': min_star_rating,
            'city': city,
            'request': request,  # Pass request for GET parameters
        })
