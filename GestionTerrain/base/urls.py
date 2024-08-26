from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.loginPage, name="loginPage"),
    path("logout/", views.logoutView, name="logout"),
    path('', views.home, name='home'),
    path("message/", views.message_step, name="message_step"),
    path('terrain/<str:ref_message>', views.terrain_step, name='terrain_step'),
    path('rapport/', views.rapport, name='rapport'),
    path('generate_rapport/<int:choixID>/', views.generate_rapport, name='generate_rapport'),
    path('delete/<int:choixID>', views.delete, name='delete'),
    path('create_commission/', views.create_commission, name='create_commission'),
    path('list_participants/', views.list_participants, name='list_participants'),
]

