from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Switch, ColumnPreference
from .forms import SwitchForm
from .decorators import can_view_switches, can_add_switches, can_edit_switches, can_delete_switches, can_export_switches, can_import_switches, can_restore_switches
import csv
import io
from datetime import datetime
import json

@can_view_switches
def switch_list(request):
    # Get or create column preferences
    if request.user.is_authenticated:
        column_pref, created = ColumnPreference.objects.get_or_create(user=request.user)
        visible_columns = column_pref.get_visible_columns()
    else:
        visible_columns = ColumnPreference.DEFAULT_COLUMNS
    
    # Get all switches
    show_deleted = request.GET.get('show_deleted', 'false') == 'true'
    if show_deleted:
        switches = Switch.all_objects.all()
    else:
        switches = Switch.objects.all()
    
    # Global search
    q = request.GET.get('q', '').strip()
    if q:
        switches = switches.filter(
            Q(hostname__icontains=q) |
            Q(ip_address__icontains=q) |
            Q(serial_number__icontains=q) |
            Q(model__icontains=q) |
            Q(vendor__icontains=q) |
            Q(building_no__icontains=q) |
            Q(location__icontains=q) |
            Q(it_tag__icontains=q) |
            Q(cabinet_no__icontains=q) |
            Q(remarks__icontains=q)
        )
    
    # Column-specific filters
    filters = {
        'hostname': request.GET.get('f_hostname', ''),
        'ip_address': request.GET.get('f_ip_address', ''),
        'serial_number': request.GET.get('f_serial_number', ''),
        'model': request.GET.get('f_model', ''),
        'vendor': request.GET.get('f_vendor', ''),
        'switch_role': request.GET.get('f_switch_role', ''),
        'building_no': request.GET.get('f_building_no', ''),
        'location': request.GET.get('f_location', ''),
        'status': request.GET.get('f_status', ''),
        'port_type': request.GET.get('f_port_type', ''),
    }
    
    for field, value in filters.items():
        if value:
            switches = switches.filter(**{f"{field}__icontains": value})
    
    # Order switches
    switches = switches.order_by('building_no', 'hostname', 'stack_member_number')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(switches, 50)  # 50 items per page
    switches_page = paginator.get_page(page)
    
    # Statistics
    stats = {
        'total': Switch.objects.count(),
        'active': Switch.objects.filter(status='Active').count(),
        'inactive': Switch.objects.filter(status='Inactive').count(),
        'deleted': Switch.all_objects.deleted_only().count(),
        'stacks': Switch.objects.filter(is_stack=True).values('hostname', 'ip_address').distinct().count(),
    }
    
    context = {
        'switches': switches_page,
        'visible_columns': visible_columns,
        'all_columns': ColumnPreference.ALL_COLUMNS,
        'q': q,
        'filters': filters,
        'show_deleted': show_deleted,
        'stats': stats,
        'role_choices': Switch.ROLE_CHOICES,
        'status_choices': Switch.STATUS_CHOICES,
        'port_type_choices': Switch.PORT_TYPE_CHOICES,
    }
    
    return render(request, 'switches/switch_list.html', context)
pass

@can_view_switches
@require_POST
def update_column_preferences(request):
    """Update user's column visibility preferences"""
    if request.user.is_authenticated:
        column_pref, created = ColumnPreference.objects.get_or_create(user=request.user)
        
        # Get selected columns from POST data
        selected_columns = request.POST.getlist('columns[]')
        column_pref.visible_columns = selected_columns
        column_pref.save()
        
        return JsonResponse({'status': 'success', 'message': 'Column preferences updated'})
    
    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=403)

@can_view_switches
def switch_detail(request, pk):
    """Detailed view of a single switch"""
    switch = get_object_or_404(Switch.all_objects, pk=pk)
    
    # Get related stack members if this is a stack
    stack_members = None
    if switch.is_stack:
        stack_members = Switch.all_objects.filter(
            hostname=switch.hostname,
            ip_address=switch.ip_address
        ).order_by('stack_member_number')
    
    context = {
        'switch': switch,
        'stack_members': stack_members,
    }
    
    return render(request, 'switches/switch_detail.html', context)

