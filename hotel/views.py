from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from datetime import date
from .models import Guest, Room, Booking, Service, AdditionalCharge
from .forms import BookingForm

def booking_list(request):
    bookings = Booking.objects.select_related('guest', 'room').all()
    return render(request, 'hotel/booking_list.html', {'bookings': bookings})

def booking_create(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            messages.success(request, f'Бронь №{booking.id} создана.')
            return redirect('booking_detail', pk=booking.id)
    else:
        form = BookingForm()
    return render(request, 'hotel/booking_form.html', {'form': form})

def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('guest', 'room'), pk=pk)
    charges = AdditionalCharge.objects.filter(booking=booking).select_related('service')
    services = Service.objects.all()
    return render(request, 'hotel/booking_detail.html', {'booking': booking, 'charges': charges, 'services': services})

@require_POST
def booking_checkin(request, pk):
    booking = get_object_or_404(Booking, pk=pk, status='confirmed')
    booking.status = 'checked_in'
    booking.room.status = 'occupied'
    booking.room.save()
    booking.save()
    messages.success(request, f'{booking.guest.full_name} заселён.')
    return redirect('booking_detail', pk=pk)

@require_POST
def booking_checkout(request, pk):
    booking = get_object_or_404(Booking, pk=pk, status='checked_in')
    booking.status = 'checked_out'
    booking.room.status = 'cleaning'
    booking.room.save()
    booking.save()
    messages.success(request, f'{booking.guest.full_name} выехал. Номер переведён в уборку.')
    return redirect('booking_detail', pk=pk)

@require_POST
def add_charge(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    service_id = request.POST.get('service_id')
    quantity = int(request.POST.get('quantity', 1))
    charge_date = request.POST.get('date', date.today().isoformat())
    service = get_object_or_404(Service, pk=service_id)
    AdditionalCharge.objects.create(booking=booking, service=service, quantity=quantity, date=charge_date)
    messages.success(request, f'Услуга "{service.name}" добавлена.')
    return redirect('booking_detail', pk=pk)

@require_POST
def check_availability(request):
    import json
    data = json.loads(request.body)
    check_in = data.get('check_in')
    check_out = data.get('check_out')
    category = data.get('category')
    if not check_in or not check_out:
        return JsonResponse({'error': 'Не указаны даты'}, status=400)
    busy = Booking.objects.filter(check_in__lt=check_out, check_out__gt=check_in).exclude(status__in=['cancelled', 'checked_out']).values_list('room_id', flat=True)
    rooms = Room.objects.filter(status='free').exclude(id__in=busy)
    if category:
        rooms = rooms.filter(category=category)
    room_list = [{'id': r.id, 'number': r.number, 'building': r.building, 'floor': r.floor, 'category': r.get_category_display(), 'price': str(r.base_price)} for r in rooms]
    return JsonResponse({'rooms': room_list})
