from django import template
from config.models import SiteSettings

register = template.Library()


@register.simple_tag
def get_site_settings():
    return SiteSettings.get()


@register.inclusion_tag('config/_registration_enabled.html')
def registration_enabled():
    return {'enabled': SiteSettings.get().registration_enabled}
