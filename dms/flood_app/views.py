from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from collections import Counter
from sklearn.metrics import confusion_matrix
from datetime import datetime
import requests
import csv
import sqlite3

from .models import WeatherData, FloodPrediction, UserProfile, FloodAlert
from .predict import train_predict_model
from .send_alerts import send_flood_alerts

# --- Severity Mapping ---
SEVERITY_MAP = {
    1: "Critical",
    2: "High",
    3: "Moderate",
    4: "Low"
}

# --- Registration ---
def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        location = request.POST.get('location', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'Citizen').strip()

        if not username or not password or not role:
            messages.error(request, "Username, password, and role are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, password=password, email=email)

                    #Check if user already has a profile (extra safety)
                    if hasattr(user, 'userprofile'):
                        messages.error(request, "User profile already exists.")
                        return redirect('register_user')

                    UserProfile.objects.create(
                        user=user,
                        name=username,
                        phone=phone,
                        email=email,
                        location=location,
                        role=role
                    )

                messages.success(request, "Registration successful. Please log in.")
                return redirect('login_user')

            except IntegrityError as e:
                messages.error(request, f"Database error during registration: {str(e)}")
            except Exception as e:
                messages.error(request, f"Unexpected error: {str(e)}")

    roles = [('Citizen', 'Citizen'), ('Admin', 'Admin'), ('Analyst', 'Analyst')]
    return render(request, 'register.html', {'roles': roles})



# --- Login ---
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
        else:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                try:
                    role = user.userprofile.role  # custom role from UserProfile

                    if role == 'Admin':
                        return redirect('homepage')  # Admins go to homepage
                    elif role == 'Citizen':
                        return redirect('user_dashboard')  # Citizens go to user dashboard
                    elif role == 'Analyst':
                        return redirect('prediction_dashboard')  # Add your analyst redirect
                    else:
                        return redirect('homepage')  # Default fallback

                except UserProfile.DoesNotExist:
                    messages.error(request, "User profile not found.")
                    logout(request)
                    return redirect('login_user')
            else:
                messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')



# --- Logout ---
def logout_user(request):
    logout(request)
    return redirect('login_user')


# --- Homepage ---
@login_required
def homepage(request):
    return render(request, 'homepage.html')


# --- User Dashboard ---
@login_required
def user_dashboard(request):
    try:
        profile = request.user.userprofile
        location = profile.location.replace(" ", "+")
        api_key = settings.WEATHERAPI_KEY
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(url)

        dashboard_data = {'role': profile.role}

        if response.status_code == 200:
            data = response.json()
            recorded_at = datetime.fromtimestamp(data['dt'])
            live_weather = {
                'recorded_at': recorded_at,
                'temperature': data['main']['temp'],
                'rainfall': data.get('rain', {}).get('1h', 0),
                'humidity': data['main']['humidity'],
                'location': profile.location,
            }
            WeatherData.objects.update_or_create(
                location=profile.location,
                recorded_at=recorded_at,
                defaults=live_weather
            )
            dashboard_data['weather_data'] = [live_weather]
        else:
            messages.warning(request, "Unable to fetch live weather.")
            dashboard_data['weather_data'] = WeatherData.objects.filter(
                location__icontains=profile.location).order_by('-recorded_at')[:5]

        dashboard_data['alerts'] = FloodAlert.objects.filter(
            location__icontains=profile.location).order_by('-created_at')[:5]

        return render(request, 'dashboard.html', dashboard_data)

    except Exception as e:
        messages.error(request, f"Dashboard error: {str(e)}")
        return render(request, 'dashboard.html', {'weather_data': [], 'alerts': []})


# --- Predict & Alert ---
def predict_and_alert(request):
    try:
        if not train_predict_model():
            return JsonResponse({"status": "No data for prediction"}, status=400)
        send_flood_alerts()
        return JsonResponse({"status": "Prediction and alerts sent"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# --- Prediction Dashboard ---
def prediction_dashboard(request):
    query = request.GET.get('q', '')
    predictions = FloodPrediction.objects.filter(location__icontains=query) if query else FloodPrediction.objects.all()

    if predictions.exists():
        severity_vals = [p.severity_level for p in predictions]
        counter = Counter(severity_vals)
        labels = sorted(counter.keys())
        chart_labels = [SEVERITY_MAP.get(k, str(k)) for k in labels]
        chart_counts = [counter[k] for k in labels]
        matrix = confusion_matrix(severity_vals, severity_vals, labels=[1, 2, 3, 4]).tolist()
    else:
        chart_labels, chart_counts, matrix = [], [], []

    return render(request, 'prediction_dashboard.html', {
        'predictions': predictions,
        'query': query,
        'chart_labels': chart_labels,
        'chart_counts': chart_counts,
        'confusion_matrix': matrix,
        'SEVERITY_MAP': SEVERITY_MAP,
    })


# --- User Management ---
@login_required
def user_management(request):
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'Admin':
        messages.error(request, "Access denied.")
        return redirect('user_dashboard')

    user_profiles = UserProfile.objects.all().order_by('name')
    show_add_form = request.GET.get('show_add_form', 'false') == 'true'
    show_update_form = request.GET.get('show_update_form', 'false') == 'true'
    update_user = None

    if show_update_form:
        update_id = request.GET.get('update_id')
        if update_id and update_id.isdigit():
            update_user = get_object_or_404(UserProfile, id=int(update_id))

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            profile = get_object_or_404(UserProfile, id=request.POST.get('delete_id'))
            profile.user.delete()
            messages.success(request, f"User '{profile.name}' deleted.")
            return redirect('user_management')

        elif 'update_id' in request.POST:
            profile = get_object_or_404(UserProfile, id=request.POST.get('update_id'))
            name = request.POST.get('update_name', '').strip()
            email = request.POST.get('update_email', '').strip()
            phone = request.POST.get('update_phone', '').strip()
            location = request.POST.get('update_location', '').strip()
            role = request.POST.get('update_role', 'Citizen').strip()

            if name and email and phone and location and role:
                try:
                    profile.user.first_name = name.split()[0]
                    profile.user.last_name = ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                    profile.user.email = email
                    profile.user.save()

                    profile.name = name
                    profile.phone = phone
                    profile.location = location
                    profile.role = role
                    profile.save()

                    messages.success(request, f"User '{profile.name}' updated.")
                except Exception as e:
                    messages.error(request, f"Update error: {str(e)}")
            else:
                messages.error(request, "All fields are required.")
            return redirect('user_management')

        elif 'name' in request.POST:
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            location = request.POST.get('location', '').strip()
            role = request.POST.get('role', 'Citizen').strip()
            username = name.lower().replace(' ', '_') + '_' + str(UserProfile.objects.count() + 1)
            password = 'default_password123'

            if not all([name, email, phone, location, role]):
                messages.error(request, "All fields are required.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already in use.")
            else:
                try:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email=email,
                        first_name=name.split()[0],
                        last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                    )
                    UserProfile.objects.create(
                        user=user,
                        name=name,
                        phone=phone,
                        email=email,
                        location=location,
                        role=role
                    )
                    messages.success(request, f"User '{name}' added with default password '{password}'.")
                except Exception as e:
                    messages.error(request, f"Add user error: {str(e)}")
            return redirect('user_management')

    return render(request, 'user_management.html', {
        'user_profiles': user_profiles,
        'show_add_form': show_add_form,
        'show_update_form': show_update_form,
        'update_user': update_user,
    })


# --- Alert Management ---
@login_required
def alert_management(request):
    profile = getattr(request.user, 'userprofile', None)
    if not profile:
        messages.error(request, "User profile not found.")
        return redirect('homepage')

    alerts = FloodAlert.objects.filter(location__icontains=profile.location) if profile.role == 'Citizen' else FloodAlert.objects.all()
    query = request.GET.get('q', '').strip()
    if query:
        alerts = alerts.filter(location__icontains=query)

    page_obj = Paginator(alerts.order_by('-created_at'), 10).get_page(request.GET.get('page'))
    return render(request, 'alert_management.html', {'alerts': page_obj, 'query': query})


# --- Download CSV ---
def download_predictions_csv(request):
    predictions = FloodPrediction.objects.all().order_by('predicted_date')
    response = StreamingHttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="flood_predictions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Location', 'Predicted Date', 'Probability', 'Severity Level'])
    for p in predictions:
        writer.writerow([
            p.location,
            p.predicted_date.strftime('%Y-%m-%d %H:%M:%S'),
            f"{p.probability:.2f}%",
            SEVERITY_MAP.get(p.severity_level, 'Unknown')
        ])

    return response



def show_userprofile_table(request):
    db_path = settings.DATABASES['default']['NAME']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    table_name = 'flood_app_userprofile'
    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # Get all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    conn.close()

    return render(request, 'full_db_view.html', {
        'columns': columns,
        'rows': rows,
        'table_name': table_name
    })
