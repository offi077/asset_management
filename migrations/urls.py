from django.urls import path
from . import views

app_name = 'migrations'

urlpatterns = [
    # Dashboard
    path('', views.migration_dashboard, name='dashboard'),
    
    # Projects
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/export/', views.export_migration_report, name='export_report'),
    
    # Migrations
    path('migrations/create/<int:project_id>/', views.create_migration, name='create_migration'),
    path('migrations/<int:pk>/', views.migration_detail, name='migration_detail'),
    path('migrations/<int:pk>/edit/', views.edit_migration, name='migration_edit'),
    path('migrations/<int:pk>/status/', views.update_migration_status, name='update_status'),
    path('migrations/<int:pk>/ports/', views.update_port_migration, name='update_port_progress'),
    
    # Port Mappings
    path('migrations/<int:migration_id>/ports/add/', views.add_port_mapping, name='add_port_mapping'),
    path('migrations/<int:pk>/ports/export/', views.export_port_mappings, name='export_port_mappings'),
    path('port-mappings/<int:pk>/edit/', views.edit_port_mapping, name='edit_port_mapping'),
    path('port-mappings/<int:pk>/toggle/', views.toggle_port_status, name='toggle_port_status'),
    
    # Checklist
    path('checklist/<int:pk>/toggle/', views.toggle_checklist_item, name='toggle_checklist'),
    
    # Issues
    path('migrations/<int:migration_id>/issues/add/', views.add_issue, name='add_issue'),
    path('issues/<int:pk>/update/', views.update_issue, name='update_issue'),
    
    # User Impact
    path('migrations/<int:migration_id>/users/add/', views.add_user_impact, name='add_user_impact'),
    path('user-impact/<int:pk>/notify/', views.send_notification, name='send_notification'),
]