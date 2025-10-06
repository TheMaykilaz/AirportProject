from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import timedelta

from .models import Order, Ticket, OrderStatus, TicketStatus
from .serializers import OrderSerializer, TicketSerializer, OrderCreateSerializer
from AirplaneDJ.permissions import IsAdmin, IsSelfOrAdmin, ReadOnly


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsSelfOrAdmin()]
        elif self.action in ["create"]:
            return []  # Any authenticated user can create orders
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsSelfOrAdmin()]
        return [IsAdmin()]

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.cancel(reason="User requested cancellation")
        return Response({
            "message": f"Order {order.id} has been cancelled",
            "status": order.status
        })

    @action(detail=False, methods=["post"], permission_classes=[])
    def create_with_tickets(self, request):
        """Create an order and book tickets in one operation"""
        from .services import BookingService
        
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flight = serializer.validated_data['flight_id']
        seat_numbers = serializer.validated_data.get('seat_numbers', [])
        user = request.user if request.user.is_authenticated else None

        try:
            order = BookingService.create_booking(user, flight, seat_numbers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "order_id": order.id,
            "tickets": [{"id": t.id, "seat": t.seat.seat_number, "price": str(t.price)} for t in order.tickets.all()],
            "total_price": str(order.total_price),
            "status": order.status,
            "reservation_expires_at": order.created_at + timedelta(minutes=15)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def confirm(self, request, pk=None):
        """Confirm booking after payment"""
        from .services import BookingService
        
        order = self.get_object()
        if order.status != OrderStatus.PROCESSING:
            return Response({"error": "Order is not in processing state"}, status=status.HTTP_400_BAD_REQUEST)
        
        BookingService.confirm_booking(order)
        return Response({
            "message": f"Order {order.id} confirmed",
            "status": order.status
        })


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(order__user=self.request.user)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsSelfOrAdmin()]
        elif self.action in ["create"]:
            return []  # Any authenticated user can book tickets
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsSelfOrAdmin()]
        return [IsAdmin()]

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def cancel(self, request, pk=None):
        ticket = self.get_object()
        with transaction.atomic():
            ticket.status = TicketStatus.CANCELLED
            ticket.save(update_fields=["status"])

            seat = ticket.seat
            if seat.seat_status != seat.SeatStatus.AVAILABLE:
                seat.seat_status = seat.SeatStatus.AVAILABLE
                seat.locked_at = None
                seat.save(update_fields=["seat_status", "locked_at"])

        return Response({"message": f"Ticket {ticket.id} has been cancelled"})

    @action(detail=True, methods=["post"], permission_classes=[IsSelfOrAdmin])
    def use(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = TicketStatus.COMPLETED
        ticket.save(update_fields=["status"])
        return Response({"message": f"Ticket {ticket.id} has been used"})
