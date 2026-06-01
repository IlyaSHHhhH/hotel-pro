"""
Модели данных для гостиницы HotelPro.
"""
from django.db import models
from django.core.validators import RegexValidator

class Guest(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ФИО")
    phone = models.CharField(max_length=20, validators=[RegexValidator(r'^\+7\d{10}$', message="Формат: +7XXXXXXXXXX")], verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    passport = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{10}$', message="10 цифр без пробелов")], verbose_name="Паспорт")
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
