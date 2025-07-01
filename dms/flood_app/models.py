from django.db import models

class WeatherData(models.Model):
    date = models.DateTimeField()
    location = models.CharField(max_length=255)  # e.g., "Karnali River"
    precipitation = models.FloatField()  # in mm
    temperature = models.FloatField()  # in °C
    humidity = models.FloatField()  # in %
    river_level = models.FloatField(null=True)  # in meters, if available

    def __str__(self):
        return f"{self.location} - {self.date}"

class FloodPrediction(models.Model):
    location = models.CharField(max_length=255)
    predicted_date = models.DateTimeField()
    probability = models.FloatField()  # 0 to 1
    severity_level = models.IntegerField()  # 1-5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location} - {self.predicted_date}"

class UserProfile(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)  # For SMS alerts
    email = models.EmailField()
    location = models.CharField(max_length=255)  # User's area
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name