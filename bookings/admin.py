from django.contrib import admin
from .models import Order, Ticket


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'flight', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'flight__flight_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'seat', 'price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'seat__seat_number']
    readonly_fields = ['created_at', 'updated_at']
