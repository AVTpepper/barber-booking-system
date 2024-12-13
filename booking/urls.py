from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('home/', views.view_bookings, name='home'),
    path('book/', views.create_booking, name='book_appointment'),
    path('register/', views.register, name='register'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('booking/update/<int:pk>/', views.update_booking, name='update_booking'),
    path('booking/delete/<int:pk>/', views.delete_booking, name='delete_booking'),
]
