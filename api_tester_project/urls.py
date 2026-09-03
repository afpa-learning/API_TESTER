"""
Configuration des URL pour le projet api_tester_project.

"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api_tester.urls')),
]
