from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('home/', views.view_bookings, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('available_time_slots/', views.available_time_slots, name='available_time_slots'),
    path('register/', views.register, name='register'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('booking/update/<int:pk>/', views.update_booking, name='update_booking'),
    path('booking/delete/<int:pk>/', views.delete_booking, name='delete_booking'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('calendar/<int:year>/<int:month>/', views.calendar_view, name='calendar_view_by_month'),
]
