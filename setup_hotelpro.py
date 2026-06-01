#!/usr/bin/env python3
"""
Автоматический установщик проекта HotelPro.
Создаёт структуру Django-проекта с приложением hotel,
устанавливает зависимости и запускает сервер.
"""

import os
import subprocess
import sys
import venv
from pathlib import Path

# ---------- Конфигурация ----------
PROJECT_NAME = "hotelpro"
APP_NAME = "hotel"
DJANGO_VERSION = "django==4.2"

def run_cmd(cmd, cwd=None):
    """Выполняет команду и выводит результат."""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Ошибка при выполнении: {cmd}")
    print(result.stdout)
    return result.stdout

def create_venv():
    """Создаёт виртуальное окружение .venv в текущей папке."""
    venv_path = Path.cwd() / ".venv"
    if not venv_path.exists():
        print("Создание виртуального окружения .venv ...")
        venv.create(venv_path, with_pip=True)
    else:
        print("Виртуальное окружение уже существует.")
    # Определяем путь к python внутри venv
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    return str(python_exe), str(pip_exe)

def install_django(pip_exe):
    """Устанавливает Django в виртуальное окружение."""
    print("Установка Django...")
    run_cmd(f'"{pip_exe}" install {DJANGO_VERSION}')

def create_project_structure(python_exe):
    """Создаёт проект Django и приложение hotel."""
    # Удаляем старый manage.py, если есть, чтобы избежать конфликта
    if Path("manage.py").exists():
        print("Удаление старого manage.py...")
        Path("manage.py").unlink()
    if Path(PROJECT_NAME).exists():
        print(f"Папка {PROJECT_NAME} уже существует. Будет использована существующая структура.")
    else:
        print("Создание проекта Django...")
        run_cmd(f'"{python_exe}" -m django startproject {PROJECT_NAME} .')
    # Создание приложения hotel
    if Path(APP_NAME).exists():
        print(f"Приложение {APP_NAME} уже существует. Пропускаем.")
    else:
        print(f"Создание приложения {APP_NAME}...")
        run_cmd(f'"{python_exe}" manage.py startapp {APP_NAME}')

def write_app_files():
    """Перезаписывает файлы приложения hotel нашими (с моделями, вьюхами и т.д.)."""
    # Определяем содержимое файлов (можно взять из вашего предыдущего кода)
    models_py = '''"""
Модели данных для гостиницы HotelPro.
"""
from django.db import models
from django.core.validators import RegexValidator

class Guest(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ФИО")
    phone = models.CharField(max_length=20, validators=[RegexValidator(r'^\\+7\\d{10}$', message="Формат: +7XXXXXXXXXX")], verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    passport = models.CharField(max_length=10, validators=[RegexValidator(r'^\\d{10}$', message="10 цифр без пробелов")], verbose_name="Паспорт")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Гость"
        verbose_name_plural = "Гости"
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

class Room(models.Model):
    STATUS_CHOICES = [('free', 'Свободен'), ('occupied', 'Занят'), ('cleaning', 'Уборка'), ('maintenance', 'Ремонт')]
    CATEGORY_CHOICES = [('std', 'Стандарт'), ('semi', 'Полулюкс'), ('lux', 'Люкс')]
    building = models.PositiveSmallIntegerField(verbose_name="Корпус")
    floor = models.PositiveSmallIntegerField(verbose_name="Этаж")
    number = models.CharField(max_length=10, verbose_name="Номер комнаты")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, verbose_name="Категория")
    capacity = models.PositiveSmallIntegerField(default=1, verbose_name="Вместимость")
    base_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена за ночь")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='free', verbose_name="Статус")

    class Meta:
        verbose_name = "Номер"
        verbose_name_plural = "Номера"
        ordering = ['building', 'floor', 'number']

    def __str__(self):
        return f"{self.number} ({self.get_category_display()})"

class Booking(models.Model):
    MEAL_CHOICES = [('none', 'Без питания'), ('breakfast', 'Завтрак'), ('full', 'Полный пансион')]
    STATUS_CHOICES = [('confirmed', 'Подтверждено'), ('checked_in', 'Заселено'), ('checked_out', 'Выехало'), ('cancelled', 'Отменено')]
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, verbose_name="Гость")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Номер")
    check_in = models.DateField(verbose_name="Дата заезда")
    check_out = models.DateField(verbose_name="Дата выезда")
    meal_plan = models.CharField(max_length=10, choices=MEAL_CHOICES, default='none', verbose_name="Питание")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='confirmed', verbose_name="Статус")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Стоимость")

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-check_in']

    def save(self, *args, **kwargs):
        if not self.total_price:
            nights = (self.check_out - self.check_in).days
            self.total_price = self.room.base_price * nights
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Бронь {self.id}: {self.guest.full_name} ({self.check_in} - {self.check_out})"

class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")
    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
    def __str__(self):
        return self.name

class AdditionalCharge(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, verbose_name="Бронь")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Услуга")
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Количество")
    date = models.DateField(verbose_name="Дата начисления")
    class Meta:
        verbose_name = "Начисление услуги"
        verbose_name_plural = "Начисления услуг"
    def __str__(self):
        return f"{self.service.name} x{self.quantity} к брони {self.booking.id}"
'''

    forms_py = '''from django import forms
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
'''

    views_py = '''from django.shortcuts import render, get_object_or_404, redirect
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
'''

    admin_py = '''from django.contrib import admin
from .models import Guest, Room, Booking, Service, AdditionalCharge

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'passport')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'building', 'floor', 'category', 'base_price', 'status')
    list_filter = ('category', 'status', 'building')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'room', 'check_in', 'check_out', 'status', 'total_price')
    date_hierarchy = 'check_in'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')

@admin.register(AdditionalCharge)
class AdditionalChargeAdmin(admin.ModelAdmin):
    list_display = ('booking', 'service', 'quantity', 'date')
'''

    urls_app_py = '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.booking_list, name='booking_list'),
    path('create/', views.booking_create, name='booking_create'),
    path('check-availability/', views.check_availability, name='check_availability'),
    path('<int:pk>/', views.booking_detail, name='booking_detail'),
    path('<int:pk>/checkin/', views.booking_checkin, name='booking_checkin'),
    path('<int:pk>/checkout/', views.booking_checkout, name='booking_checkout'),
    path('<int:pk>/add-charge/', views.add_charge, name='add_charge'),
]
'''

    # Шаблоны
    base_html = '''<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>{% block title %}HotelPro{% endblock %}</title>
