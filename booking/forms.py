from django import forms
from .models import Booking
from django.contrib.auth.models import User

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['barber', 'date', 'time', 'service']

    def clean(self):
        cleaned_data = super().clean()
        barber = cleaned_data.get('barber')
        time = cleaned_data.get('time')

        if barber and time:
            if time < barber.start_time or time > barber.end_time:
                raise forms.ValidationError(f"{barber.name} is not available at the selected time.")
        return cleaned_data


class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())