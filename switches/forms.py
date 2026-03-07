# switches/forms.py
from django import forms
from .models import Switch

class SwitchForm(forms.ModelForm):
    class Meta:
        model = Switch
        exclude = ['deleted_at', 'deleted_by', 'created_at', 'updated_at']
        widgets = {
            # Basic Information
            'hostname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SW-CORE-01'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.1'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SN123456'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cisco 9500'}),
            'vendor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cisco'}),
            'it_tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IT-001'}),
            
            # Location Information
            'building_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Building-A'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Server Room 101'}),
            'communication_room_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CR-101'}),
            'cabinet_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CAB-01'}),
            'cabinet_tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TAG-001'}),
            
            # Technical Specifications
            'switch_role': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            
            # Line Cards and Ports
            'no_of_line_cards_fiber': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'no_of_line_cards_utp': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_ports_fiber': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_ports_utp': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'port_type': forms.Select(attrs={'class': 'form-select'}),
            'no_of_used_ports': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            
            # Power Supplies
            'no_of_power_supplies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'used_power_supplies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            
            # Additional Information
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
            
            # Stack Information
            'is_stack': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stack_priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 9}),
            'stack_member_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 9}),
        }
        
        labels = {
            'hostname': 'Hostname',
            'ip_address': 'IP Address',
            'serial_number': 'Serial Number',
            'model': 'Model',
            'vendor': 'Vendor',
            'it_tag': 'IT Tag',
            'building_no': 'Building No',
            'location': 'Location',
            'communication_room_no': 'Communication Room No',
            'cabinet_no': 'Cabinet No',
            'cabinet_tag': 'Cabinet Tag',
            'switch_role': 'Switch Role',
            'status': 'Status',
            'no_of_line_cards_fiber': 'Line Cards (Fiber)',
            'no_of_line_cards_utp': 'Line Cards (UTP)',
            'total_ports_fiber': 'Total Ports (Fiber)',
            'total_ports_utp': 'Total Ports (UTP)',
            'port_type': '24P or 48P',
            'no_of_used_ports': 'No. of Used Ports',
            'no_of_power_supplies': 'No. of Power Supplies',
            'used_power_supplies': 'Used Power Supplies',
            'remarks': 'Remarks',
            'is_stack': 'Is Stack',
            'stack_priority': 'Stack Priority',
            'stack_member_number': 'Stack Member Number',
        }
        
        help_texts = {
            'hostname': 'Unique hostname for the switch',
            'serial_number': 'Must be unique across all switches',
            'stack_priority': '1 = Master, 2-9 = Member priority',
            'stack_member_number': 'Member position in the stack (1-9)',
        }


class StackMemberForm(forms.Form):
    """Form for adding stack members during switch creation"""
    serial_number = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serial Number'})
    )
    model = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model'})
    )
    stack_priority = forms.IntegerField(
        min_value=1,
        max_value=9,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Priority'})
    )