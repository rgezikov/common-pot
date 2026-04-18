from django.contrib import admin
from django.urls import path
from pots import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('auth/telegram/', views.telegram_login, name='telegram_login'),
    path('logout/', views.logout, name='logout'),
    path('pot/new/', views.create_pot, name='create_pot'),
    path('pot/<uuid:token>/', views.pot_detail, name='pot_detail'),
    path('pot/<uuid:token>/drop/new/', views.add_drop, name='add_drop'),
    path('pot/<uuid:token>/drop/<int:drop_id>/', views.drop_detail, name='drop_detail'),
    path('pot/<uuid:token>/drop/<int:drop_id>/edit/', views.edit_drop, name='edit_drop'),
    path('pot/<uuid:token>/drop/<int:drop_id>/delete/', views.delete_drop, name='delete_drop'),
    path('pot/<uuid:token>/member/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    path('pot/<uuid:token>/rename/', views.rename_pot, name='rename_pot'),
    path('pot/<uuid:token>/report/', views.pot_report, name='pot_report'),
    path('join/<uuid:token>/', views.join_pot, name='join_pot'),
]
