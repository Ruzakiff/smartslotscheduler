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
    path('logout/', auth_views.LogoutView.as_view(next_page='core:landing'), name='logout'),
    
    # Business dashboard
    path('dashboard/', views.business_dashboard, name='dashboard'),
] 