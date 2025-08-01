from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('home/', views.homepage, name='homepage'),
    path('register/', views.register_user, name='register_user'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('predict/', views.predict_and_alert, name='predict_and_alert'),
    path('prediction_dashboard/', views.prediction_dashboard, name='prediction_dashboard'),
    path('user_management/', views.user_management, name='user_management'),
    path('alert_management/', views.alert_management, name='alert_management'),
    path('download-csv/', views.download_predictions_csv, name='download_predictions_csv'),
    path('userprofile-table/', views.show_userprofile_table, name='show_userprofile_table'),


]
