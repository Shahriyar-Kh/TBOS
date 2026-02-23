import hashlib
from django import template

register = template.Library()

@register.simple_tag
def gravatar_url(email, size=150):
    default = "retro"
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}"