# custom_filters.py
from django import template
from datetime import date

register = template.Library()

@register.filter(name='event_status')
def event_status(event_date):
    today = date.today()
    return 'Finished' if event_date < today else 'Active'
