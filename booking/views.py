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
import calendar
from itertools import chain


def fetch_available_dates(request):
    """Fetch available dates for either all barbers or a specific barber."""
    barber_id = request.GET.get("barber_id", None)

    try:
        year = int(request.GET.get("year", date.today().year))
        month = int(request.GET.get("month", date.today().month))
    except ValueError:
        return JsonResponse({"error": "Invalid year or month"}, status=400)

    start_date = date(year, month, 1)
    _, days_in_month = calendar.monthrange(year, month)
    end_date = date(year, month, days_in_month)

    if barber_id:  # Fetch dates for a specific barber
        try:
            barber = Barber.objects.get(id=barber_id)
            print(f"Barber ID: {barber_id}, Year: {year}, Month: {month}")

            working_days = {day[:3]: idx for idx, day in enumerate(calendar.day_name)}
            barber_working_days = [working_days[day] for day in barber.working_days]

            # Calculate available dates for the specific barber
            available_dates = [
                (start_date + timedelta(days=i)).isoformat()
                for i in range((end_date - start_date).days + 1)
                if (start_date + timedelta(days=i)).weekday() in barber_working_days
            ]

            # Exclude fully booked dates
            bookings = Booking.objects.filter(barber=barber, date__range=(start_date, end_date))
            booked_dates = set(booking.date for booking in bookings)

            available_dates = [d for d in available_dates if date.fromisoformat(d) not in booked_dates]

            return JsonResponse({"available_dates": available_dates})

        except Barber.DoesNotExist:
            return JsonResponse({"error": "Barber not found"}, status=404)

    else:  # Fetch combined availability across all barbers
        print(f"Fetching dates for all barbers, Year: {year}, Month: {month}")

        # Find available dates for all barbers
        all_available_dates = set()

        for barber in Barber.objects.all():
            working_days = {day[:3]: idx for idx, day in enumerate(calendar.day_name)}
            barber_working_days = [working_days[day] for day in barber.working_days]

            # Calculate barber's available dates
            barber_available_dates = [
                (start_date + timedelta(days=i)).isoformat()
                for i in range((end_date - start_date).days + 1)
                if (start_date + timedelta(days=i)).weekday() in barber_working_days
            ]

            # Exclude barber's fully booked dates
            bookings = Booking.objects.filter(barber=barber, date__range=(start_date, end_date))
            booked_dates = set(booking.date for booking in bookings)

            barber_available_dates = [d for d in barber_available_dates if date.fromisoformat(d) not in booked_dates]

            # Add to the combined set
            all_available_dates.update(barber_available_dates)

        return JsonResponse({"available_dates": list(all_available_dates)})

    
    
def fetch_barber_availability(request):
    """Fetch availability for a barber on a specific date."""
    barber_id = request.GET.get("barber_id")
    selected_date = request.GET.get("date")

    # Fetch the barber and their bookings for the selected date
    barber = Barber.objects.get(id=barber_id)
    bookings = Booking.objects.filter(barber=barber, date=selected_date)

    # Define barber's working hours
    start_time = barber.start_time  # Assuming Barber model has start_time (e.g., 09:00)
    end_time = barber.end_time  # Assuming Barber model has end_time (e.g., 17:00)

    # Calculate all possible time slots
    total_slots = [
        (datetime.combine(date.today(), start_time) + timedelta(minutes=30 * i)).time()
        for i in range(int((end_time.hour - start_time.hour) * 2))
    ]

    # Adjust for the current day to exclude past time slots
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    if selected_date_obj == datetime.today().date():
        current_time = datetime.now().time()
        total_slots = [slot for slot in total_slots if slot > current_time]

    # Subtract booked slots from total slots
    booked_slots = [booking.time for booking in bookings]
    available_slots = [slot.strftime('%H:%M') for slot in total_slots if slot not in booked_slots]

    return JsonResponse({"available_slots": available_slots})


def book_appointment(request):
    today = date.today()
    selected_date = request.GET.get("date", None)

    if not selected_date:
        selected_date = today.strftime('%Y-%m-%d')

    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    year = selected_date_obj.year
    month = selected_date_obj.month

    first_day_of_month = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    first_weekday = (first_day_of_month.weekday() + 1) % 7

    start_date = first_day_of_month - timedelta(days=first_weekday)
    end_date = start_date + timedelta(days=41)

    calendar_days = []
    current_date = start_date
    week = []

    while current_date <= end_date:
        week.append(current_date)
        if len(week) == 7:
            calendar_days.append(week)
            week = []
        current_date += timedelta(days=1)

    barbers = Barber.objects.all()
    for barber in barbers:
        start_time = barber.start_time
        end_time = barber.end_time

        # Check availability for the next 30 days
        available_dates = []
        for single_date in (today + timedelta(days=i) for i in range(30)):
            total_slots = [
                (datetime.combine(single_date, start_time) + timedelta(minutes=30 * i)).time()
                for i in range(int((end_time.hour - start_time.hour) * 2))
            ]

            # Check for booked slots
            bookings = Booking.objects.filter(barber=barber, date=single_date)
            booked_slots = [b.time for b in bookings]

            # If any slot is available, add the date to available dates
            if any(slot for slot in total_slots if slot not in booked_slots):
                available_dates.append(single_date)

        barber.next_available_date = available_dates[0] if available_dates else None
        barber.is_fully_booked = not bool(available_dates)

    services = [
        {"id": 1, "name": "Haircut"},
        {"id": 2, "name": "Beard Trim"},
        {"id": 3, "name": "Combo (Haircut + Beard Trim)"},
    ]

    context = {
        "barbers": barbers,
        "services": services,
        "selected_date": selected_date,
        "calendar_days": calendar_days,
        "year": year,
        "month": month,
    }
    print(f"Barber: {barber.name}, Fully Booked: {barber.is_fully_booked}, Next Available Date: {barber.next_available_date}")

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


