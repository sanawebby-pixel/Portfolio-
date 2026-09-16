from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('employee/add/', views.add_employee, name='add_employee'),
    path('employee/edit/<int:pk>/', views.edit_employee, name='edit_employee'),
    path('record/add/', views.add_record, name='add_record'),
    path('record/edit/<int:pk>/', views.edit_record, name='edit_record'),
    path('record/delete/<int:pk>/', views.delete_record, name='delete_record'),
    path('employee/delete/<int:pk>/', views.delete_employee, name='delete_employee'),
]