@can_export_switches
def switch_export(request):
    """Export switches to CSV with all columns"""
    
    # Check if this is a POST request with selected items
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_switches[]')
        
        if not selected_ids:
            messages.error(request, 'Please select at least one switch to export.')
            return redirect('switches:list')
        
        switches = Switch.all_objects.filter(id__in=selected_ids)
        filename = f'switches_selected_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    else:
        # GET request - export by type
        export_type = request.GET.get('type', 'active')
        
        if export_type == 'deleted':
            switches = Switch.all_objects.deleted_only()
            filename = f'switches_deleted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        elif export_type == 'all':
            switches = Switch.all_objects.all()
            filename = f'switches_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        else:
            switches = Switch.objects.all()
            filename = f'switches_active_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header with all fields
    writer.writerow([
        'S.No', 'Hostname', 'IP Address', 'Serial Number', 'Model', 'Vendor',
        'Line Cards (Fiber)', 'Line Cards (UTP)', 'Total Ports (Fiber)',
        'Total Ports (UTP)', '24P or 48P', 'Used Ports', 'Free Ports',
        'No. of Power Supplies', 'Used Power Supplies', 'Remarks',
        'Switch Role', 'Building No', 'IT Tag', 'Location',
        'Communication Room No', 'Cabinet No', 'Cabinet Tag',
        'Status', 'Is Stack', 'Stack Member', 'Stack Priority',
        'Created At', 'Updated At', 'Deleted At'
    ])
    
    # Write data
    for idx, switch in enumerate(switches.order_by('building_no', 'hostname', 'stack_member_number'), 1):
        writer.writerow([
            idx,
            switch.hostname,
            switch.ip_address,
            switch.serial_number,
            switch.model,
            switch.vendor,
            switch.no_of_line_cards_fiber,
            switch.no_of_line_cards_utp,
            switch.total_ports_fiber,
            switch.total_ports_utp,
            switch.port_type,
            switch.no_of_used_ports,
            switch.free_ports,
            switch.no_of_power_supplies,
            switch.used_power_supplies,
            switch.remarks,
            switch.get_switch_role_display() if switch.switch_role else '',
            switch.building_no,
            switch.it_tag,
            switch.location,
            switch.communication_room_no,
            switch.cabinet_no,
            switch.cabinet_tag,
            switch.status,
            'Yes' if switch.is_stack else 'No',
            switch.stack_member_number if switch.is_stack else '',
            switch.stack_priority if switch.is_stack else '',
            switch.created_at.strftime('%Y-%m-%d %H:%M:%S') if switch.created_at else '',
            switch.updated_at.strftime('%Y-%m-%d %H:%M:%S') if switch.updated_at else '',
            switch.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if switch.deleted_at else '',
        ])
    
    return response
pass

@can_delete_switches
@require_POST
def switch_bulk_delete(request):
    """Bulk soft delete selected switches"""
    selected_ids = request.POST.getlist('selected_switches[]')
    
    if not selected_ids:
        messages.error(request, 'Please select at least one switch to delete.')
        return redirect('switches:list')
    
    try:
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        switches = Switch.objects.filter(id__in=selected_ids)
        
        count = 0
        for switch in switches:
            switch.soft_delete(user=user)
            count += 1
        
        messages.success(request, f'Successfully deleted {count} switch(es).')
    except Exception as e:
        messages.error(request, f'Error deleting switches: {str(e)}')
    
    return redirect('switches:list')
pass

@can_restore_switches
@require_POST
def switch_bulk_restore(request):
    """Bulk restore selected switches"""
    selected_ids = request.POST.getlist('selected_switches[]')
    
    if not selected_ids:
        messages.error(request, 'Please select at least one switch to restore.')
        return redirect('switches:list')
    
    try:
        switches = Switch.all_objects.filter(id__in=selected_ids, deleted_at__isnull=False)
        
        count = 0
        for switch in switches:
            switch.restore()
            count += 1
        
        messages.success(request, f'Successfully restored {count} switch(es).')
    except Exception as e:
        messages.error(request, f'Error restoring switches: {str(e)}')
    
    return redirect('switches:list')
