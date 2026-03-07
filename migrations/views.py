from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import csv
import json

# Get the User model
User = get_user_model()

# Import models from this app
from .models import (
    MigrationProject, SwitchMigration, PortMigrationMapping,
    MigrationChecklist, MigrationIssue, MigrationActivityLog,
    UserImpactAssessment
)

# Import Switch model from switches app
from switches.models import Switch

def check_migration_permission(user, permission):
    """
    Check if user has migration permission or is admin.
    Works with CustomUser model's is_admin() method.
    """
    if user.is_admin():
        return True
    return user.has_migration_permission(permission)

# ====================
# DASHBOARD
# ====================

@login_required
def migration_dashboard(request):
    """Main dashboard showing all migration projects"""
    if not check_migration_permission(request.user, 'can_view_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to view migrations.</p>"
            "<p><a href='/'>Go to Home</a></p>"
        )
    projects = MigrationProject.objects.all()
    
    # Statistics
    total_projects = projects.count()
    active_projects = projects.filter(status__in=['Planning', 'In Progress']).count()
    completed_projects = projects.filter(status='Completed').count()
    
    # Get upcoming migrations (next 7 days)
    upcoming_date = timezone.now() + timedelta(days=7)
    upcoming_migrations = SwitchMigration.objects.filter(
        scheduled_date__lte=upcoming_date,
        migration_status__in=['Scheduled', 'Pre-Check']
    ).select_related('old_switch', 'new_switch', 'project')[:10]
    
    # Get in-progress migrations
    in_progress = SwitchMigration.objects.filter(
        migration_status='In Progress'
    ).select_related('old_switch', 'new_switch', 'project')
    
    # Recent issues
    recent_issues = MigrationIssue.objects.filter(
        status__in=['Open', 'In Progress']
    ).select_related('switch_migration', 'assigned_to')[:10]
    
    context = {
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'upcoming_migrations': upcoming_migrations,
        'in_progress': in_progress,
        'recent_issues': recent_issues,
    }
    
    return render(request, 'migrations/migration_dashboard.html', context)


# ====================
# PROJECT VIEWS
# ====================

