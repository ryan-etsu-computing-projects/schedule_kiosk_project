from django.db import models
from django.core.validators import FileExtensionValidator
import csv
import os
from datetime import datetime, time

class ScheduleFile(models.Model):
    """Model to store uploaded CSV schedule files"""
    name = models.CharField(max_length=255)
    csv_file = models.FileField(
        upload_to='csv_files/',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('lecture', 'Lecture'),
            ('lab', 'Lab'),
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.file_type})"

    class Meta:
        ordering = ['-uploaded_at']

class CourseSession(models.Model):
    """Model to represent individual course sessions parsed from CSV"""
    schedule_file = models.ForeignKey(ScheduleFile, on_delete=models.CASCADE)
    subject = models.CharField(max_length=10)
    course_number = models.CharField(max_length=10)
    section = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    days = models.CharField(max_length=10)  # M, T, W, R, F format
    start_time = models.TimeField()
    end_time = models.TimeField()
    instructor = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    date_range = models.CharField(max_length=50, blank=True, null=True)  # For lab files

    def __str__(self):
        return f"{self.subject} {self.course_number}-{self.section} ({self.days} {self.start_time}-{self.end_time})"

    @property
    def full_course_code(self):
        return f"{self.subject} {self.course_number}-{self.section}"

    @property
    def time_range(self):
        return f"{self.start_time.strftime('%-I:%M %p')}-{self.end_time.strftime('%-I:%M %p')}"

    def get_day_names(self):
        """Convert single letter days to full names"""
        day_map = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'R': 'Thursday', 'F': 'Friday'}
        return [day_map.get(day, day) for day in self.days]

    class Meta:
        ordering = ['days', 'start_time']
