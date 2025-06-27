from django.core.management.base import BaseCommand
from django.db import models
from schedule_kiosk.models import ScheduleFile, CourseSession
from schedule_kiosk.utils import get_current_day_letter, get_sessions_for_day

class Command(BaseCommand):
    help = 'Debug schedule data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== SCHEDULE DEBUG INFO ==="))
        
        # Check files
        files = ScheduleFile.objects.all()
        self.stdout.write(f"Total schedule files: {files.count()}")
        for file in files:
            sessions_count = CourseSession.objects.filter(schedule_file=file).count()
            self.stdout.write(f"  - {file.name} ({file.file_type}) - Active: {file.is_active} - Sessions: {sessions_count}")
        
        # Check sessions
        sessions = CourseSession.objects.all()
        self.stdout.write(f"\nTotal course sessions: {sessions.count()}")
        
        active_sessions = CourseSession.objects.filter(schedule_file__is_active=True)
        self.stdout.write(f"Active course sessions: {active_sessions.count()}")
        
        # Check days
        all_days = set(session.days for session in active_sessions)
        self.stdout.write(f"Days found in active sessions: {sorted(all_days)}")
        
        # Check each day individually
        for day in ['M', 'T', 'W', 'R', 'F']:
            day_sessions = get_sessions_for_day(day)
            self.stdout.write(f"Sessions for {day}: {day_sessions.count()}")
        
        # Check current day
        current_day = get_current_day_letter()
        self.stdout.write(f"\nCurrent day letter: {current_day}")
        
        today_sessions = get_sessions_for_day(current_day)
        self.stdout.write(f"Sessions for today ({current_day}): {today_sessions.count()}")
        
        # Show some sample sessions with detailed info
        self.stdout.write(f"\nSample sessions (first 10):")
        for i, session in enumerate(active_sessions[:10]):
            self.stdout.write(f"  {i+1}. {session.full_course_code}: Days='{session.days}' Time={session.start_time}-{session.end_time} Location={session.location}")
        
        # Check time ranges
        if active_sessions.exists():
            earliest = active_sessions.aggregate(models.Min('start_time'))['start_time__min']
            latest = active_sessions.aggregate(models.Max('end_time'))['end_time__max']
            self.stdout.write(f"\nTime range in database: {earliest} to {latest}")
        
        # Test the day filtering logic specifically
        self.stdout.write(f"\n=== TESTING DAY FILTERING ===")
        for day in ['M', 'T', 'W', 'R', 'F']:
            # Test the exact query used in get_sessions_for_day
            test_sessions = CourseSession.objects.filter(
                schedule_file__is_active=True,
                days__contains=day
            )
            self.stdout.write(f"Day '{day}': {test_sessions.count()} sessions")
            
            # Show a few examples
            for session in test_sessions[:3]:
                self.stdout.write(f"    - {session.full_course_code} (days='{session.days}')")
        
        # Check if there are any issues with the days field
        self.stdout.write(f"\n=== DAYS FIELD ANALYSIS ===")
        unique_days = CourseSession.objects.filter(schedule_file__is_active=True).values_list('days', flat=True).distinct()
        for days_value in unique_days:
            count = CourseSession.objects.filter(schedule_file__is_active=True, days=days_value).count()
            self.stdout.write(f"Days value '{days_value}': {count} sessions")