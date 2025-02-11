from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Public pages
    path('', views.landing_page, name='landing'),
    
    # Authentication
    path('signup/', views.business_signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard - make sure this is before any catch-all patterns
    path('dashboard/', views.business_dashboard, name='dashboard'),
    path('business/hours/', views.business_hours, name='business_hours'),
    path('service/add/', views.add_service, name='add_service'),
    path('service/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('service/<int:service_id>/delete/', views.delete_service, name='delete_service'),
] 