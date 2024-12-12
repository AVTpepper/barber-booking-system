from django.shortcuts import render
from .models import Booking

def home(request):
    bookings = Booking.objects.all()
    return render(request, 'booking/home.html', {'bookings': bookings})
