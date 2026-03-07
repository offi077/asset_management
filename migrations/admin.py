# migrations/admin.py
from django.contrib import admin
from .models import (
    MigrationProject, SwitchMigration, PortMigrationMapping,
    MigrationChecklist, MigrationIssue, MigrationActivityLog,
    UserImpactAssessment
)

@admin.register(MigrationProject)
class MigrationProjectAdmin(admin.ModelAdmin):
    list_display = ['project_name', 'status', 'planned_start_date', 'planned_end_date', 'project_manager']
    list_filter = ['status', 'planned_start_date']
    search_fields = ['project_name', 'description']

@admin.register(SwitchMigration)
class SwitchMigrationAdmin(admin.ModelAdmin):
    list_display = ['old_switch', 'new_switch', 'migration_status', 'priority', 'scheduled_date', 'assigned_to']
    list_filter = ['migration_status', 'priority', 'scheduled_date']
    search_fields = ['old_switch__hostname', 'new_switch__hostname']

@admin.register(PortMigrationMapping)
class PortMigrationMappingAdmin(admin.ModelAdmin):
    list_display = ['switch_migration', 'old_port_number', 'new_port_number', 'old_port_type', 'is_migrated', 'test_result']
    list_filter = ['old_port_type', 'is_migrated', 'test_result']

@admin.register(MigrationChecklist)
class MigrationChecklistAdmin(admin.ModelAdmin):
    list_display = ['switch_migration', 'phase', 'description', 'is_completed', 'completed_by']
    list_filter = ['phase', 'is_completed']

@admin.register(MigrationIssue)
class MigrationIssueAdmin(admin.ModelAdmin):
    list_display = ['switch_migration', 'title', 'severity', 'status', 'reported_by', 'assigned_to']
    list_filter = ['severity', 'status']
    search_fields = ['title', 'description']

@admin.register(UserImpactAssessment)
class UserImpactAssessmentAdmin(admin.ModelAdmin):
    list_display = ['switch_migration', 'department_name', 'contact_person', 'number_of_users_affected', 'notified']
    list_filter = ['notified']
    search_fields = ['department_name', 'contact_person']

@admin.register(MigrationActivityLog)
class MigrationActivityLogAdmin(admin.ModelAdmin):
    list_display = ['switch_migration', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['timestamp']