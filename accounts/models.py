# accounts/models.py - Updated with Migration Permissions

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('user', 'Regular User'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Switch Permissions
    can_view_switches = models.BooleanField(default=True)
    can_add_switches = models.BooleanField(default=False)
    can_edit_switches = models.BooleanField(default=False)
    can_delete_switches = models.BooleanField(default=False)
    can_export_switches = models.BooleanField(default=False)
    can_import_switches = models.BooleanField(default=False)
    can_restore_switches = models.BooleanField(default=False)
    
    # Migration Permissions
    can_view_migrations = models.BooleanField(default=False, help_text="Can view migration dashboard and projects")
    can_add_migrations = models.BooleanField(default=False, help_text="Can create migration projects and switch migrations")
    can_edit_migrations = models.BooleanField(default=False, help_text="Can edit migration projects and switch migrations")
    can_delete_migrations = models.BooleanField(default=False, help_text="Can delete migration projects")
    can_manage_port_mappings = models.BooleanField(default=False, help_text="Can add/edit port mappings")
    can_manage_issues = models.BooleanField(default=False, help_text="Can report and update migration issues")
    can_manage_user_impact = models.BooleanField(default=False, help_text="Can add/edit user impact assessments")
    can_export_migration_reports = models.BooleanField(default=False, help_text="Can export migration reports")
    can_update_migration_status = models.BooleanField(default=False, help_text="Can update migration status and progress")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin' or self.is_superuser
    
    def grant_all_permissions(self):
        """Grant all switch and migration permissions"""
        # Switch permissions
        self.can_view_switches = True
        self.can_add_switches = True
        self.can_edit_switches = True
        self.can_delete_switches = True
        self.can_export_switches = True
        self.can_import_switches = True
        self.can_restore_switches = True
        
        # Migration permissions
        self.can_view_migrations = True
        self.can_add_migrations = True
        self.can_edit_migrations = True
        self.can_delete_migrations = True
        self.can_manage_port_mappings = True
        self.can_manage_issues = True
        self.can_manage_user_impact = True
        self.can_export_migration_reports = True
        self.can_update_migration_status = True
        
        self.save()
    
    def grant_migration_view_permissions(self):
        """Grant read-only migration permissions"""
        self.can_view_migrations = True
        self.save()
    
    def grant_migration_coordinator_permissions(self):
        """Grant coordinator-level migration permissions"""
        self.can_view_migrations = True
        self.can_add_migrations = True
        self.can_manage_port_mappings = True
        self.can_manage_user_impact = True
        self.can_export_migration_reports = True
        self.save()
    
    def grant_migration_engineer_permissions(self):
        """Grant engineer-level migration permissions"""
        self.can_view_migrations = True
        self.can_manage_port_mappings = True
        self.can_manage_issues = True
        self.can_update_migration_status = True
        self.save()
    
    def grant_migration_manager_permissions(self):
        """Grant full migration permissions"""
        self.can_view_migrations = True
        self.can_add_migrations = True
        self.can_edit_migrations = True
        self.can_delete_migrations = True
        self.can_manage_port_mappings = True
        self.can_manage_issues = True
        self.can_manage_user_impact = True
        self.can_export_migration_reports = True
        self.can_update_migration_status = True
        self.save()
    
    def has_migration_permission(self, permission):
        """Check if user has a specific migration permission or is admin"""
        if self.is_admin():
            return True
        return getattr(self, permission, False)