# urls.py
from django.urls import path
from . import views

app_name = 'switches'

urlpatterns = [
   path('', views.switch_list, name='list'),
    path('create/', views.switch_create, name='create'),
    path('<int:pk>/', views.switch_detail, name='detail'),
    path('<int:pk>/edit/', views.switch_edit, name='edit'),
    path('<int:pk>/delete/', views.switch_delete, name='delete'),
    path('<int:pk>/restore/', views.switch_restore, name='restore'),
    path('<int:pk>/permanent-delete/', views.switch_permanent_delete, name='permanent_delete'),
    path('delete-stack/', views.switch_delete_stack, name='delete_stack'),
    path('bulk-delete/', views.switch_bulk_delete, name='bulk_delete'),
    path('bulk-restore/', views.switch_bulk_restore, name='bulk_restore'),
    path('export/', views.switch_export, name='export'),
    path('import/', views.switch_import, name='import'),
    path('download-sample/', views.download_sample_csv, name='download_sample'),
    path('update-columns/', views.update_column_preferences, name='update_columns'),
]