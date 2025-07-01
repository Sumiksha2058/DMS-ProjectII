from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_and_alert, name='predict_and_alert'),
    path('', views.homepage, name='templates/homepage'),  # Maps to root of flood_app URLs
    path('dashboard/', views.prediction_dashboard, name='templates/prediction_dashboard'),
    path('users/', views.user_management, name='templates/user_management'),
]