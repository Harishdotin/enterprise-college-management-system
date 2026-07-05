"""
URL configuration for CollegeManagementSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("db-check/", views.db_check),
    path('', lambda request: redirect('dashboard_home'), name='root_redirect'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('students/', include('students.urls')),
    path('staff/', include('staff.urls')),
    path('academics/', include('academics.urls')),
    path('attendance/', include('attendance.urls')),
    path('timetable/', include('timetable.urls')),
    path('marks/', include('marks.urls')),
    path('fees/', include('fees.urls')),
    path('notifications/', include('notifications.urls')),
    path('assignments/', include('assignments.urls')),
    path('ai/', include('ai_assistant.urls')),  
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
