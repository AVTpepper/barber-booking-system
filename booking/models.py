from django.db import models

class Barber(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Booking(models.Model):
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    service = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.customer.name} - {self.date} at {self.time}'
