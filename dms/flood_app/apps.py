from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Returns the value for a given key in a dictionary.
    Usage: {{ my_dict|get_item:key }}
    """
    return dictionary.get(key)

# flood_app/apps.py
from django.apps import AppConfig

class FloodAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flood_app'

    def ready(self):
        import flood_app.signals  # Ensure signals are loaded
