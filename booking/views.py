from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Count
from datetime import date, timedelta, datetime
from calendar import monthrange
from .models import Booking, Barber
from .forms import BookingForm, CustomUserCreationForm


def book_appointment(request):
    """Streamlined booking page for selecting service, barber, date, and time."""
    selected_date = request.GET.get("date", None)  # Get the selected date from the query or POST data
    selected_time = request.GET.get("time", None)

    # Annotate each barber with their dynamically calculated available slots
    barbers = Barber.objects.all()
    for barber in barbers:
        # Fetch bookings for the barber on the selected date
        if selected_date:
            bookings = Booking.objects.filter(barber=barber, date=selected_date)
        else:
            bookings = Booking.objects.none()

        # Calculate all possible time slots for the barber
        start_time = barber.start_time
        end_time = barber.end_time
        total_slots = [
            (datetime.combine(date.today(), start_time) + timedelta(minutes=30 * i)).time()
            for i in range(int((end_time.hour - start_time.hour) * 2))
        ]

        # Find the remaining available slots
        booked_slots = [booking.time for booking in bookings]
        barber.available_slots = len([slot for slot in total_slots if slot not in booked_slots])

    # Define the available services
    services = [
        {"id": 1, "name": "Haircut"},
        {"id": 2, "name": "Beard Trim"},
        {"id": 3, "name": "Combo (Haircut + Beard Trim)"},
    ]

    if request.method == "POST":
        service_id = request.POST.get("service")
        barber_id = request.POST.get("barber")
        selected_date = request.POST.get("date")
        time_slot = request.POST.get("time_slot")

        # Create a new booking
        barber = get_object_or_404(Barber, id=barber_id)
        Booking.objects.create(
            customer=request.user,
            barber=barber,
            service=services[int(service_id) - 1]["name"],
            date=selected_date,
            time=time_slot,
        )
        return JsonResponse({"status": "success", "message": "Booking confirmed!"})

    context = {
        "barbers": barbers,
        "services": services,
        "selected_date": selected_date,
        "selected_time": selected_time,
    }
    return render(request, "booking/book_appointment.html", context)

def available_time_slots(request):
    """Fetch available time slots for a barber and date."""
    if request.method == "GET":
        barber_id = request.GET.get("barber_id")
        selected_date = request.GET.get("date")
        barber = get_object_or_404(Barber, id=barber_id)
        bookings = Booking.objects.filter(barber=barber, date=selected_date)

        # Generate all possible time slots (e.g., 9:00 AM to 5:00 PM)
        start_time = barber.start_time
        end_time = barber.end_time
        all_time_slots = [
            (datetime.combine(date.today(), start_time) + timedelta(minutes=30 * i)).time()
            for i in range(int((end_time.hour - start_time.hour) * 2))
        ]

        # Exclude booked time slots
        booked_slots = [b.time for b in bookings]
        available_slots = [slot.strftime("%H:%M") for slot in all_time_slots if slot not in booked_slots]
        return JsonResponse({"available_slots": available_slots})

    
    
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


