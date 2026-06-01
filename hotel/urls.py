from django.urls import path
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
