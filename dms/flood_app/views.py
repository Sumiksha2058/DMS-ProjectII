from django.shortcuts import render, redirect
from django.http import JsonResponse
from .predict import train_predict_model
from .send_alerts import send_flood_alerts
from .models import WeatherData, FloodPrediction, UserProfile

def predict_and_alert(request):
    train_predict_model()
    send_flood_alerts()
    return JsonResponse({"status": "Predictions and alerts processed"})

def homepage(request):
    return render(request, 'homepage.html')


def prediction_dashboard(request):
    predictions = FloodPrediction.objects.all().order_by('-predicted_date')
    return render(request, 'prediction_dashboard.html', {'predictions': predictions})

def user_management(request):
    users = UserProfile.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        location = request.POST.get('location')
        if name and phone and email and location:
            UserProfile.objects.create(name=name, phone=phone, email=email, location=location)
            return redirect('user_management')
    return render(request, 'flood_app/templates/user_management.html', {'users': users})