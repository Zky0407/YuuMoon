# coding: utf-8
from django.urls import path
from . import views


urlpatterns = [
    path('', views.proxy_index, name='proxy_index'),
]
