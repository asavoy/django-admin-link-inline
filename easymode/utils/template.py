import os
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import template_source_loaders, find_template_loader

def find_template_path(name):
    """
    Same as :func:`django.template.loader.find_template`, but it only returns the path
    to the template file.
    """
    global template_source_loaders
    if template_source_loaders is None:
        loaders = []
        for loader_name in settings.TEMPLATE_LOADERS:
            loader = find_template_loader(loader_name)
            if loader is not None:
                loaders.append(loader)
        template_source_loaders = tuple(loaders)
    for loader in template_source_loaders:
        try:
            _, display_name = loader(name)
            if display_name:
                return display_name
        except TemplateDoesNotExist:
            pass
    raise TemplateDoesNotExist(name)

def get_admin_media_prefix():
    """
    Returns path prefix for admin assets consistently, even in Django 1.4+
    where `ADMIN_MEDIA_PREFIX` is deprecated.

    NOTE: This is generated directly from the settings module, instead
    of looking in the TemplateContext, which skips template context
    processors.
    """
    if hasattr(settings, 'ADMIN_MEDIA_PREFIX'):
        return settings.ADMIN_MEDIA_PREFIX

    return os.path.join(getattr(settings, 'STATIC_URL'), 'admin/')
