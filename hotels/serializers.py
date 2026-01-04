from rest_framework import serializers
from decimal import Decimal
from django.db.models import Q
from datetime import date, timedelta
from .models import Hotel, RoomType, Room, HotelBooking


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['id', 'name', 'description', 'max_occupancy', 'bed_type', 'room_size_sqm', 'amenities']


class RoomSerializer(serializers.ModelSerializer):
    room_type = RoomTypeSerializer(read_only=True)
    room_type_id = serializers.PrimaryKeyRelatedField(
        queryset=RoomType.objects.all(),
        source='room_type',
        write_only=True
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'hotel', 'hotel_name', 'room_type', 'room_type_id',
            'room_number', 'base_price_per_night', 'is_available',
            'floor', 'view_type'
        ]
        read_only_fields = ['id']


class HotelSerializer(serializers.ModelSerializer):
    nearest_airport_code = serializers.CharField(source='nearest_airport.code', read_only=True)
    nearest_airport_name = serializers.CharField(source='nearest_airport.name', read_only=True)
    room_count = serializers.SerializerMethodField()
    min_price_per_night = serializers.SerializerMethodField()
    
    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'description', 'address', 'city', 'country',
            'postal_code', 'nearest_airport', 'nearest_airport_code',
            'nearest_airport_name', 'distance_from_airport_km', 'phone',
            'email', 'website', 'star_rating', 'amenities', 'images',
            'is_active', 'room_count', 'min_price_per_night',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_room_count(self, obj):
        return obj.rooms.filter(is_available=True).count()
    
    def get_min_price_per_night(self, obj):
        available_rooms = obj.rooms.filter(is_available=True)
        if available_rooms.exists():
            return str(available_rooms.order_by('base_price_per_night').first().base_price_per_night)
        return None


class HotelSearchSerializer(serializers.Serializer):
    """Serializer for hotel search parameters"""
    airport_code = serializers.CharField(required=False, help_text="Airport IATA code")
    city = serializers.CharField(required=False, help_text="City name")
    country = serializers.CharField(required=False, help_text="Country name")
    max_distance_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        help_text="Maximum distance from airport in km"
    )
    min_star_rating = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        help_text="Minimum star rating"
    )
    check_in_date = serializers.DateField(required=False)
    check_out_date = serializers.DateField(required=False)
    number_of_guests = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Number of guests"
    )
    amenities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Required amenities (e.g., ['wifi', 'pool'])"
    )


class HotelBookingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    room_type_name = serializers.CharField(source='room.room_type.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    
    class Meta:
        model = HotelBooking
        fields = [
            'id', 'user', 'hotel', 'hotel_name', 'room', 'room_type_name',
            'room_number', 'check_in_date', 'check_out_date', 'number_of_nights',
            'number_of_guests', 'price_per_night', 'total_price', 'discount_amount',
            'status', 'guest_name', 'guest_email', 'guest_phone', 'special_requests',
            'payment', 'created_at', 'updated_at', 'cancelled_at', 'cancellation_reason'
        ]
        read_only_fields = [
            'id', 'user', 'number_of_nights', 'total_price', 'status',
            'created_at', 'updated_at', 'cancelled_at', 'cancellation_reason'
        ]


class HotelBookingCreateSerializer(serializers.Serializer):
    """Serializer for creating a hotel booking"""
    hotel_id = serializers.PrimaryKeyRelatedField(
        queryset=Hotel.objects.filter(is_active=True),
        source='hotel'
    )
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_available=True),
        source='room'
    )
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    number_of_guests = serializers.IntegerField(min_value=1)
    guest_name = serializers.CharField(max_length=200)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    special_requests = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        check_in = attrs['check_in_date']
        check_out = attrs['check_out_date']
        room = attrs['room']
        number_of_guests = attrs['number_of_guests']
        
        # Validate dates
        if check_in < date.today():
            raise serializers.ValidationError({
                'check_in_date': 'Check-in date cannot be in the past'
            })
        
        if check_out <= check_in:
            raise serializers.ValidationError({
                'check_out_date': 'Check-out date must be after check-in date'
            })
        
        # Validate room capacity
        if number_of_guests > room.room_type.max_occupancy:
            raise serializers.ValidationError({
                'number_of_guests': f'Room can accommodate maximum {room.room_type.max_occupancy} guests'
            })
        
        # Check room availability for the dates
        conflicting_bookings = HotelBooking.objects.filter(
            room=room,
            status__in=[
                HotelBooking.BookingStatus.PENDING,
                HotelBooking.BookingStatus.CONFIRMED,
                HotelBooking.BookingStatus.CHECKED_IN
            ]
        ).filter(
            Q(check_in_date__lt=check_out) & Q(check_out_date__gt=check_in)
        )
        
        if conflicting_bookings.exists():
            raise serializers.ValidationError({
                'room_id': 'Room is not available for the selected dates'
            })
        
        return attrs

