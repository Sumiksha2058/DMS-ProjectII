from django_cron import CronJobBase, Schedule
from flood_app.predict import train_predict_model
from flood_app.send_alerts import send_flood_alert
from flood_app.management.commands.collect_weather_data import Command as CollectWeatherData

class PredictFloodCronJob(CronJobBase):
    RUN_EVERY_MINS = 1440  # Daily
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'flood_app.predict_flood'

    def do(self):
        try:
            collect_command = CollectWeatherData()
            collect_command.handle(use_weatherapi=True)
            train_predict_model()
            send_flood_alert()
            print("Predictions and alerts processed.")
        except Exception as e:
            print(f"Error in cron job: {str(e)}")