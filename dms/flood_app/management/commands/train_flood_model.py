from django.core.management.base import BaseCommand
from flood_app.predict import train_predict_model

class Command(BaseCommand):
    help = 'Train flood prediction model for all cities and forecast for next 7 days'

    def handle(self, *args, **kwargs):
        train_predict_model()
        self.stdout.write(self.style.SUCCESS("✅ Flood prediction training completed."))
