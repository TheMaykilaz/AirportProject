"""
Hotel booking services and business logic
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal
from .models import Hotel, Room, HotelBooking


class HotelBookingService:
    """Service class for hotel booking operations"""
    
    @classmethod
    def check_room_availability(cls, room: Room, check_in: date, check_out: date) -> bool:
        """Check if a room is available for the given dates"""
        conflicting_bookings = HotelBooking.objects.filter(
            room=room,
            status__in=[
                HotelBooking.BookingStatus.PENDING,
                HotelBooking.BookingStatus.CONFIRMED,
                HotelBooking.BookingStatus.CHECKED_IN
            ]
        ).filter(
            # Check for date overlap
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        )
        
        return not conflicting_bookings.exists()
    
    @classmethod
    def find_available_rooms(cls, hotel: Hotel, check_in: date, check_out: date, 
                            number_of_guests: int = None) -> list:
        """Find available rooms in a hotel for given dates"""
        rooms = hotel.rooms.filter(is_available=True)
        
        if number_of_guests:
            rooms = rooms.filter(room_type__max_occupancy__gte=number_of_guests)
        
        available_rooms = []
        for room in rooms:
            if cls.check_room_availability(room, check_in, check_out):
                available_rooms.append(room)
        
        return available_rooms
    
    @classmethod
    @transaction.atomic
    def create_booking(cls, user, hotel: Hotel, room: Room, check_in: date, 
                      check_out: date, number_of_guests: int, guest_name: str,
                      guest_email: str, guest_phone: str = "", 
                      special_requests: str = "") -> HotelBooking:
        """Create a hotel booking"""
        # Validate dates
        if check_in < date.today():
            raise ValidationError("Check-in date cannot be in the past")
        
        if check_out <= check_in:
            raise ValidationError("Check-out date must be after check-in date")
        
        # Validate room capacity
        if number_of_guests > room.room_type.max_occupancy:
            raise ValidationError(
                f"Room can accommodate maximum {room.room_type.max_occupancy} guests"
            )
        
        # Check availability
        if not cls.check_room_availability(room, check_in, check_out):
            raise ValidationError("Room is not available for the selected dates")
        
        # Calculate pricing
        price_per_night = room.base_price_per_night
        number_of_nights = (check_out - check_in).days
        total_price = price_per_night * number_of_nights
        
        # Create booking
        booking = HotelBooking.objects.create(
            user=user,
            hotel=hotel,
            room=room,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_nights=number_of_nights,
            number_of_guests=number_of_guests,
            price_per_night=price_per_night,
            total_price=total_price,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            special_requests=special_requests,
            status=HotelBooking.BookingStatus.PENDING
        )
        
        return booking
    
    @classmethod
    @transaction.atomic
    def confirm_booking(cls, booking: HotelBooking):
        """Confirm a booking after payment"""
        if booking.status != HotelBooking.BookingStatus.PENDING:
            raise ValidationError("Only pending bookings can be confirmed")
        
        booking.status = HotelBooking.BookingStatus.CONFIRMED
        booking.save(update_fields=['status'])
    
    @classmethod
    @transaction.atomic
    def cancel_booking(cls, booking: HotelBooking, reason: str = ""):
        """Cancel a booking"""
        if booking.status in [
            HotelBooking.BookingStatus.CANCELLED,
            HotelBooking.BookingStatus.CHECKED_OUT
        ]:
            raise ValidationError("Booking cannot be cancelled")
        
        booking.cancel(reason=reason)
    
    @classmethod
    def calculate_total_price(cls, room: Room, check_in: date, check_out: date,
                             discount: Decimal = Decimal('0.00')) -> Decimal:
        """Calculate total price for a booking"""
        number_of_nights = (check_out - check_in).days
        total = room.base_price_per_night * number_of_nights
        return total - discount