@login_required
def project_list(request):
    """List all migration projects"""
    if not check_migration_permission(request.user, 'can_view_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to view migration projects.</p>"
        )
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')
    
    projects = MigrationProject.objects.all()
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    if search:
        projects = projects.filter(
            Q(project_name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Annotate with statistics
    projects = projects.annotate(
        total_migrations=Count('migrations'),
        completed_count=Count('migrations', filter=Q(migrations__migration_status='Completed'))
    )
    
    context = {
        'projects': projects,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'migrations/project_list.html', context)


@login_required
def create_project(request):
    """Create a new migration project"""
    if not check_migration_permission(request.user, 'can_add_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to create migration projects.</p>"
        )
    if request.method == 'POST':
        project = MigrationProject.objects.create(
            project_name=request.POST.get('project_name'),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'Planning'),
            planned_start_date=request.POST.get('planned_start_date'),
            planned_end_date=request.POST.get('planned_end_date'),
            project_manager_id=request.POST.get('project_manager') or None,
            estimated_budget=request.POST.get('estimated_budget') or None,
            created_by=request.user
        )
        
        # Add team members if provided
        team_member_ids = request.POST.getlist('team_members')
        if team_member_ids:
            project.team_members.set(team_member_ids)
        
        messages.success(request, f'Project "{project.project_name}" created successfully!')
        return redirect('migrations:project_detail', pk=project.pk)
    
    # GET request - show form
    users = User.objects.all().order_by('username')
    context = {
        'users': users,
        'status_choices': MigrationProject.STATUS_CHOICES,
    }
    return render(request, 'migrations/project_create.html', context)


@login_required
def edit_project(request, pk):
    """Edit an existing migration project"""
    if not check_migration_permission(request.user, 'can_edit_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to edit migration projects.</p>"
        )
    project = get_object_or_404(MigrationProject, pk=pk)
    
    if request.method == 'POST':
        project.project_name = request.POST.get('project_name')
        project.description = request.POST.get('description', '')
        project.status = request.POST.get('status')
        project.planned_start_date = request.POST.get('planned_start_date')
        project.planned_end_date = request.POST.get('planned_end_date')
        project.project_manager_id = request.POST.get('project_manager') or None
        
        budget = request.POST.get('estimated_budget')
        project.estimated_budget = budget if budget else None
        
        actual_cost = request.POST.get('actual_cost')
        project.actual_cost = actual_cost if actual_cost else None
        
        project.save()
        
        # Update team members
        team_member_ids = request.POST.getlist('team_members')
        project.team_members.set(team_member_ids)
        
        messages.success(request, 'Project updated successfully!')
        return redirect('migrations:project_detail', pk=project.pk)
    
    # GET request - show form
    users = User.objects.all().order_by('username')
    context = {
        'project': project,
        'users': users,
        'status_choices': MigrationProject.STATUS_CHOICES,
    }
    return render(request, 'migrations/project_edit.html', context)


@login_required
def project_detail(request, pk):
    """Detailed view of a migration project"""
    if not check_migration_permission(request.user, 'can_view_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to view this project.</p>"
        )
    project = get_object_or_404(MigrationProject, pk=pk)
    
    # Get all migrations for this project
    migrations = project.migrations.select_related(
        'old_switch', 'new_switch', 'assigned_to'
    ).all()
    
    # Statistics by status
    status_stats = {}
    for status_choice in SwitchMigration.MIGRATION_STATUS_CHOICES:
        status_code = status_choice[0]
        count = migrations.filter(migration_status=status_code).count()
        status_stats[status_code] = count
    
    # Port migration statistics
    total_fiber_to_migrate = migrations.aggregate(Sum('fiber_ports_to_migrate'))['fiber_ports_to_migrate__sum'] or 0
    total_fiber_migrated = migrations.aggregate(Sum('fiber_ports_migrated'))['fiber_ports_migrated__sum'] or 0
    total_utp_to_migrate = migrations.aggregate(Sum('utp_ports_to_migrate'))['utp_ports_to_migrate__sum'] or 0
    total_utp_migrated = migrations.aggregate(Sum('utp_ports_migrated'))['utp_ports_migrated__sum'] or 0
    
    # Timeline
    timeline_events = []
    for migration in migrations.filter(actual_start_time__isnull=False).order_by('-actual_start_time')[:20]:
        timeline_events.append({
            'date': migration.actual_start_time,
            'title': f"Migration: {migration.old_switch.hostname}",
            'status': migration.migration_status,
            'migration': migration
        })
    
    # Issues
    open_issues = MigrationIssue.objects.filter(
        switch_migration__project=project,
        status__in=['Open', 'In Progress']
    ).count()
    
    context = {
        'project': project,
        'migrations': migrations,
        'status_stats': status_stats,
        'total_fiber_to_migrate': total_fiber_to_migrate,
        'total_fiber_migrated': total_fiber_migrated,
        'total_utp_to_migrate': total_utp_to_migrate,
        'total_utp_migrated': total_utp_migrated,
        'timeline_events': timeline_events,
        'open_issues': open_issues,
    }
    
    return render(request, 'migrations/project_detail.html', context)


# ====================
# MIGRATION VIEWS
# ====================

@login_required
def migration_detail(request, pk):
    """Detailed view of a single switch migration"""
    if not check_migration_permission(request.user, 'can_view_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to view migration details.</p>"
        )
    migration = get_object_or_404(
        SwitchMigration.objects.select_related(
            'old_switch', 'new_switch', 'project', 'assigned_to', 'backup_engineer'
        ),
        pk=pk
    )
    
    # Port mappings
    port_mappings = migration.port_mappings.all()
    
    # Checklist items
    checklist = migration.checklist_items.select_related('completed_by').all()
    
    # Issues
    issues = migration.issues.select_related('reported_by', 'assigned_to').all()
    
    # Activity log
    activity_log = migration.activity_logs.select_related('user')[:50]
    
    # User impacts
    user_impacts = migration.user_impacts.all()
    
    context = {
        'migration': migration,
        'port_mappings': port_mappings,
        'checklist': checklist,
        'issues': issues,
        'activity_log': activity_log,
        'user_impacts': user_impacts,
        'checklist_phases': ['Pre-Migration', 'During Migration', 'Post-Migration'],
    }
    
    return render(request, 'migrations/migration_detail.html', context)


@login_required
def create_migration(request, project_id):
    """Create new switch migration(s) - supports bulk creation"""
    if not check_migration_permission(request.user, 'can_add_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to create migrations.</p>"
        )
    project = get_object_or_404(MigrationProject, pk=project_id)
    
    if request.method == 'POST':
        # Get list of old switches (can be multiple)
        old_switch_ids = request.POST.getlist('old_switches')
        
        if not old_switch_ids:
            messages.error(request, 'Please select at least one switch to migrate.')
            return redirect('migrations:create_migration', project_id=project_id)
        
        # Get common data for all migrations
        scheduled_date = request.POST.get('scheduled_date')
        priority = request.POST.get('priority', 'Medium')
        assigned_to_id = request.POST.get('assigned_to') or None
        
        # Safely get integer values
        try:
            fiber_ports_to_migrate = int(request.POST.get('fiber_ports_to_migrate', 0) or 0)
            utp_ports_to_migrate = int(request.POST.get('utp_ports_to_migrate', 0) or 0)
        except (ValueError, TypeError):
            fiber_ports_to_migrate = 0
            utp_ports_to_migrate = 0
        
        pre_migration_notes = request.POST.get('pre_migration_notes', '')
        rollback_plan = request.POST.get('rollback_plan', '')
        
        created_count = 0
        failed_switches = []
        
        # Create migration for each selected switch
        for old_switch_id in old_switch_ids:
            try:
                # Try to get the switch
                try:
                    old_switch = Switch.objects.get(pk=old_switch_id, deleted_at__isnull=True)
                except Switch.DoesNotExist:
                    failed_switches.append(f"Switch ID {old_switch_id} (not found or deleted)")
                    continue
                
                # Check if migration already exists
                if SwitchMigration.objects.filter(project=project, old_switch=old_switch).exists():
                    failed_switches.append(f"{old_switch.hostname} (already exists in this project)")
                    continue
                
                # Create the migration
                migration = SwitchMigration.objects.create(
                    project=project,
                    old_switch=old_switch,
                    new_switch=None,  # Will be assigned later
                    scheduled_date=scheduled_date,
                    priority=priority,
                    assigned_to_id=assigned_to_id,
                    fiber_ports_to_migrate=fiber_ports_to_migrate,
                    utp_ports_to_migrate=utp_ports_to_migrate,
                    pre_migration_notes=pre_migration_notes,
                    rollback_plan=rollback_plan,
                    created_by=request.user
                )
                
                # Create default checklist
                create_default_checklist(migration)
                
                # Log activity
                MigrationActivityLog.objects.create(
                    switch_migration=migration,
                    user=request.user,
                    action='Migration Created',
                    description=f'Created migration for {old_switch.hostname}'
                )
                
                created_count += 1
                
            except Exception as e:
                failed_switches.append(f"Switch ID {old_switch_id} (Error: {str(e)})")
        
        # Show messages
        if created_count > 0:
            messages.success(request, f'✓ Successfully created {created_count} migration(s)!')
        
        if failed_switches:
            messages.warning(request, f'⚠ Failed to create migrations: {", ".join(failed_switches)}')
        
        if created_count == 0 and not failed_switches:
            messages.error(request, 'No migrations were created. Please check your selections.')
        
        return redirect('migrations:project_detail', pk=project_id)
    
    # GET request - show form
    available_old_switches = Switch.objects.filter(
        deleted_at__isnull=True,
        status='Active'
    ).exclude(
        migrations_as_old__project=project
    ).order_by('hostname')
    
    available_new_switches = Switch.objects.filter(
        deleted_at__isnull=True,
        status='Active'
    ).order_by('hostname')
    
    users = User.objects.all().order_by('username')
    
    context = {
        'project': project,
        'available_old_switches': available_old_switches,
        'available_new_switches': available_new_switches,
        'users': users,
    }
    
    return render(request, 'migrations/migration_create.html', context)


@login_required
def edit_migration(request, pk):
    """Edit a switch migration"""
    if not check_migration_permission(request.user, 'can_edit_migrations'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to edit migrations.</p>"
        )
    migration = get_object_or_404(SwitchMigration, pk=pk)
    
    if request.method == 'POST':
        # Update basic fields
        migration.new_switch_id = request.POST.get('new_switch') or None
        migration.scheduled_date = request.POST.get('scheduled_date')
        migration.priority = request.POST.get('priority')
        migration.assigned_to_id = request.POST.get('assigned_to') or None
        migration.backup_engineer_id = request.POST.get('backup_engineer') or None
        
        # Update port counts
        migration.fiber_ports_to_migrate = request.POST.get('fiber_ports_to_migrate', 0)
        migration.utp_ports_to_migrate = request.POST.get('utp_ports_to_migrate', 0)
        
        # Update notes
        migration.pre_migration_notes = request.POST.get('pre_migration_notes', '')
        migration.migration_notes = request.POST.get('migration_notes', '')
        migration.post_migration_notes = request.POST.get('post_migration_notes', '')
        migration.rollback_plan = request.POST.get('rollback_plan', '')
        migration.issues_encountered = request.POST.get('issues_encountered', '')
        
        # Update downtime estimates
        estimated = request.POST.get('estimated_downtime')
        migration.estimated_downtime = int(estimated) if estimated else None
        
        migration.save()
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=migration,
            user=request.user,
            action='Migration Updated',
            description='Migration details updated'
        )
        
        messages.success(request, 'Migration updated successfully!')
        return redirect('migrations:migration_detail', pk=pk)
    
    # GET request - show form
    available_new_switches = Switch.objects.filter(deleted_at__isnull=True, status='Active')
    users = User.objects.all().order_by('username')
    
    context = {
        'migration': migration,
        'available_new_switches': available_new_switches,
        'users': users,
        'priority_choices': SwitchMigration.PRIORITY_CHOICES,
        'status_choices': SwitchMigration.MIGRATION_STATUS_CHOICES,
    }
    return render(request, 'migrations/migration_edit.html', context)


