from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('evaluate/', views.evaluate, name='evaluate'),
    path('evaluate-prompt/', views.evaluate_prompt, name='evaluate_prompt'),
    path('scan-weaknesses/', views.scan_weaknesses, name='scan_weaknesses'),
]
