from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from airport.models import Airport


class Hotel(models.Model):
    """Hotel or apartment near airport"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Location - distance from airport
    nearest_airport = models.ForeignKey(
        Airport, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='nearby_hotels',
        help_text="Nearest airport"
    )
    distance_from_airport_km = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        help_text="Distance from airport in kilometers"
    )
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Ratings and amenities
    star_rating = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Hotel star rating (1-5)"
    )
    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of amenities (e.g., ['wifi', 'pool', 'gym', 'parking'])"
    )
    
    # Images
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="List of image URLs"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['nearest_airport', 'is_active']),
            models.Index(fields=['city', 'country']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city} ({self.distance_from_airport_km}km from {self.nearest_airport.code if self.nearest_airport else 'airport'})"


class RoomType(models.Model):
    """Room type (e.g., Single, Double, Suite)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    max_occupancy = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of guests"
    )
    bed_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., '1 King Bed', '2 Twin Beds'"
    )
    room_size_sqm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Room size in square meters"
    )
    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text="Room-specific amenities"
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (max {self.max_occupancy} guests)"


class Room(models.Model):
    """Individual room in a hotel"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='rooms')
    room_number = models.CharField(max_length=20, blank=True)
    
    # Pricing
    base_price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Base price per night"
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    
    # Additional info
    floor = models.IntegerField(null=True, blank=True)
    view_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('city', 'City View'),
            ('ocean', 'Ocean View'),
            ('garden', 'Garden View'),
            ('airport', 'Airport View'),
            ('none', 'No View'),
        ],
        default='none'
    )
    
    class Meta:
        ordering = ['hotel', 'room_number']
        indexes = [
            models.Index(fields=['hotel', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.hotel.name} - {self.room_type.name} ({self.room_number})"


class HotelBooking(models.Model):
    """Hotel booking/reservation"""
    class BookingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked In"
        CHECKED_OUT = "checked_out", "Checked Out"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"
    
    # User and hotel info
    user = models.ForeignKey(
        'user.User',
        on_delete=models.PROTECT,
        related_name='hotel_bookings'
    )
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    
    # Dates
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_nights = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Calculated automatically"
    )
    
    # Guests
    number_of_guests = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of guests"
    )
    
    # Pricing
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per night at time of booking"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total price for all nights"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Any discount applied"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    
    # Guest information
    guest_name = models.CharField(max_length=200)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    special_requests = models.TextField(blank=True)
    
    # Payment reference (link to payment if exists)
    payment = models.ForeignKey(
        'stripe_payment.Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hotel_bookings'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['hotel', 'check_in_date', 'check_out_date']),
            models.Index(fields=['room', 'check_in_date', 'check_out_date']),
        ]
    
    def __str__(self):
        return f"Booking {self.id} - {self.hotel.name} ({self.check_in_date} to {self.check_out_date})"
    
    def save(self, *args, **kwargs):
        # Calculate number of nights
        if self.check_in_date and self.check_out_date:
            delta = self.check_out_date - self.check_in_date
            self.number_of_nights = delta.days
            if self.number_of_nights < 1:
                raise ValueError("Check-out date must be after check-in date")
        
        # Calculate total price
        if self.price_per_night and self.number_of_nights:
            self.total_price = (self.price_per_night * self.number_of_nights) - self.discount_amount
        
        super().save(*args, **kwargs)
    
    def cancel(self, reason=""):
        """Cancel the booking"""
        self.status = self.BookingStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])
    
    def check_in(self):
        """Mark as checked in"""
        if self.status != self.BookingStatus.CONFIRMED:
            raise ValueError("Only confirmed bookings can be checked in")
        self.status = self.BookingStatus.CHECKED_IN
        self.save(update_fields=['status'])
    
    def check_out(self):
        """Mark as checked out"""
        if self.status not in [self.BookingStatus.CONFIRMED, self.BookingStatus.CHECKED_IN]:
            raise ValueError("Only confirmed or checked-in bookings can be checked out")
        self.status = self.BookingStatus.CHECKED_OUT
        self.save(update_fields=['status'])
