import base64
from django import template

register = template.Library()

@register.filter(name='b64encode')
def b64encode(value):
    """
    Encodes a binary value to a Base64 string for display in templates.
    """
    if value:
        return base64.b64encode(value).decode('utf-8')
    return ''
