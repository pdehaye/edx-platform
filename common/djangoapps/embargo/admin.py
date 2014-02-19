"""
Admin site bindings for embargo
"""

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from embargo.models import EmbargoConfig

admin.site.register(EmbargoConfig, ConfigurationModelAdmin)
