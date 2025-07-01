from twilio.rest import Client
from decouple import config
from flood_app.models import FloodPrediction, UserProfile
import datetime

def send_flood_alerts():
    account_sid = config('TWILIO_ACCOUNT_SID')
    auth_token = config('TWILIO_AUTH_TOKEN')
    twilio_phone = config('TWILIO_PHONE_NUMBER')
    client = Client(account_sid, auth_token)

    predictions = FloodPrediction.objects.filter(predicted_date__gte=datetime.datetime.now())
    for pred in predictions:
        if pred.probability > 0.7:
            users = UserProfile.objects.filter(location=pred.location, is_active=True)
            for user in users:
                message = f"ALERT: Flood risk in {pred.location} on {pred.predicted_date.date()}! Severity: {pred.severity_level}/5. Take precautions."
                try:
                    client.messages.create(
                        body=message,
                        from_=twilio_phone,
                        to=f"+977{user.phone}"
                    )
                    print(f"Alert sent to {user.name} at {user.phone}")
                except Exception as e:
                    print(f"Failed to send alert to {user.phone}: {e}")