from django.shortcuts import render, redirect
from .models import Booking
from .forms import BookingForm

def home(request):
    bookings = Booking.objects.all()
    return render(request, 'booking/home.html', {'bookings': bookings})


def book_appointment(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = BookingForm()
    return render(request, 'booking/booking_form.html', {'form': form})