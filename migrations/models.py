from django.db import models
#from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator


class MigrationProject(models.Model):
    """Track overall migration projects"""
    STATUS_CHOICES = [
        ('Planning', 'Planning'),
        ('In Progress', 'In Progress'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    project_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    
    # Timeline
    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Project lead
    project_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_migrations')
    team_members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='migration_team', blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_migrations')
    
    # Budget tracking
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.project_name} ({self.status})"
    
    @property
    def total_switches_to_migrate(self):
        return self.migrations.count()
    
    @property
    def completed_migrations(self):
        return self.migrations.filter(migration_status='Completed').count()
    
    @property
    def progress_percentage(self):
        total = self.total_switches_to_migrate
        if total == 0:
            return 0
        return round((self.completed_migrations / total) * 100, 2)
    
    @property
    def is_overdue(self):
        if self.status == 'Completed':
            return False
        return timezone.now().date() > self.planned_end_date


class SwitchMigration(models.Model):
    """Track individual switch migrations"""
    MIGRATION_STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Pre-Check', 'Pre-Check Done'),
        ('In Progress', 'In Progress'),
        ('Testing', 'Testing'),
        ('Completed', 'Completed'),
        ('Rolled Back', 'Rolled Back'),
        ('Failed', 'Failed'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    # Link to migration project
    project = models.ForeignKey(MigrationProject, on_delete=models.CASCADE, related_name='migrations')
    
    # Old and New Switches (using your existing Switch model)
    old_switch = models.ForeignKey('switches.Switch', on_delete=models.CASCADE, related_name='migrations_as_old')
    new_switch = models.ForeignKey('switches.Switch', on_delete=models.CASCADE, related_name='migrations_as_new', null=True, blank=True)
    
    # Migration details
    migration_status = models.CharField(max_length=20, choices=MIGRATION_STATUS_CHOICES, default='Scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    
    # Port migration tracking
    fiber_ports_to_migrate = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    fiber_ports_migrated = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    utp_ports_to_migrate = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    utp_ports_migrated = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Schedule
    scheduled_date = models.DateTimeField()
    scheduled_downtime_start = models.DateTimeField(null=True, blank=True)
    scheduled_downtime_end = models.DateTimeField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_migrations')
    backup_engineer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='backup_migrations')
    
    # Documentation
    pre_migration_notes = models.TextField(blank=True, help_text="Pre-migration checklist and notes")
    migration_notes = models.TextField(blank=True, help_text="Notes during migration")
    post_migration_notes = models.TextField(blank=True, help_text="Post-migration verification notes")
    issues_encountered = models.TextField(blank=True)
    rollback_plan = models.TextField(blank=True)
    
    # Verification flags
    config_backup_done = models.BooleanField(default=False)
    pre_check_done = models.BooleanField(default=False)
    stakeholder_notified = models.BooleanField(default=False)
    post_verification_done = models.BooleanField(default=False)
    documentation_updated = models.BooleanField(default=False)
    
    # Downtime tracking (in minutes)
    estimated_downtime = models.IntegerField(null=True, blank=True, help_text="Estimated downtime in minutes")
    actual_downtime = models.IntegerField(null=True, blank=True, help_text="Actual downtime in minutes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_switch_migrations')
    
    class Meta:
        ordering = ['scheduled_date']
        unique_together = ['project', 'old_switch']
        
    def __str__(self):
        return f"Migration: {self.old_switch.hostname} → {self.new_switch.hostname if self.new_switch else 'TBD'}"
    
    @property
    def total_ports_to_migrate(self):
        return self.fiber_ports_to_migrate + self.utp_ports_to_migrate
    
    @property
    def total_ports_migrated(self):
        return self.fiber_ports_migrated + self.utp_ports_migrated
    
    @property
    def port_migration_progress(self):
        total = self.total_ports_to_migrate
        if total == 0:
            return 0
        return round((self.total_ports_migrated / total) * 100, 2)
    
    @property
    def is_fiber_migration_complete(self):
        return self.fiber_ports_migrated >= self.fiber_ports_to_migrate
    
    @property
    def is_utp_migration_complete(self):
        return self.utp_ports_migrated >= self.utp_ports_to_migrate
    
    @property
    def all_ports_migrated(self):
        return self.is_fiber_migration_complete and self.is_utp_migration_complete


class PortMigrationMapping(models.Model):
    """Track individual port-to-port mappings during migration"""
    switch_migration = models.ForeignKey(SwitchMigration, on_delete=models.CASCADE, related_name='port_mappings')
    
    # Old switch port details
    old_port_number = models.CharField(max_length=50)
    old_port_type = models.CharField(max_length=20, choices=[('Fiber', 'Fiber'), ('UTP', 'UTP')])
    old_port_description = models.CharField(max_length=200, blank=True)
    old_vlan = models.CharField(max_length=100, blank=True)
    
    # New switch port details
    new_port_number = models.CharField(max_length=50, blank=True)
    new_port_type = models.CharField(max_length=20, choices=[('Fiber', 'Fiber'), ('UTP', 'UTP')])
    new_vlan = models.CharField(max_length=100, blank=True)
    
    # Connected device/user info
    connected_device = models.CharField(max_length=200, blank=True, help_text="Device connected to this port")
    user_department = models.CharField(max_length=100, blank=True)
    user_contact = models.CharField(max_length=100, blank=True)
    
    # Migration status
    is_migrated = models.BooleanField(default=False)
    migration_date = models.DateTimeField(null=True, blank=True)
    migrated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Testing
    is_tested = models.BooleanField(default=False)
    test_result = models.CharField(max_length=20, choices=[('Pass', 'Pass'), ('Fail', 'Fail'), ('Pending', 'Pending')], default='Pending')
    test_notes = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['old_port_number']
        
    def __str__(self):
        return f"{self.old_port_number} → {self.new_port_number or 'Not Assigned'}"


class MigrationChecklist(models.Model):
    """Pre-defined checklist items for migrations"""
    PHASE_CHOICES = [
        ('Pre-Migration', 'Pre-Migration'),
        ('During Migration', 'During Migration'),
        ('Post-Migration', 'Post-Migration'),
    ]
    
    switch_migration = models.ForeignKey(SwitchMigration, on_delete=models.CASCADE, related_name='checklist_items')
    
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES)
    item_order = models.IntegerField(default=0)
    description = models.CharField(max_length=300)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['phase', 'item_order']
        
    def __str__(self):
        return f"{self.phase}: {self.description}"


class MigrationIssue(models.Model):
    """Track issues encountered during migration"""
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]
    
    switch_migration = models.ForeignKey(SwitchMigration, on_delete=models.CASCADE, related_name='issues')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_issues')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.severity}: {self.title}"


class MigrationActivityLog(models.Model):
    """Audit trail for all migration activities"""
    switch_migration = models.ForeignKey(SwitchMigration, on_delete=models.CASCADE, related_name='activity_logs')
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Store changed data as JSON
    changed_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"


class UserImpactAssessment(models.Model):
    """Track user/department impact for migrations"""
    switch_migration = models.ForeignKey(SwitchMigration, on_delete=models.CASCADE, related_name='user_impacts')
    
    # User/Department info
    department_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Impact details
    number_of_users_affected = models.IntegerField(default=0)
    critical_services = models.TextField(blank=True, help_text="List critical services affected")
    
    # Notification tracking
    notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    acknowledgment_received = models.BooleanField(default=False)
    
    # Post-migration feedback
    feedback = models.TextField(blank=True)
    issues_reported = models.TextField(blank=True)
    satisfaction_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    
    class Meta:
        ordering = ['department_name']
        
    def __str__(self):
        return f"{self.department_name} - {self.number_of_users_affected} users"