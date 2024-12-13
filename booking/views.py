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


@login_required
def calendar_view(request, year=None, month=None):
    """Display a calendar with bookings for a specific month."""
    today = date.today()

    # Default to current year and month if not provided
    year = year or today.year
    month = month or today.month

    # Get the first day and the number of days in the current month
    first_day_of_month = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]  # Total days in the current month

    # Weekday of the first day of the month (0 = Monday, 6 = Sunday)
    first_weekday = first_day_of_month.weekday()

    # Adjust for Sunday-based calendars (Sunday = 0, Saturday = 6)
    first_weekday = (first_weekday + 1) % 7

    # Calculate the start date (the Sunday before the first day of the month)
    start_date = first_day_of_month - timedelta(days=first_weekday)

    # Calculate the end date (ensure there are 35 slots: 5 rows × 7 columns)
    end_date = start_date + timedelta(days=34)

    # Generate a list of all days to display in the calendar
    calendar_days = []
    current_date = start_date
    while current_date <= end_date:
        calendar_days.append(current_date)
        current_date += timedelta(days=1)

    # Get bookings for the range of dates
    bookings = Booking.objects.filter(customer=request.user, date__range=(start_date, end_date))

    # Group bookings by date
    bookings_by_date = {}
    for booking in bookings:
        if booking.date not in bookings_by_date:
            bookings_by_date[booking.date] = []
        bookings_by_date[booking.date].append(booking)

    # Get the previous and next months
    prev_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
    next_month = (first_day_of_month + timedelta(days=days_in_month)).replace(day=1)

    context = {
        'year': year,
        'month': month,
        'month_name': first_day_of_month.strftime('%B'),
        'calendar_days': calendar_days,
        'bookings_by_date': bookings_by_date,
        'prev_month': prev_month,
        'next_month': next_month,
    }
    return render(request, 'booking/calendar.html', context)


def send_confirmation_email(booking):
    subject = "Booking Confirmation"
    message = f"Dear {booking.customer.username},\n\nYour booking with {booking.barber.name} on {booking.date} at {booking.time} has been confirmed.\n\nThank you!"
    recipient = [booking.customer.email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient, fail_silently=False)
    
    
def landing_page(request):
    """Landing page displaying services and barbers."""
    # Example: Fetch barbers and services from the database
    barbers = Barber.objects.all()
    services = [
        {"name": "Haircut", "description": "Professional haircut tailored to your style."},
        {"name": "Beard Trim", "description": "Expert beard grooming and styling."},
        {"name": "Combo", "description": "Haircut and beard trim package."},
    ]
    context = {
        "barbers": barbers,
        "services": services,
    }
    return render(request, 'booking/landing_page.html', context)


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


