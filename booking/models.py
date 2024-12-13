from django.contrib.auth.models import User
from django.db import models
from multiselectfield import MultiSelectField


DAYS_OF_WEEK = [
    ('Mon', 'Monday'),
    ('Tue', 'Tuesday'),
    ('Wed', 'Wednesday'),
    ('Thu', 'Thursday'),
    ('Fri', 'Friday'),
    ('Sat', 'Saturday'),
    ('Sun', 'Sunday'),
]


class Barber(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    start_time = models.TimeField(default="09:00:00")  
    end_time = models.TimeField(default="17:00:00")    
    working_days = MultiSelectField(choices=DAYS_OF_WEEK, default=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])

    def __str__(self):
        return self.name



class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Booking(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to Django's User model
    barber = models.ForeignKey('Barber', on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    service = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.customer.username} - {self.date} at {self.time}'
