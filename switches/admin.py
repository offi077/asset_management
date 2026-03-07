
from django.contrib import admin
from .models import Switch

@admin.register(Switch)
class SwitchAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ip_address', 'location', 'model', 'status')
    search_fields = ('hostname', 'ip_address', 'serial_number', 'location')
