from django.contrib import admin
from .models import Barber, Customer, Booking


admin.site.register(Customer)
admin.site.register(Booking)

@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'start_time', 'end_time', 'working_days')
    list_filter = ('specialization',)
    search_fields = ('name',)