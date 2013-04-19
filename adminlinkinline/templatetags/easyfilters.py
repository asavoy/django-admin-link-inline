from django.template.defaultfilters import stringfilter
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def admin_media_prefix(context):
    """
    Returns path prefix to admin media assets, since ADMIN_MEDIA_PREFIX
    is deprecated in Django 1.4.
    """
    if context.has_key('ADMIN_MEDIA_PREFIX'):
        return context.get('ADMIN_MEDIA_PREFIX')
    else:
        return context.get('STATIC_URL') + 'admin/'