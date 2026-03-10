"""
Shared validators for TechBuilt Open School.
"""

import re

from django.core.exceptions import ValidationError


def validate_youtube_url(value):
    """Validate that the URL is a valid YouTube video or playlist link."""
    youtube_pattern = re.compile(
        r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
    )
    if not youtube_pattern.match(value):
        raise ValidationError("Enter a valid YouTube URL.")


def validate_file_size(value, max_mb=10):
    """Validate that uploaded file does not exceed max_mb megabytes."""
    limit = max_mb * 1024 * 1024
    if value.size > limit:
        raise ValidationError(f"File size must not exceed {max_mb} MB.")


def validate_positive_decimal(value):
    """Validate that a decimal value is zero or positive."""
    if value < 0:
        raise ValidationError("Value must be zero or positive.")
