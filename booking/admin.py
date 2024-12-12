from django.contrib import admin
from .models import Barber, Customer, Booking

admin.site.register(Barber)
admin.site.register(Customer)
admin.site.register(Booking)