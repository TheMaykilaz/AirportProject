"""
Booking and seat management services
"""
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import List, Dict, Optional
from .models import Order, Ticket, OrderStatus, TicketStatus
from airport.models import Flight, FlightSeat


class SeatReservationService:
    """Handles seat reservations with timeout management"""

    RESERVATION_TIMEOUT_MINUTES = 30
    
    @classmethod
    def reserve_seats(cls, flight: Flight, seat_numbers: List[str], user_id: Optional[int] = None) -> List[FlightSeat]:
        """Reserve seats for a limited time"""
        with transaction.atomic():
            # Lock flight to prevent concurrent modifications
            flight = Flight.objects.select_for_update().get(pk=flight.pk)
            
            # Clean up expired reservations first
            cls._cleanup_expired_reservations(flight)
            
            # Check seat availability
            unavailable_seats = FlightSeat.objects.filter(
                flight=flight,
                seat_number__in=seat_numbers
            ).exclude(seat_status=FlightSeat.SeatStatus.AVAILABLE)
            
            if unavailable_seats.exists():
                taken = list(unavailable_seats.values_list('seat_number', flat=True))
                raise ValidationError(f"Seats not available: {', '.join(taken)}")
            
            # Get or create seats and reserve them
            reservation_time = timezone.now()
            reserved_seats = []
            
            for seat_number in seat_numbers:
                seat, created = FlightSeat.objects.get_or_create(
                    flight=flight,
                    seat_number=seat_number,
                    defaults={
                        'seat_status': FlightSeat.SeatStatus.RESERVED,
                        'locked_at': reservation_time,
                    }
                )
                
                if not created:
                    seat.seat_status = FlightSeat.SeatStatus.RESERVED
                    seat.locked_at = reservation_time
                    seat.save(update_fields=['seat_status', 'locked_at'])
                
                reserved_seats.append(seat)
            
            return reserved_seats
    
    @classmethod
    def _cleanup_expired_reservations(cls, flight: Flight):
        """Clean up expired seat reservations"""
        expiry_time = timezone.now() - timedelta(minutes=cls.RESERVATION_TIMEOUT_MINUTES)
        
        FlightSeat.objects.filter(
            flight=flight,
            seat_status=FlightSeat.SeatStatus.RESERVED,
            locked_at__lt=expiry_time
        ).update(
            seat_status=FlightSeat.SeatStatus.AVAILABLE,
            locked_at=None
        )
    
    @classmethod
    def confirm_reservation(cls, seats: List[FlightSeat]):
        """Convert reserved seats to booked"""
        FlightSeat.objects.filter(
            id__in=[seat.id for seat in seats]
        ).update(
            seat_status=FlightSeat.SeatStatus.BOOKED,
            locked_at=timezone.now()
        )
    
    @classmethod
    def release_seats(cls, seats: List[FlightSeat]):
        """Release seats back to available"""
        FlightSeat.objects.filter(
            id__in=[seat.id for seat in seats]
        ).update(
            seat_status=FlightSeat.SeatStatus.AVAILABLE,
            locked_at=None
        )


class PricingService:
    """Simple class-based pricing"""
    
    SEAT_CLASS_MULTIPLIERS = {
        "economy": Decimal("1.00"),
        "premium_economy": Decimal("1.50"),
        "business": Decimal("2.50"),
        "first": Decimal("4.00"),
    }
    
    @classmethod
    def calculate_seat_price(cls, flight: Flight, seat: FlightSeat) -> Decimal:
        """Calculate price based on seat class only"""
        base_price = flight.base_price
        seat_class = cls._get_seat_class(flight.airplane, seat.seat_number)
        
        # Simple class-based multiplier
        class_multiplier = cls.SEAT_CLASS_MULTIPLIERS.get(seat_class, Decimal("1.00"))
        
        final_price = base_price * class_multiplier
        return final_price.quantize(Decimal("0.01"))
    
    @classmethod
    def _get_seat_class(cls, airplane, seat_number: str) -> str:
        """Get seat class from airplane configuration"""
        for seat_config in airplane.seat_map:
            if isinstance(seat_config, dict):
                if seat_config.get("seat_number") == seat_number:
                    return seat_config.get("seat_class", "economy")
            elif str(seat_config) == seat_number:
                return "economy"
        return "economy"