pass

@can_add_switches
# Keep all other existing view functions...
def switch_create(request):
    if request.method == 'POST':
        form = SwitchForm(request.POST)
        add_as_stack = request.POST.get('add_as_stack') == 'on'
        
        if add_as_stack:
            number_of_members = int(request.POST.get('number_of_members', 2))
            hostname = request.POST.get('hostname')
            ip_address = request.POST.get('ip_address')
            location = request.POST.get('location', '')
            status = request.POST.get('status', 'Active')
            
            try:
                for i in range(1, number_of_members + 1):
                    serial = request.POST.get(f'serial_number_{i}', '')
                    model = request.POST.get(f'model_{i}', '')
                    priority = request.POST.get(f'stack_priority_{i}', i)
                    
                    if serial:
                        Switch.objects.create(
                            hostname=hostname,
                            ip_address=ip_address,
                            location=location,
                            model=model,
                            serial_number=serial,
                            status=status,
                            is_stack=True,
                            stack_priority=int(priority),
                            stack_member_number=i
                        )
                
                messages.success(request, f'Successfully created stack with {number_of_members} members!')
                return redirect(reverse('switches:list'))
                
            except Exception as e:
                messages.error(request, f'Error creating stack: {str(e)}')
        else:
            if form.is_valid():
                switch = form.save(commit=False)
                switch.is_stack = False
                switch.stack_member_number = 1
                switch.save()
                messages.success(request, 'Switch added successfully!')
                return redirect(reverse('switches:list'))
    else:
        form = SwitchForm()
    
    return render(request, 'switches/switch_form.html', {
        'form': form, 
        'title': 'Add Switch'
    })
pass

