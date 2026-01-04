from django.contrib import admin
from .models import Hotel, RoomType, Room, HotelBooking


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'nearest_airport', 'distance_from_airport_km', 'star_rating', 'is_active']
    list_filter = ['is_active', 'star_rating', 'nearest_airport', 'city']
    search_fields = ['name', 'city', 'address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_occupancy', 'bed_type']
    search_fields = ['name']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'room_type', 'room_number', 'base_price_per_night', 'is_available']
    list_filter = ['hotel', 'is_available', 'room_type', 'view_type']
    search_fields = ['hotel__name', 'room_number']


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'hotel', 'user', 'check_in_date', 'check_out_date', 'status', 'total_price']
    list_filter = ['status', 'hotel', 'check_in_date']
    search_fields = ['user__email', 'guest_name', 'hotel__name']
    readonly_fields = ['created_at', 'updated_at', 'cancelled_at', 'number_of_nights', 'total_price']
    date_hierarchy = 'check_in_date'
