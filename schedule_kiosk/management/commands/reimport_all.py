# Create this file: schedule_kiosk/management/commands/reimport_all.py

from django.core.management.base import BaseCommand
from schedule_kiosk.models import ScheduleFile
from schedule_kiosk.utils import import_csv_schedule

class Command(BaseCommand):
    help = 'Re-import all CSV schedule files to handle BOM issues'

    def handle(self, *args, **options):
        files = ScheduleFile.objects.all()
        
        if not files.exists():
            self.stdout.write(self.style.WARNING("No schedule files found to re-import"))
            return
        
        self.stdout.write(f"Found {files.count()} files to re-import:")
        
        for file in files:
            self.stdout.write(f"\nRe-importing: {file.name}")
            try:
                import_csv_schedule(file)
                sessions_count = file.coursesession_set.count()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Successfully imported {sessions_count} sessions")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error importing {file.name}: {str(e)}")
                )
        
        self.stdout.write(f"\nRe-import completed!")
        
        # Show summary
        total_sessions = 0
        for file in files:
            sessions_count = file.coursesession_set.count()
            total_sessions += sessions_count
            self.stdout.write(f"  {file.name}: {sessions_count} sessions")
        
        self.stdout.write(f"\nTotal sessions in database: {total_sessions}")
