from django.contrib import admin
from .models import Guest, Room, Booking, Service, AdditionalCharge

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'passport')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'building', 'floor', 'category', 'base_price', 'status')
    list_filter = ('category', 'status', 'building')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'room', 'check_in', 'check_out', 'status', 'total_price')
    date_hierarchy = 'check_in'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')

@admin.register(AdditionalCharge)
class AdditionalChargeAdmin(admin.ModelAdmin):
    list_display = ('booking', 'service', 'quantity', 'date')