<style>body { font-family: Arial, sans-serif; margin: 20px; } nav { margin-bottom: 20px; } nav a { margin-right: 10px; } .messages { color: green; } .error { color: red; } table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #aaa; padding: 6px; text-align: left; }</style>
</head>
<body>
<nav><a href="{% url 'booking_list' %}">Главная</a> <a href="{% url 'booking_create' %}">Новая бронь</a> <a href="/admin/">Админка</a></nav>
{% if messages %}<ul class="messages">{% for message in messages %}<li{% if message.tags %} class="{{ message.tags }}"{% endif %}>{{ message }}</li>{% endfor %}</ul>{% endif %}
{% block content %}{% endblock %}
</body>
</html>
'''

    booking_list_html = '''{% extends "hotel/base.html" %}
{% block title %}Список бронирований{% endblock %}
{% block content %}
<h1>Бронирования</h1>
<table><tr><th>ID</th><th>Гость</th><th>Номер</th><th>Дата заезда</th><th>Дата выезда</th><th>Статус</th><th>Сумма</th></tr>
{% for b in bookings %}
<tr><td><a href="{% url 'booking_detail' b.id %}">{{ b.id }}</a></td><td>{{ b.guest.full_name }}</td><td>{{ b.room.number }}</td><td>{{ b.check_in }}</td><td>{{ b.check_out }}</td><td>{{ b.get_status_display }}</td><td>{{ b.total_price }}</td></tr>
{% endfor %}
</table>
{% endblock %}
'''

    booking_form_html = '''{% extends "hotel/base.html" %}
{% block title %}Новая бронь{% endblock %}
{% block content %}
<h1>Создание бронирования</h1>
<form method="post">{% csrf_token %}{{ form.as_p }}<button type="submit">Сохранить</button></form>
{% endblock %}
'''

    booking_detail_html = '''{% extends "hotel/base.html" %}
{% block title %}Бронь №{{ booking.id }}{% endblock %}
{% block content %}
<h1>Бронь №{{ booking.id }}</h1>
<p><strong>Гость:</strong> {{ booking.guest.full_name }}</p>
<p><strong>Номер:</strong> {{ booking.room.number }} ({{ booking.room.get_category_display }})</p>
<p><strong>Даты:</strong> {{ booking.check_in }} – {{ booking.check_out }}</p>
<p><strong>Статус:</strong> {{ booking.get_status_display }}</p>
<p><strong>Питание:</strong> {{ booking.get_meal_plan_display }}</p>
<p><strong>Стоимость:</strong> {{ booking.total_price }} ₽</p>

<h3>Услуги</h3>
<ul>
{% for charge in charges %}
<li>{{ charge.date }} – {{ charge.service.name }} x{{ charge.quantity }} ({{ charge.service.price }} ₽/ед.)</li>
{% empty %}<li>Нет дополнительных услуг</li>{% endfor %}
</ul>

