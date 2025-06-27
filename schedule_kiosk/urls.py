from django.urls import path
from . import views

urlpatterns = [
    path('', views.KioskView.as_view(), name='kiosk'),
    path('api/today/', views.TodayScheduleView.as_view(), name='api_today'),
    path('api/weekly/', views.WeeklyScheduleView.as_view(), name='api_weekly'),
    path('admin/', views.AdminView.as_view(), name='admin'),
    path('upload/', views.UploadCSVView.as_view(), name='upload_csv'),
    path('delete/<int:file_id>/', views.DeleteFileView.as_view(), name='delete_file'),
    path('toggle/<int:file_id>/', views.ToggleFileView.as_view(), name='toggle_file'),
]