def create_default_checklist(migration):
    """Create default checklist items for a migration"""
    checklist_items = [
        # Pre-Migration
        ('Pre-Migration', 1, 'Backup current switch configuration'),
        ('Pre-Migration', 2, 'Document all port connections and VLANs'),
        ('Pre-Migration', 3, 'Notify all affected users/departments'),
        ('Pre-Migration', 4, 'Verify new switch is properly configured'),
        ('Pre-Migration', 5, 'Test new switch in lab environment'),
        ('Pre-Migration', 6, 'Prepare rollback plan'),
        ('Pre-Migration', 7, 'Schedule maintenance window'),
        
        # During Migration
        ('During Migration', 1, 'Disconnect old switch from network'),
        ('During Migration', 2, 'Install and rack new switch'),
        ('During Migration', 3, 'Configure management IP and basic settings'),
        ('During Migration', 4, 'Migrate fiber connections'),
        ('During Migration', 5, 'Migrate UTP connections'),
        ('During Migration', 6, 'Verify all port lights and connections'),
        ('During Migration', 7, 'Test connectivity for critical services'),
        
        # Post-Migration
        ('Post-Migration', 1, 'Verify all ports are operational'),
        ('Post-Migration', 2, 'Test network connectivity from user locations'),
        ('Post-Migration', 3, 'Monitor switch performance for 1 hour'),
        ('Post-Migration', 4, 'Update network documentation'),
        ('Post-Migration', 5, 'Gather user feedback'),
        ('Post-Migration', 6, 'Mark old switch for decommission'),
        ('Post-Migration', 7, 'Close migration ticket'),
    ]
    
    for phase, order, description in checklist_items:
        MigrationChecklist.objects.create(
            switch_migration=migration,
            phase=phase,
            item_order=order,
            description=description
        )


@login_required
def update_migration_status(request, pk):
    """Update migration status"""
    if not check_migration_permission(request.user, 'can_update_migration_status'):
        messages.error(request, "You don't have permission to update migration status.")
        return redirect('migrations:migration_detail', pk=pk)
    migration = get_object_or_404(SwitchMigration, pk=pk)
    
    if request.method == 'POST':
        old_status = migration.migration_status
        new_status = request.POST.get('status')
        
        migration.migration_status = new_status
        
        # Update timestamps based on status
        if new_status == 'In Progress' and not migration.actual_start_time:
            migration.actual_start_time = timezone.now()
        elif new_status == 'Completed' and not migration.actual_end_time:
            migration.actual_end_time = timezone.now()
        
        migration.save()
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=migration,
            user=request.user,
            action='Status Changed',
            description=f'Status changed from {old_status} to {new_status}'
        )
        
        messages.success(request, f'Migration status updated to {new_status}')
    
    return redirect('migrations:migration_detail', pk=pk)


@login_required
def update_port_migration(request, pk):
    """Update port migration progress"""
    if not check_migration_permission(request.user, 'can_update_migration_status'):
        messages.error(request, "You don't have permission to update port migration progress.")
        return redirect('migrations:migration_detail', pk=pk)
    migration = get_object_or_404(SwitchMigration, pk=pk)
    
    if request.method == 'POST':
        fiber_migrated = int(request.POST.get('fiber_ports_migrated', 0))
        utp_migrated = int(request.POST.get('utp_ports_migrated', 0))
        
        migration.fiber_ports_migrated = fiber_migrated
        migration.utp_ports_migrated = utp_migrated
        migration.save()
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=migration,
            user=request.user,
            action='Port Migration Updated',
            description=f'Updated port counts: {fiber_migrated} fiber, {utp_migrated} UTP'
        )
        
        messages.success(request, 'Port migration progress updated')
    
    return redirect('migrations:migration_detail', pk=pk)


