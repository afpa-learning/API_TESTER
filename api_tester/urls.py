"""
Configuration des URL pour l'app api_tester.
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/test/', views.test_api_view, name='test_api'),
]
