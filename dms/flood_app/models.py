from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=100)
    role = models.CharField(
        max_length=20,
        choices=[
            ('Citizen', 'Citizen'),
            ('Admin', 'Admin'),
            ('Analyst', 'Analyst'),
        ],
        default='Citizen'
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    class Meta:
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['location']),
        ]

class WeatherData(models.Model):
    location = models.CharField(max_length=100, db_index=True)  # Add index for faster queries
    recorded_at = models.DateTimeField(db_index=True)  # Index for time-based queries
    temperature = models.FloatField()
    rainfall = models.FloatField()

    def __str__(self):
        return f"Weather at {self.location} on {self.recorded_at}"

    class Meta:
        ordering = ['-recorded_at']  # Default ordering for recent data first

class FloodPrediction(models.Model):
    location = models.CharField(max_length=100, db_index=True)
    predicted_date = models.DateTimeField(db_index=True)
    probability = models.FloatField(default=0.0)
    severity_level = models.IntegerField()

    def __str__(self):
        return f"Prediction for {self.location} on {self.predicted_date}"

    class Meta:
        ordering = ['predicted_date']

class FloodAlert(models.Model):
    location = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    message = models.TextField()

    def __str__(self):
        return f"Alert for {self.location} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']

class RainfallData(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='rainfall_reports')
    location = models.CharField(max_length=100, db_index=True)
    rainfall_amount = models.FloatField()
    collected_time = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=100)

    def __str__(self):
        return f"Rainfall at {self.location} on {self.collected_time}"

    class Meta:
        ordering = ['-collected_time']

class CronJobLog(models.Model):
    code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['code', 'created_at']),
        ]
        ordering = ['-created_at']
