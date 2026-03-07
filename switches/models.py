# switches/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings

class SwitchManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    
    def deleted_only(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class Switch(models.Model):
    ROLE_CHOICES = [
        ('core', 'Core'),
        ('distribution', 'Distribution'),
        ('access', 'Access'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Maintenance', 'Maintenance'),
        ('EoL', 'End of Life'),
    ]
    
    PORT_TYPE_CHOICES = [
        ('24P', '24 Port'),
        ('48P', '48 Port'),
        ('Other', 'Other'),
    ]
    
    # Basic Information
    hostname = models.CharField(max_length=100, verbose_name='Hostname')
    ip_address = models.GenericIPAddressField(verbose_name='IP Address')
    serial_number = models.CharField(max_length=100, unique=True, verbose_name='Serial Number')
    model = models.CharField(max_length=100, blank=True, verbose_name='Model')
    vendor = models.CharField(max_length=100, blank=True, verbose_name='Vendor')
    it_tag = models.CharField(max_length=100, blank=True, verbose_name='IT Tag')
    
    # Location Information
    building_no = models.CharField(max_length=100, blank=True, verbose_name='Building No')
    location = models.CharField(max_length=200, blank=True, verbose_name='Location')
    communication_room_no = models.CharField(max_length=100, blank=True, verbose_name='Communication Room No')
    cabinet_no = models.CharField(max_length=100, blank=True, verbose_name='Cabinet No')
    cabinet_tag = models.CharField(max_length=100, blank=True, verbose_name='Cabinet Tag')
    
    # Technical Specifications
    switch_role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, verbose_name='Switch Role')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', verbose_name='Status')
    
    # Line Cards and Ports
    no_of_line_cards_fiber = models.IntegerField(default=0, verbose_name='Line Cards (Fiber)')
    no_of_line_cards_utp = models.IntegerField(default=0, verbose_name='Line Cards (UTP)')
    total_ports_fiber = models.IntegerField(default=0, verbose_name='Total Ports (Fiber)')
    total_ports_utp = models.IntegerField(default=0, verbose_name='Total Ports (UTP)')
    port_type = models.CharField(max_length=10, choices=PORT_TYPE_CHOICES, blank=True, verbose_name='24P or 48P')
    no_of_used_ports = models.IntegerField(default=0, verbose_name='No. of Used Ports')
    
    # Power Supplies
    no_of_power_supplies = models.IntegerField(default=0, verbose_name='No. of Power Supplies')
    used_power_supplies = models.IntegerField(default=0, verbose_name='Used Power Supplies')
    
    # Additional Information
    remarks = models.TextField(blank=True, verbose_name='Remarks')
    
    # Stack Information
    is_stack = models.BooleanField(default=False, verbose_name='Is Stack')
    stack_priority = models.IntegerField(default=1, verbose_name='Stack Priority')
    stack_member_number = models.IntegerField(default=1, verbose_name='Stack Member Number')
    
    # Soft Delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Managers
    objects = SwitchManager()
    all_objects = AllObjectsManager()
    
    class Meta:
        ordering = ['building_no', 'hostname', 'stack_member_number']
        verbose_name = 'Switch'
        verbose_name_plural = 'Switches'
    
    def __str__(self):
        if self.is_stack:
            return f"{self.hostname} (Member {self.stack_member_number})"
        return self.hostname
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    @property
    def total_ports(self):
        return self.total_ports_fiber + self.total_ports_utp
    
    @property
    def free_ports(self):
        return self.total_ports - self.no_of_used_ports
    
    @property
    def stack_group_key(self):
        return f"{self.hostname}_{self.ip_address}"
    
    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = str(user)
        self.save()
    
    def restore(self):
        self.deleted_at = None
        self.deleted_by = ''
        self.save()


class ColumnPreference(models.Model):
    """Store user's column visibility preferences"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='column_preferences')
    visible_columns = models.JSONField(default=list, help_text='List of visible column names')
    
    # Default columns that should always be visible
    DEFAULT_COLUMNS = [
        'hostname', 'ip_address', 'serial_number', 'model', 'switch_role',
        'building_no', 'location', 'status', 'actions'
    ]
    
    # All available columns
    ALL_COLUMNS = [
        'select', 's_no', 'hostname', 'ip_address', 'serial_number', 'model',
        'no_of_line_cards_fiber', 'no_of_line_cards_utp', 'total_ports_fiber',
        'total_ports_utp', 'port_type', 'no_of_used_ports', 'free_ports',
        'no_of_power_supplies', 'used_power_supplies', 'remarks', 'switch_role',
        'building_no', 'it_tag', 'location', 'communication_room_no',
        'cabinet_no', 'cabinet_tag', 'vendor', 'status', 'stack_info', 'actions'
    ]
    
    def get_visible_columns(self):
        if not self.visible_columns:
            return self.DEFAULT_COLUMNS
        return self.visible_columns
    
    class Meta:
        verbose_name = 'Column Preference'
        verbose_name_plural = 'Column Preferences'