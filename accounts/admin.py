# accounts/admin.py - Updated with Migration Permissions

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    list_display = [
        'username', 
        'email', 
        'role', 
        'department',
        'can_view_switches',
        'can_view_migrations',
        'is_active', 
        'is_staff'
    ]
    
    list_filter = [
        'role', 
        'is_active', 
        'is_staff', 
        'department',
        'can_view_switches',
        'can_add_switches',
        'can_view_migrations',
        'can_add_migrations',
    ]
    
    search_fields = ['username', 'email', 'first_name', 'last_name', 'department']
    
    ordering = ['username']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'department')
        }),
        ('Role', {
            'fields': ('role',)
        }),
        ('Switch Permissions', {
            'fields': (
                'can_view_switches',
                'can_add_switches',
                'can_edit_switches',
                'can_delete_switches',
                'can_export_switches',
                'can_import_switches',
                'can_restore_switches',
            ),
            'classes': ('collapse',),
        }),
        ('Migration Permissions', {
            'fields': (
                'can_view_migrations',
                'can_add_migrations',
                'can_edit_migrations',
                'can_delete_migrations',
                'can_manage_port_mappings',
                'can_manage_issues',
                'can_manage_user_impact',
                'can_export_migration_reports',
                'can_update_migration_status',
            ),
            'classes': ('collapse',),
        }),
        ('System Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'department'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    actions = [
        'grant_all_permissions',
        'grant_switch_permissions',
        'grant_migration_view_permissions',
        'grant_migration_coordinator_permissions',
        'grant_migration_engineer_permissions',
        'grant_migration_manager_permissions',
    ]
    
    def grant_all_permissions(self, request, queryset):
        """Grant all permissions to selected users"""
        count = 0
        for user in queryset:
            user.grant_all_permissions()
            count += 1
        self.message_user(request, f'Granted all permissions to {count} user(s).')
    grant_all_permissions.short_description = "Grant all permissions"
    
    def grant_switch_permissions(self, request, queryset):
        """Grant all switch permissions"""
        count = 0
        for user in queryset:
            user.can_view_switches = True
            user.can_add_switches = True
            user.can_edit_switches = True
            user.can_delete_switches = True
            user.can_export_switches = True
            user.can_import_switches = True
            user.can_restore_switches = True
            user.save()
            count += 1
        self.message_user(request, f'Granted switch permissions to {count} user(s).')
    grant_switch_permissions.short_description = "Grant all switch permissions"
    
    def grant_migration_view_permissions(self, request, queryset):
        """Grant migration view permissions (read-only)"""
        count = 0
        for user in queryset:
            user.grant_migration_view_permissions()
            count += 1
        self.message_user(request, f'Granted migration view permissions to {count} user(s).')
    grant_migration_view_permissions.short_description = "Grant migration view permissions"
    
    def grant_migration_coordinator_permissions(self, request, queryset):
        """Grant migration coordinator permissions"""
        count = 0
        for user in queryset:
            user.grant_migration_coordinator_permissions()
            count += 1
        self.message_user(request, f'Granted migration coordinator permissions to {count} user(s).')
    grant_migration_coordinator_permissions.short_description = "Grant migration coordinator permissions"
    
    def grant_migration_engineer_permissions(self, request, queryset):
        """Grant migration engineer permissions"""
        count = 0
        for user in queryset:
            user.grant_migration_engineer_permissions()
            count += 1
        self.message_user(request, f'Granted migration engineer permissions to {count} user(s).')
    grant_migration_engineer_permissions.short_description = "Grant migration engineer permissions"
    
    def grant_migration_manager_permissions(self, request, queryset):
        """Grant migration manager permissions (full access)"""
        count = 0
        for user in queryset:
            user.grant_migration_manager_permissions()
            count += 1
        self.message_user(request, f'Granted migration manager permissions to {count} user(s).')
    grant_migration_manager_permissions.short_description = "Grant migration manager permissions"