# ====================
# PORT MAPPING VIEWS
# ====================

@login_required
def add_port_mapping(request, migration_id):
    """Add a port mapping"""
    if not check_migration_permission(request.user, 'can_manage_port_mappings'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to manage port mappings.</p>"
        )
    migration = get_object_or_404(SwitchMigration, pk=migration_id)
    
    if request.method == 'POST':
        PortMigrationMapping.objects.create(
            switch_migration=migration,
            old_port_number=request.POST.get('old_port_number'),
            old_port_type=request.POST.get('old_port_type'),
            old_port_description=request.POST.get('old_port_description', ''),
            old_vlan=request.POST.get('old_vlan', ''),
            new_port_number=request.POST.get('new_port_number', ''),
            new_port_type=request.POST.get('new_port_type'),
            new_vlan=request.POST.get('new_vlan', ''),
            connected_device=request.POST.get('connected_device', ''),
            user_department=request.POST.get('user_department', ''),
            user_contact=request.POST.get('user_contact', ''),
            notes=request.POST.get('notes', '')
        )
        
        messages.success(request, 'Port mapping added successfully!')
        return redirect('migrations:migration_detail', pk=migration_id)
    
    context = {
        'migration': migration,
    }
    return render(request, 'migrations/port_mapping_add.html', context)


@login_required
def edit_port_mapping(request, pk):
    """Edit a port mapping"""
    if not check_migration_permission(request.user, 'can_manage_port_mappings'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to edit port mappings.</p>"
        )
    mapping = get_object_or_404(PortMigrationMapping, pk=pk)
    
    if request.method == 'POST':
        mapping.old_port_number = request.POST.get('old_port_number')
        mapping.old_port_type = request.POST.get('old_port_type')
        mapping.old_port_description = request.POST.get('old_port_description', '')
        mapping.old_vlan = request.POST.get('old_vlan', '')
        mapping.new_port_number = request.POST.get('new_port_number', '')
        mapping.new_port_type = request.POST.get('new_port_type')
        mapping.new_vlan = request.POST.get('new_vlan', '')
        mapping.connected_device = request.POST.get('connected_device', '')
        mapping.user_department = request.POST.get('user_department', '')
        mapping.user_contact = request.POST.get('user_contact', '')
        mapping.is_migrated = request.POST.get('is_migrated') == 'on'
        mapping.is_tested = request.POST.get('is_tested') == 'on'
        mapping.test_result = request.POST.get('test_result', 'Pending')
        mapping.test_notes = request.POST.get('test_notes', '')
        mapping.notes = request.POST.get('notes', '')
        
        if mapping.is_migrated and not mapping.migration_date:
            mapping.migration_date = timezone.now()
            mapping.migrated_by = request.user
        
        mapping.save()
        
        messages.success(request, 'Port mapping updated successfully!')
        return redirect('migrations:migration_detail', pk=mapping.switch_migration.pk)
    
    context = {
        'mapping': mapping,
    }
    return render(request, 'migrations/port_mapping_edit.html', context)


@login_required
def toggle_port_status(request, pk):
    """Toggle port migration status via AJAX"""
    if request.method == 'POST':
        mapping = get_object_or_404(PortMigrationMapping, pk=pk)
        data = json.loads(request.body)
        
        mapping.is_migrated = data.get('is_migrated', False)
        if mapping.is_migrated and not mapping.migration_date:
            mapping.migration_date = timezone.now()
            mapping.migrated_by = request.user
        
        mapping.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def export_port_mappings(request, pk):
    """Export port mappings to CSV"""
    if not check_migration_permission(request.user, 'can_export_migration_reports'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to export port mappings.</p>"
        )
    migration = get_object_or_404(SwitchMigration, pk=pk)
    
    response = HttpResponse(content_type='text/csv')
    filename = f'port_mappings_{migration.old_switch.hostname}_{timezone.now().strftime("%Y%m%d")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Old Port', 'Type', 'Old VLAN', 'New Port', 'New VLAN',
        'Connected Device', 'Department', 'Contact', 'Migrated', 
        'Test Result', 'Notes'
    ])
    
    for mapping in migration.port_mappings.all():
        writer.writerow([
            mapping.old_port_number,
            mapping.old_port_type,
            mapping.old_vlan,
            mapping.new_port_number,
            mapping.new_vlan,
            mapping.connected_device,
            mapping.user_department,
            mapping.user_contact,
            'Yes' if mapping.is_migrated else 'No',
            mapping.test_result,
            mapping.notes
        ])
    
    return response


# ====================
# CHECKLIST VIEWS
# ====================

@login_required
def toggle_checklist_item(request, pk):
    """Toggle checklist item completion via AJAX"""
    if request.method == 'POST':
        item = get_object_or_404(MigrationChecklist, pk=pk)
        data = json.loads(request.body)
        
        item.is_completed = data.get('is_completed', False)
        if item.is_completed:
            item.completed_at = timezone.now()
            item.completed_by = request.user
        else:
            item.completed_at = None
            item.completed_by = None
        
        item.save()
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=item.switch_migration,
            user=request.user,
            action='Checklist Updated',
            description=f'{"Completed" if item.is_completed else "Unchecked"}: {item.description}'
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


# ====================
# ISSUE VIEWS
# ====================

@login_required
def add_issue(request, migration_id):
    """Add a new issue"""
    if not check_migration_permission(request.user, 'can_manage_issues'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to report issues.</p>"
        )
    migration = get_object_or_404(SwitchMigration, pk=migration_id)
    
    if request.method == 'POST':
        issue = MigrationIssue.objects.create(
            switch_migration=migration,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            severity=request.POST.get('severity', 'Medium'),
            status='Open',
            reported_by=request.user,
            assigned_to_id=request.POST.get('assigned_to') or None
        )
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=migration,
            user=request.user,
            action='Issue Reported',
            description=f'New issue: {issue.title}'
        )
        
        messages.success(request, 'Issue reported successfully!')
        return redirect('migrations:migration_detail', pk=migration_id)
    
    users = User.objects.all().order_by('username')
    context = {
        'migration': migration,
        'users': users,
        'severity_choices': MigrationIssue.SEVERITY_CHOICES,
    }
    return render(request, 'migrations/issue_add.html', context)


