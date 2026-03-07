# switches/decorators.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps

def permission_required(permission_attr):
    """
    Decorator to check if user has specific permission
    Usage: @permission_required('can_add_switches')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Admins and superusers always have permission
            if request.user.is_admin():
                return view_func(request, *args, **kwargs)
            
            # Check if user has the specific permission
            if getattr(request.user, permission_attr, False):
                return view_func(request, *args, **kwargs)
            
            # Permission denied
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('switches:list')
        
        return _wrapped_view
    return decorator


def can_view_switches(view_func):
    """Decorator to check if user can view switches"""
    return permission_required('can_view_switches')(view_func)


def can_add_switches(view_func):
    """Decorator to check if user can add switches"""
    return permission_required('can_add_switches')(view_func)


def can_edit_switches(view_func):
    """Decorator to check if user can edit switches"""
    return permission_required('can_edit_switches')(view_func)


def can_delete_switches(view_func):
    """Decorator to check if user can delete switches"""
    return permission_required('can_delete_switches')(view_func)


def can_export_switches(view_func):
    """Decorator to check if user can export switches"""
    return permission_required('can_export_switches')(view_func)


def can_import_switches(view_func):
    """Decorator to check if user can import switches"""
    return permission_required('can_import_switches')(view_func)


def can_restore_switches(view_func):
    """Decorator to check if user can restore switches"""
    return permission_required('can_restore_switches')(view_func)