from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from .models import Booking, Barber
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


@login_required
def view_bookings(request):
    """View all bookings for the logged-in user"""
    bookings = Booking.objects.filter(customer=request.user)
    return render(request, 'booking/view_bookings.html', {'bookings': bookings})

@login_required
def create_booking(request):
    """Create a new booking"""
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user  # Associate booking with logged-in user
            booking.save()
            return redirect('view_bookings')
    else:
        form = BookingForm()
    return render(request, 'booking/booking_form.html', {'form': form})

@login_required
def update_booking(request, pk):
    """Update an existing booking"""
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('view_bookings')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'booking/booking_form.html', {'form': form})

@login_required
def delete_booking(request, pk):
    """Delete an existing booking"""
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    if request.method == 'POST':
        booking.delete()
        return redirect('view_bookings')
    return render(request, 'booking/delete_booking.html', {'booking': booking})