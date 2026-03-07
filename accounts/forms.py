# accounts/forms.py - Complete forms file

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users"""
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users"""
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone', 'is_active')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class UserPermissionForm(forms.ModelForm):
    """Form for managing user permissions"""
    class Meta:
        model = CustomUser
        fields = [
            # Switch permissions
            'can_view_switches',
            'can_add_switches',
            'can_edit_switches',
            'can_delete_switches',
            'can_export_switches',
            'can_import_switches',
            'can_restore_switches',
            
            # Migration permissions
            'can_view_migrations',
            'can_add_migrations',
            'can_edit_migrations',
            'can_delete_migrations',
            'can_manage_port_mappings',
            'can_manage_issues',
            'can_manage_user_impact',
            'can_export_migration_reports',
            'can_update_migration_status',
        ]
        
        widgets = {
            # Switch permissions
            'can_view_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_add_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_edit_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_delete_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_export_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_import_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_restore_switches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Migration permissions
            'can_view_migrations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_add_migrations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_edit_migrations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_delete_migrations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_port_mappings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_issues': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_user_impact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_export_migration_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_update_migration_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }