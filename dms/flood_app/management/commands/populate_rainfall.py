from django.core.management.base import BaseCommand
from flood_app.models import RainfallData, UserProfile
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Populate RainfallData with sample data for the last 20 days for all registered users'

    def handle(self, *args, **kwargs):
        # List of locations (matching your weather data system)
        locations = [
            'Kathmandu (Bagmati River)', 'Banepa (Roshi River, tributary of Bagmati)',
            'Birgunj (Bagmati River)', 'Pokhara (Seti River, tributary of Gandaki)',
            'Butwal (Tinau River, Gandaki Basin)', 'Baglung (West Rapti River)',
            'Biratnagar (Koshi River)', 'Rajbiraj (Kamala River, Koshi Basin)',
            'Ilam (Mai River, tributary of Koshi)', 'Gulariya (Karnali River)',
            'Surkhet (Bheri River, Karnali tributary)', 'Jumla (Karnali upstream)',
            'Dhangadhi (Mahakali River)', 'Mahendranagar (Mahakali River)',
            'Tulsipur (West Rapti River)', 'Dang (Rapti River)', 'Nepalgunj (Babai River)',
            'Dhulikhel (Near Roshi River)', 'Janakpur (Kamala River)', 'Bharatpur (Narayani River)'
        ]

        sources = ['Manual', 'Sensor', 'Mobile App']
        total_count = 0

        # Loop through all user profiles
        user_profiles = UserProfile.objects.select_related('user')

        if not user_profiles.exists():
            self.stdout.write(self.style.WARNING('⚠️ No UserProfiles found.'))
            return

        for profile in user_profiles:
            # Optional: delete previous test data for this user
            RainfallData.objects.filter(user=profile).delete()

            for location in locations:
                for i in range(20):
                    collected_time = datetime.today() - timedelta(days=(19 - i))
                    rainfall_amount = round(random.uniform(0, 200), 2)
                    source = random.choice(sources)

                    RainfallData.objects.create(
                        user=profile,
                        location=location,
                        rainfall_amount=rainfall_amount,
                        collected_time=collected_time,
                        source=source
                    )
                    total_count += 1

            self.stdout.write(self.style.SUCCESS(f"✅ Populated RainfallData for user {profile.user.username}"))

        self.stdout.write(self.style.SUCCESS(f"🎉 Total {total_count} RainfallData records populated."))
