from django.contrib import admin
from .models import ScheduleFile, CourseSession

@admin.register(ScheduleFile)
class ScheduleFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'is_active', 'uploaded_at']
    list_filter = ['file_type', 'is_active', 'uploaded_at']
    search_fields = ['name']

@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ['full_course_code', 'title', 'days', 'start_time', 'end_time', 'instructor', 'location']
    list_filter = ['days', 'schedule_file__file_type', 'subject']
    search_fields = ['subject', 'course_number', 'title', 'instructor']
    ordering = ['days', 'start_time']