{% if booking.status == 'confirmed' %}
<form method="post" action="{% url 'booking_checkin' booking.id %}">{% csrf_token %}<button type="submit">Заселить</button></form>
{% elif booking.status == 'checked_in' %}
<form method="post" action="{% url 'booking_checkout' booking.id %}">{% csrf_token %}<button type="submit">Выселить</button></form>
<h3>Добавить услугу</h3>
<form method="post" action="{% url 'add_charge' booking.id %}">{% csrf_token %}
<select name="service_id">{% for s in services %}<option value="{{ s.id }}">{{ s.name }} ({{ s.price }} ₽)</option>{% endfor %}</select>
<input type="number" name="quantity" value="1" min="1">
<input type="date" name="date" value="{% now 'Y-m-d' %}">
<button type="submit">Добавить</button>
</form>
{% endif %}
<a href="{% url 'booking_list' %}">Назад к списку</a>
{% endblock %}
'''

    # Запись файлов
    app_dir = Path(APP_NAME)
    (app_dir / "models.py").write_text(models_py)
    (app_dir / "forms.py").write_text(forms_py)
    (app_dir / "views.py").write_text(views_py)
    (app_dir / "admin.py").write_text(admin_py)
    (app_dir / "urls.py").write_text(urls_app_py)

    templates_dir = app_dir / "templates" / "hotel"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "base.html").write_text(base_html)
    (templates_dir / "booking_list.html").write_text(booking_list_html)
    (templates_dir / "booking_form.html").write_text(booking_form_html)
    (templates_dir / "booking_detail.html").write_text(booking_detail_html)

    print("Файлы приложения hotel успешно записаны.")

def update_project_settings():
    """Добавляет приложение hotel в INSTALLED_APPS и настраивает русскую локаль."""
    settings_path = Path(PROJECT_NAME) / "settings.py"
    if not settings_path.exists():
        raise FileNotFoundError("settings.py не найден. Запустите скрипт из корня проекта после создания проекта.")
    content = settings_path.read_text()
    # Добавляем hotel в INSTALLED_APPS, если ещё нет
    if "'hotel'" not in content:
        content = content.replace("INSTALLED_APPS = [", "INSTALLED_APPS = [\n    'hotel',")
    # Меняем язык и часовой пояс
    content = content.replace("LANGUAGE_CODE = 'en-us'", "LANGUAGE_CODE = 'ru-ru'")
    content = content.replace("TIME_ZONE = 'UTC'", "TIME_ZONE = 'Europe/Moscow'")
    settings_path.write_text(content)
    print("Настройки проекта обновлены.")

def update_root_urls():
    """Подключает urls приложения hotel в корневой urls.py."""
    urls_path = Path(PROJECT_NAME) / "urls.py"
    if not urls_path.exists():
        return
    content = urls_path.read_text()
    # Добавляем include если ещё нет
    if "include('hotel.urls')" not in content:
        # Добавляем импорт include
        if "from django.urls import path" in content:
            content = content.replace("from django.urls import path", "from django.urls import path, include")
        # Добавляем path для пустой строки
        # Находим urlpatterns и вставляем path('', include('hotel.urls')),
        lines = content.split('\n')
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if 'urlpatterns = [' in line and not inserted:
                new_lines.append("    path('', include('hotel.urls')),")
                inserted = True
        if not inserted:
            # fallback: просто добавить в конец списка
            content = content.replace(']', "    path('', include('hotel.urls')),\n]")
        else:
            content = '\n'.join(new_lines)
        urls_path.write_text(content)
        print("Корневой urls.py обновлён.")

def run_migrations(python_exe):
    """Выполняет миграции и создаёт суперпользователя."""
    print("Применение миграций...")
    run_cmd(f'"{python_exe}" manage.py makemigrations')
    run_cmd(f'"{python_exe}" manage.py migrate')
    print("Создание суперпользователя (потребуется ввод данных)...")
    run_cmd(f'"{python_exe}" manage.py createsuperuser')

def main():
    print("=== Автоматическая установка HotelPro ===\n")
    # Шаг 1: создать venv
    python_exe, pip_exe = create_venv()
    # Шаг 2: установить Django
    install_django(pip_exe)
    # Шаг 3: создать проект и приложение
    create_project_structure(python_exe)
    # Шаг 4: перезаписать файлы приложения нашими
    write_app_files()
    # Шаг 5: обновить настройки и urls
    update_project_settings()
    update_root_urls()
    # Шаг 6: миграции и суперпользователь
    run_migrations(python_exe)
    # Шаг 7: запуск сервера
    print("\nЗапуск сервера разработки...")
    print("Сервер будет доступен по адресу http://127.0.0.1:8000")
    run_cmd(f'"{python_exe}" manage.py runserver')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановка пользователем.")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)