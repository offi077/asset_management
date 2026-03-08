from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserPermissionForm

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('switches:list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'switches:list')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'total_users': users.count(),
        'admin_count': users.filter(role='admin').count(),
        'regular_count': users.filter(role='user').count(),
    }
    return render(request, 'accounts/user_list.html', context)

# @login_required
@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == 'admin':
                user.grant_all_permissions()
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create New User'
    })

@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            if user.role == 'admin':
                user.grant_all_permissions()
            messages.success(request, f'User "{user.username}" updated successfully!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserChangeForm(instance=user)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Edit User',
        'user_obj': user
    })

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.user.pk == user.pk:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully!')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user_obj': user})

@login_required
@user_passes_test(is_admin)
def user_permissions(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        form = UserPermissionForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Permissions updated for "{user.username}"!')
            return redirect('accounts:user_list')
    else:
        form = UserPermissionForm(instance=user)
    
    return render(request, 'accounts/user_permissions.html', {
        'form': form,
        'user_obj': user
    })