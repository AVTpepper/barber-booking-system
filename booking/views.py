from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
from calendar import monthrange
from .models import Booking, Barber
from .forms import BookingForm, CustomUserCreationForm


def send_confirmation_email(booking):
    subject = "Booking Confirmation"
    message = f"Dear {booking.customer.username},\n\nYour booking with {booking.barber.name} on {booking.date} at {booking.time} has been confirmed.\n\nThank you!"
    recipient = [booking.customer.email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient, fail_silently=False)
    
    
def landing_page(request):
    """This is the public landing page for all users."""
    return render(request, 'booking/landing_page.html')


@login_required
def view_bookings(request):
    """View all bookings for the logged-in user"""
    bookings = Booking.objects.filter(customer=request.user)  # Only logged-in user's bookings
    return render(request, 'booking/view_bookings.html', {'bookings': bookings})


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
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.save()
            send_confirmation_email(booking)
            send_admin_notification(booking)
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


def send_admin_notification(booking):
    subject = "New Booking Created"
    message = f"A new booking has been made for {booking.barber.name} on {booking.date} at {booking.time}."
    recipient = ['admin@example.com', booking.barber.email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient, fail_silently=False)


@login_required
def calendar_view(request, year=None, month=None):
    """Display a calendar with bookings for a specific month"""
    today = date.today()

    # Default to the current month if not provided
    year = year or today.year
    month = month or today.month

    # Get the first and last day of the month
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    # Get all bookings for the logged-in user within this month
    bookings = Booking.objects.filter(customer=request.user, date__range=(start_date, end_date))

    # Create a dictionary of bookings grouped by date
    bookings_by_date = {}
    for booking in bookings:
        if booking.date not in bookings_by_date:
            bookings_by_date[booking.date] = []
        bookings_by_date[booking.date].append(booking)

    # Generate a list of days in the month
    days_in_month = range(1, monthrange(year, month)[1] + 1)

    # Get the previous and next months
    prev_month = (start_date - timedelta(days=1)).replace(day=1)
    next_month = (end_date + timedelta(days=1)).replace(day=1)

    context = {
        'year': year,
        'month': month,
        'month_name': start_date.strftime('%B'),
        'days_in_month': days_in_month,  # Pass the range as a list
        'start_date': start_date,
        'bookings_by_date': bookings_by_date,
        'prev_month': prev_month,
        'next_month': next_month,
    }

    return render(request, 'booking/calendar.html', context)