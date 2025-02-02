from django import template
from datetime import datetime, date, timedelta

register = template.Library()

@register.filter
def days_to_expire_func(value):
    today = date.today()
    if today > value.date_created:
        days_to_expire = (value.date_created + timedelta(days=value.expiry_in)) - today
    elif today == value.date_created:
        days_to_expire = 'Expires today'
    else:
        days_to_expire = 'Expired'
    return days_to_expire


@register.filter
def generate_range(value):
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []
