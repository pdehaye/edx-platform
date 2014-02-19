""" Utility functions related to HTTP requests """
from django.conf import settings
from microsite_configuration.middleware import MicrositeConfiguration
from django.contrib.gis.geoip import GeoIP
from django.contrib.gis.geoip.libgeoip import GEOIP_SETTINGS
from functools import wraps
from django.shortcuts import redirect


def safe_get_host(request):
    """
    Get the host name for this request, as safely as possible.

    If ALLOWED_HOSTS is properly set, this calls request.get_host;
    otherwise, this returns whatever settings.SITE_NAME is set to.

    This ensures we will never accept an untrusted value of get_host()
    """
    if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) and '*' not in settings.ALLOWED_HOSTS:
        return request.get_host()
    else:
        return MicrositeConfiguration.get_microsite_configuration_value('site_domain', settings.SITE_NAME)

def embargo_check(func):
    def _wrapped_view(request, *args, **kwargs):
        # TODO: Gracefully degrade if GEOIP_PATH is not set
        path = GEOIP_SETTINGS.get('GEOIP_PATH', None)
        ip = None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        geoip = GeoIP()
        if geoip.country_code(ip) in EmbargoConfig.embargoed_countries_list():
            return redirect('embargo')
        return func(request, *args, **kwargs)
    return _wrapped_view