@login_required
def update_issue(request, pk):
    """Update an issue"""
    if not check_migration_permission(request.user, 'can_manage_issues'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to update issues.</p>"
        )
    issue = get_object_or_404(MigrationIssue, pk=pk)
    
    if request.method == 'POST':
        old_status = issue.status
        
        issue.title = request.POST.get('title')
        issue.description = request.POST.get('description')
        issue.severity = request.POST.get('severity')
        issue.status = request.POST.get('status')
        issue.assigned_to_id = request.POST.get('assigned_to') or None
        issue.resolution = request.POST.get('resolution', '')
        
        if issue.status == 'Resolved' and not issue.resolved_at:
            issue.resolved_at = timezone.now()
            issue.resolved_by = request.user
        
        issue.save()
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=issue.switch_migration,
            user=request.user,
            action='Issue Updated',
            description=f'Issue "{issue.title}" status: {old_status} → {issue.status}'
        )
        
        messages.success(request, 'Issue updated successfully!')
        return redirect('migrations:migration_detail', pk=issue.switch_migration.pk)
    
    users = User.objects.all().order_by('username')
    context = {
        'issue': issue,
        'users': users,
        'severity_choices': MigrationIssue.SEVERITY_CHOICES,
        'status_choices': MigrationIssue.STATUS_CHOICES,
    }
    return render(request, 'migrations/issue_edit.html', context)


# ====================
# USER IMPACT VIEWS
# ====================

@login_required
def add_user_impact(request, migration_id):
    """Add user impact assessment"""
    if not check_migration_permission(request.user, 'can_manage_user_impact'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to manage user impact assessments.</p>"
        )
    migration = get_object_or_404(SwitchMigration, pk=migration_id)
    
    if request.method == 'POST':
        impact = UserImpactAssessment.objects.create(
            switch_migration=migration,
            department_name=request.POST.get('department_name'),
            contact_person=request.POST.get('contact_person'),
            contact_email=request.POST.get('contact_email'),
            contact_phone=request.POST.get('contact_phone', ''),
            number_of_users_affected=request.POST.get('number_of_users_affected', 0),
            critical_services=request.POST.get('critical_services', '')
        )
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=migration,
            user=request.user,
            action='User Impact Added',
            description=f'Added impact for {impact.department_name}'
        )
        
        messages.success(request, 'User impact assessment added!')
        return redirect('migrations:migration_detail', pk=migration_id)
    
    context = {
        'migration': migration,
    }
    return render(request, 'migrations/user_impact_add.html', context)

@login_required
def send_notification(request, pk):
    """Mark notification as sent"""
    impact = get_object_or_404(UserImpactAssessment, pk=pk)
    
    if request.method == 'POST':
        impact.notified = True
        impact.notification_sent_at = timezone.now()
        impact.save()
        
        # Log activity
        MigrationActivityLog.objects.create(
            switch_migration=impact.switch_migration,
            user=request.user,
            action='Notification Sent',
            description=f'Notified {impact.department_name}'
        )
        
        messages.success(request, f'Notification marked as sent to {impact.department_name}')
        return redirect('migrations:migration_detail', pk=impact.switch_migration.pk)
    
    return redirect('migrations:migration_detail', pk=impact.switch_migration.pk)


# ====================
# EXPORT VIEWS
# ====================

@login_required
def export_migration_report(request, project_id):
    """Export migration report to CSV"""
    if not check_migration_permission(request.user, 'can_export_migration_reports'):
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1>"
            "<p>You don't have permission to export migration reports.</p>"
        )
    project = get_object_or_404(MigrationProject, pk=project_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="migration_report_{project.project_name}_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Old Switch', 'Old IP', 'New Switch', 'New IP', 'Status', 
        'Fiber To Migrate', 'Fiber Migrated', 'UTP To Migrate', 'UTP Migrated',
        'Scheduled Date', 'Actual Start', 'Actual End', 'Assigned To'
    ])

    migrations = project.migrations.select_related('old_switch', 'new_switch', 'assigned_to').all()

    for mig in migrations:
        writer.writerow([
            mig.old_switch.hostname if mig.old_switch else '',
            mig.old_switch.ip_address if mig.old_switch else '',
            mig.new_switch.hostname if mig.new_switch else 'TBD',
            mig.new_switch.ip_address if mig.new_switch else '',
            mig.migration_status,
            mig.fiber_ports_to_migrate,
            mig.fiber_ports_migrated,
            mig.utp_ports_to_migrate,
            mig.utp_ports_migrated,
            mig.scheduled_date,
            mig.actual_start_time or '',
            mig.actual_end_time or '',
            mig.assigned_to.username if mig.assigned_to else ''
        ])

    return response