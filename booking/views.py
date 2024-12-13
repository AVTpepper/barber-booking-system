from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from .models import Booking
from .forms import BookingForm, CustomUserCreationForm


def landing_page(request):
    """This is the public landing page for all users."""
    return render(request, 'booking/landing_page.html')


@login_required
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


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


class CustomLogoutView(LogoutView):
    template_name = 'registration/logout.html'