@can_edit_switches
def switch_edit(request, pk):
    """Edit a single switch"""
    switch = get_object_or_404(Switch, pk=pk)
    
    if request.method == 'POST':
        form = SwitchForm(request.POST, instance=switch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Switch updated successfully!')
            return redirect(reverse('switches:list'))
    else:
        form = SwitchForm(instance=switch)
    
    return render(request, 'switches/switch_form.html', {
        'form': form,
        'title': 'Edit Switch',
        'switch': switch
    })
pass

@can_delete_switches
@require_POST
def switch_delete(request, pk):
    """Soft delete a single switch"""
    switch = get_object_or_404(Switch, pk=pk)
    
    try:
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        switch.soft_delete(user=user)
        messages.success(request, f'Switch "{switch.hostname}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting switch: {str(e)}')
    
    return redirect(reverse('switches:list'))
pass

@can_delete_switches
@require_POST
def switch_delete_stack(request):
    """Soft delete entire stack"""
    hostname = request.POST.get('hostname')
    ip_address = request.POST.get('ip_address')
    
    try:
        switches = Switch.objects.filter(hostname=hostname, ip_address=ip_address)
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        
        count = 0
        for switch in switches:
            switch.soft_delete(user=user)
            count += 1
        
        messages.success(request, f'Stack "{hostname}" with {count} members deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting stack: {str(e)}')
    
    return redirect(reverse('switches:list'))
pass

@can_restore_switches
@require_POST
def switch_restore(request, pk):
    """Restore a soft deleted switch"""
    switch = get_object_or_404(Switch.all_objects, pk=pk)
    
    try:
        switch.restore()
        messages.success(request, f'Switch "{switch.hostname}" restored successfully!')
    except Exception as e:
        messages.error(request, f'Error restoring switch: {str(e)}')
    
    return redirect(reverse('switches:list'))
pass

@can_delete_switches
@require_POST
def switch_permanent_delete(request, pk):
    """Permanently delete a switch from database"""
    switch = get_object_or_404(Switch.all_objects, pk=pk)
    
    try:
        hostname = switch.hostname
        switch.delete()  # Hard delete
        messages.success(request, f'Switch "{hostname}" permanently deleted!')
    except Exception as e:
        messages.error(request, f'Error permanently deleting switch: {str(e)}')
    
    return redirect(reverse('switches:list'))
pass

@can_import_switches
def switch_import(request):
    """Import switches from CSV"""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('switches:import')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    Switch.objects.create(
                        hostname=row.get('hostname', '').strip(),
                        ip_address=row.get('ip_address', '').strip(),
                        serial_number=row.get('serial_number', '').strip(),
                        model=row.get('model', '').strip(),
                        vendor=row.get('vendor', '').strip(),
                        no_of_line_cards_fiber=int(row.get('no_of_line_cards_fiber', 0) or 0),
                        no_of_line_cards_utp=int(row.get('no_of_line_cards_utp', 0) or 0),
                        total_ports_fiber=int(row.get('total_ports_fiber', 0) or 0),
                        total_ports_utp=int(row.get('total_ports_utp', 0) or 0),
                        port_type=row.get('port_type', '').strip(),
                        no_of_used_ports=int(row.get('no_of_used_ports', 0) or 0),
                        no_of_power_supplies=int(row.get('no_of_power_supplies', 0) or 0),
                        used_power_supplies=int(row.get('used_power_supplies', 0) or 0),
                        remarks=row.get('remarks', '').strip(),
                        switch_role=row.get('switch_role', '').strip(),
                        building_no=row.get('building_no', '').strip(),
                        it_tag=row.get('it_tag', '').strip(),
                        location=row.get('location', '').strip(),
                        communication_room_no=row.get('communication_room_no', '').strip(),
                        cabinet_no=row.get('cabinet_no', '').strip(),
                        cabinet_tag=row.get('cabinet_tag', '').strip(),
                        status=row.get('status', 'Active').strip(),
                        is_stack=(row.get('is_stack', 'no').lower() in ['yes', 'true', '1']),
                        stack_member_number=int(row.get('stack_member_number', 1) or 1),
                        stack_priority=int(row.get('stack_priority', 1) or 1),
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
            
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} switch(es).')
            
            if error_count > 0:
                error_message = f'Failed to import {error_count} switch(es). '
                if len(errors) <= 5:
                    error_message += ' '.join(errors)
                else:
                    error_message += ' '.join(errors[:5]) + f' ...and {len(errors) - 5} more errors.'
                messages.error(request, error_message)
            
            return redirect('switches:list')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
            return redirect('switches:import')
    
    return render(request, 'switches/switch_import.html')
pass

def download_sample_csv(request):
    """Download CSV template with all fields"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="switch_import_template.csv"'
    
    writer = csv.writer(response)
    
    writer.writerow([
        'hostname', 'ip_address', 'serial_number', 'model', 'vendor',
        'no_of_line_cards_fiber', 'no_of_line_cards_utp',
        'total_ports_fiber', 'total_ports_utp', 'port_type',
        'no_of_used_ports', 'no_of_power_supplies', 'used_power_supplies',
        'remarks', 'switch_role', 'building_no', 'it_tag', 'location',
        'communication_room_no', 'cabinet_no', 'cabinet_tag',
        'status', 'is_stack', 'stack_member_number', 'stack_priority'
    ])
    
    # Sample data
    writer.writerow([
        'SW-CORE-01', '192.168.1.1', 'SN123456', 'Cisco 9500', 'Cisco',
        '2', '0', '4', '48', '48P',
        '35', '2', '2', 'Core switch for data center', 'core',
        'Building-A', 'IT-001', 'Server Room', 'Room-101', 'Cab-01', 'TAG-001',
        'Active', 'yes', '1', '1'
    ])
    
    writer.writerow([
        'SW-ACCESS-01', '192.168.1.10', 'SN789012', 'Cisco 2960X', 'Cisco',
        '0', '0', '0', '24', '24P',
        '20', '1', '1', 'Access switch floor 2', 'access',
        'Building-A', 'IT-002', 'Floor 2 IDF', 'Room-205', 'Cab-02', 'TAG-002',
        'Active', 'no', '1', '1'
    ])
    
    return response
pass