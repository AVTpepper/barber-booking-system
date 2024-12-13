from django.urls import path
from .views import home, book_appointment, register

urlpatterns = [
    path('', home, name='home'),
    path('book/', book_appointment, name='book_appointment'),
    path('register/', register, name='register'),
]
