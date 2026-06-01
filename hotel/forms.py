from django import forms
from django.core.exceptions import ValidationError
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest', 'room', 'check_in', 'check_out', 'meal_plan']
        widgets = {'check_in': forms.DateInput(attrs={'type': 'date'}), 'check_out': forms.DateInput(attrs={'type': 'date'})}
    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        room = cleaned_data.get('room')
        if check_in and check_out and check_out <= check_in:
            raise ValidationError("Дата выезда должна быть позже даты заезда.")
        if check_in and check_out and room:
            overlapping = Booking.objects.filter(room=room, check_in__lt=check_out, check_out__gt=check_in).exclude(status__in=['cancelled', 'checked_out'])
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise ValidationError("Номер уже занят в эти даты.")
        return cleaned_data
