from django.contrib import admin
from django.urls import path
from pots import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('auth/telegram/', views.telegram_login, name='telegram_login'),
    path('auth/webapp/', views.webapp_auth, name='webapp_auth'),
    path('logout/', views.logout, name='logout'),
    path('pot/new/', views.create_pot, name='create_pot'),
    path('pot/<uuid:token>/', views.pot_detail, name='pot_detail'),
    path('pot/<uuid:token>/manifest.json', views.pot_manifest, name='pot_manifest'),
    path('pot/<uuid:token>/drop/new/', views.add_drop, name='add_drop'),
    path('pot/<uuid:token>/drop/<int:drop_id>/', views.drop_detail, name='drop_detail'),
    path('pot/<uuid:token>/drop/<int:drop_id>/edit/', views.edit_drop, name='edit_drop'),
    path('pot/<uuid:token>/drop/<int:drop_id>/delete/', views.delete_drop, name='delete_drop'),
    path('pot/<uuid:token>/member/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    path('pot/<uuid:token>/placeholder/add/', views.add_placeholder, name='add_placeholder'),
    path('pot/<uuid:token>/placeholder/<int:member_id>/claim-link/', views.generate_claim_link, name='generate_claim_link'),
    path('claim/<uuid:claim_token>/', views.claim_placeholder, name='claim_placeholder'),
    path('pot/<uuid:token>/rename/', views.rename_pot, name='rename_pot'),
    path('pot/<uuid:token>/delete/', views.delete_pot, name='delete_pot'),
    path('pot/<uuid:token>/report/', views.pot_report, name='pot_report'),
    path('join/<uuid:token>/', views.join_pot, name='join_pot'),
    path('help/', views.help_page, name='help'),
    path('sw.js', views.service_worker, name='service_worker'),
]
