from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_change/', views.password_change_view, name='password_change'),
    path('forgot_password/', views.forgot_password_view, name='forgot_password'),
    path('access-denied/', views.access_denied_view, name='access_denied'),
]
