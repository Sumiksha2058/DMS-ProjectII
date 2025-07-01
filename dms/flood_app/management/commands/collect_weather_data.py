from django.core.management.base import BaseCommand
import requests
from flood_app.models import WeatherData
from decouple import config
import datetime

class Command(BaseCommand):
    help = 'Collects historical weather data for Nepal'

    def handle(self, *args, **options):
        api_key = config('WEATHERAPI_KEY')
        cities = ['Kathmandu', 'Pokhara', 'Biratnagar']  # Nepal locations
        for city in cities:
            # Historical data (last 7 days, free tier limit)
            url = f"http://api.weatherapi.com/v1/history.json?key={api_key}&q={city}&dt={datetime.datetime.now().strftime('%Y-%m-%d')}&end_dt={datetime.datetime.now().strftime('%Y-%m-%d')}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for entry in data['forecast']['forecastday'][0]['hour'][:5]:  # Limit to recent 5 hours
                    precip = entry['precip_mm']
                    temp = entry['temp_c']
                    humidity = entry['humidity']
                    date = datetime.datetime.fromisoformat(entry['time'].replace('Z', '+00:00'))
                    WeatherData.objects.update_or_create(
                        date=date,
                        location=city,
                        defaults={'precipitation': precip, 'temperature': temp, 'humidity': humidity}
                    )
                self.stdout.write(self.style.SUCCESS(f"Data collected for {city}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to collect data for {city}: {response.text}"))