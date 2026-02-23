import hashlib

from django import template
from Utils_File.video_durations import video_duration  # Import your function
from app.models import Course


register = template.Library()

@register.filter
def get(value, key):
    """Safe get method for dictionary lookup."""
    return value.get(key) if isinstance(value, dict) else None

@register.filter
def course_video_duration(course):
    """Returns the total video duration for a given course."""
    if isinstance(course, Course):
        return video_duration(course)  # Call your function and return formatted time
    return "N/A"  # Return 'N/A' if invalid input

@register.filter
def get_item(value, key):
    """Safe dictionary lookup with default"""
    if isinstance(value, dict):
        return value.get(key, 0)
    return 0  # Return 0 if not a dictionary

@register.filter
def multiply(value, arg):
    """Multiplication filter"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Division filter with zero protection"""
    try:
        return float(value) / float(arg) if arg else 0
    except (ValueError, TypeError):
        return 0

@register.filter(name='range')
def make_range(value):
    """Range generator filter"""
    return range(1, int(value) + 1)


@register.filter
def format_duration(minutes):
    """Convert total minutes to hours and minutes format"""
    if not minutes:
        return "0m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{remaining_minutes}m"


@register.filter(name='discount_calculation')
def discount_calculation(price, discount):
    try:
        # Convert to float and handle commas
        price = float(str(price).replace(',', ''))
        discount = float(str(discount).replace(',', ''))

        # Calculate discounted price
        discounted_price = price * (1 - discount / 100)
        return round(discounted_price, 2)
    except (ValueError, TypeError):
        return price  # Return original price if calculation fails

@register.filter(name='multiply')
def multiply(value, arg):
        """Multiply the value by the argument"""
        try:
            return float(value) * float(arg)
        except (ValueError, TypeError):
            return value