from django.core.management.base import BaseCommand
from django.conf import settings
from meteostat import Point, Hourly
from flood_app.models import WeatherData, FloodPrediction
from flood_app.predict import train_predict_model
import datetime
import pandas as pd
import requests

class Command(BaseCommand):
    help = 'Collects historical weather data and updates flood predictions for Nepal'

    def add_arguments(self, parser):
        parser.add_argument('--use-weatherapi', action='store_true', help='Use WeatherAPI.com instead of Meteostat')

    def fetch_weatherapi_data(self, location, start, end):
        """Fetch historical weather data from WeatherAPI.com."""
        try:
            api_key = settings.WEATHERAPI_KEY
            url = f'http://api.weatherapi.com/v1/history.json?key={api_key}&q={location}&dt={start.strftime("%Y-%m-%d")}&end_dt={end.strftime("%Y-%m-%d")}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            forecast = data['forecast']['forecastday']
            weather_data = []
            for day in forecast:
                date = datetime.datetime.strptime(day['date'], '%Y-%m-%d')
                weather_data.append({
                    'recorded_at': date,
                    'rainfall': day['day'].get('totalprecip_mm', 0.0),
                    'temperature': day['day'].get('avgtemp_c', 0.0)
                })
            return weather_data
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"WeatherAPI failed for {location}: {str(e)}"))
            return []

    def fetch_meteostat_data(self, location, point, start, end):
        """Fetch historical weather data from Meteostat."""
        try:
            data = Hourly(point, start, end).fetch()
            if data.empty:
                self.stdout.write(self.style.WARNING(f"No Meteostat data for {location}"))
                return []
            weather_data = []
            for timestamp, row in data.iterrows():
                weather_data.append({
                    'recorded_at': timestamp,
                    'rainfall': row['prcp'] if not pd.isna(row['prcp']) else 0,
                    'temperature': row['temp'] if not pd.isna(row['temp']) else 0
                })
            return weather_data
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Meteostat failed for {location}: {str(e)}"))
            return []

    def handle(self, *args, **options):
        use_weatherapi = options.get('use_weatherapi', False)

        # Define cities and coordinates
        cities = {
            'Kathmandu (Bagmati River)': Point(27.7152, 85.3240),
            'Banepa (Roshi River, tributary of Bagmati)': Point(27.6325, 85.5219),
            'Birgunj (Bagmati River)': Point(27.0000, 84.8667),
            'Pokhara (Seti River, tributary of Gandaki)': Point(28.2096, 83.9856),
            'Butwal (Tinau River, Gandaki Basin)': Point(27.7000, 83.4500),
            'Baglung (West Rapti River)': Point(28.2744, 83.5895),
            'Biratnagar (Koshi River)': Point(26.4525, 87.2718),
            'Rajbiraj (Kamala River, Koshi Basin)': Point(26.5367, 86.7458),
            'Ilam (Mai River, tributary of Koshi)': Point(26.9111, 87.9283),
            'Gulariya (Karnali River)': Point(28.0429, 81.5702),
            'Surkhet (Bheri River, Karnali tributary)': Point(28.6167, 81.6167),
            'Jumla (Karnali upstream)': Point(29.2733, 82.1903),
            'Dhangadhi (Mahakali River)': Point(28.6833, 80.6000),
            'Mahendranagar (Mahakali River)': Point(29.0032, 80.5207),
            'Tulsipur (West Rapti River)': Point(28.2530, 82.3375),
            'Dang (Rapti River)': Point(27.9333, 82.4667),
            'Nepalgunj (Babai River)': Point(28.0500, 81.6167),
            'Dhulikhel (Near Roshi River)': Point(27.6227, 85.5392),
            'Janakpur (Kamala River)': Point(26.7161, 85.9214),
            'Bharatpur (Narayani River)': Point(27.6833, 84.4333),
        }

        # Cleanup old data
        city_names = list(cities.keys())
        WeatherData.objects.exclude(location__in=city_names).delete()
        FloodPrediction.objects.exclude(location__in=city_names).delete()
        self.stdout.write(self.style.SUCCESS("✅ Old data for removed locations cleaned up."))

        # Set date range (last 30 days)
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=30)

        # Collect data
        for city, point in cities.items():
            if use_weatherapi:
                weather_data = self.fetch_weatherapi_data(city.split(' (')[0], start, end)
            else:
                weather_data = self.fetch_meteostat_data(city, point, start, end)

            for data in weather_data:
                WeatherData.objects.update_or_create(
                    location=city,
                    recorded_at=data['recorded_at'],
                    defaults={
                        'temperature': data['temperature'],
                        'rainfall': data['rainfall']
                    }
                )
            self.stdout.write(self.style.SUCCESS(f"Collected data for {city}"))

        # Run predictions
        train_predict_model()
        self.stdout.write(self.style.SUCCESS("✅ Flood prediction model trained and predictions updated."))