class BookingService:
    """Main booking orchestration service"""
    
    @classmethod
    def create_booking(cls, user, flight: Flight, seat_numbers: List[str]) -> Order:
        """Create a complete booking with seat reservation"""
        with transaction.atomic():
            # Step 1: Reserve seats
            reserved_seats = SeatReservationService.reserve_seats(flight, seat_numbers, user.id if user else None)
            
            # Step 2: Create order
            order = Order.objects.create(
                user=user,
                flight=flight,
                status=OrderStatus.PROCESSING,
                total_price=Decimal("0")
            )
            
            # Step 3: Create tickets and calculate total price
            total_price = Decimal("0")
            tickets = []
            
            for seat in reserved_seats:
                price = PricingService.calculate_seat_price(flight, seat)
                total_price += price
                
                ticket = Ticket.objects.create(
                    order=order,
                    seat=seat,
                    price=price,
                    status=TicketStatus.BOOKED
                )
                tickets.append(ticket)
            
            # Step 4: Update order total
            order.total_price = total_price
            order.save(update_fields=['total_price'])
            
            return order
    
    @classmethod
    def confirm_booking(cls, order: Order):
        """Confirm booking after successful payment"""
        with transaction.atomic():
            seats = [ticket.seat for ticket in order.tickets.all()]
            SeatReservationService.confirm_reservation(seats)
            order.status = OrderStatus.CONFIRMED
            order.save(update_fields=['status'])
    
    @classmethod
    def cancel_booking(cls, order: Order, reason: str = ""):
        """Cancel booking and release seats"""
        with transaction.atomic():
            seats = [ticket.seat for ticket in order.tickets.all()]
            SeatReservationService.release_seats(seats)
            
            order.tickets.update(status=TicketStatus.CANCELLED)
            order.status = OrderStatus.CANCELLED
            order.save(update_fields=['status'])


class SeatMapService:
    """Service for managing seat maps and availability"""
    
    @classmethod
    def get_available_seats(cls, flight: Flight) -> Dict:
        """Get seat map with availability status"""
        # Clean up expired reservations first
        SeatReservationService._cleanup_expired_reservations(flight)
        
        airplane = flight.airplane
        seat_statuses = {
            seat.seat_number: seat.seat_status 
            for seat in FlightSeat.objects.filter(flight=flight)
        }
        
        seat_map = []
        for seat_config in airplane.seat_map:
            if isinstance(seat_config, dict):
                seat_number = seat_config.get("seat_number")
                seat_info = {
                    **seat_config,
                    "status": seat_statuses.get(seat_number, FlightSeat.SeatStatus.AVAILABLE),
                    "price": str(PricingService.calculate_seat_price(flight, 
                        FlightSeat(flight=flight, seat_number=seat_number)))
                }
            else:
                seat_number = str(seat_config)
                seat_info = {
                    "seat_number": seat_number,
                    "seat_class": "economy",
                    "status": seat_statuses.get(seat_number, FlightSeat.SeatStatus.AVAILABLE),
                    "price": str(PricingService.calculate_seat_price(flight,
                        FlightSeat(flight=flight, seat_number=seat_number)))
                }
            seat_map.append(seat_info)
        
        return {
            "flight_id": flight.id,
            "airplane": airplane.model,
            "total_seats": airplane.capacity,
            "available_seats": len([s for s in seat_map if s["status"] == FlightSeat.SeatStatus.AVAILABLE]),
            "seat_map": seat_map
        }
