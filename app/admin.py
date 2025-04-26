from django.contrib import admin
from .models import Region, Category, Organization, TimeSlot, Booking

# Inline tahrirlash uchun TimeSlot
class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 1
    fields = ['start_time', 'duration', 'max_bookings', 'current_bookings', 'is_booked']
    readonly_fields = ['current_bookings']

# Inline tahrirlash uchun Booking
class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ['user', 'status', 'booking_code', 'created_at']
    readonly_fields = ['booking_code', 'created_at']
    can_delete = False

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    date_hierarchy = 'created_at'

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'category', 'address', 'created_at']
    search_fields = ['name', 'address']
    list_filter = ['region', 'category', 'created_at']
    inlines = [TimeSlotInline]
    date_hierarchy = 'created_at'

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['organization', 'start_time', 'duration', 'max_bookings', 'current_bookings', 'is_booked']
    search_fields = ['organization__name']
    list_filter = ['organization', 'is_booked', 'start_time']
    inlines = [BookingInline]
    date_hierarchy = 'start_time'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'time_slot', 'status', 'booking_code', 'created_at']
    search_fields = ['user__username', 'booking_code']
    list_filter = ['status', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['booking_code']