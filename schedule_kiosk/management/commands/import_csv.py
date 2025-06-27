from django.core.management.base import BaseCommand
from django.core.files import File
from schedule_kiosk.models import ScheduleFile
from schedule_kiosk.utils import import_csv_schedule
import os

class Command(BaseCommand):
    help = 'Import a CSV schedule file'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to the CSV file')
        parser.add_argument('--name', type=str, help='Name for the schedule file')
        parser.add_argument('--type', choices=['lecture', 'lab'], default='lecture', help='Type of schedule file')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        name = options['name'] or os.path.basename(csv_path)
        file_type = options['type']

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        with open(csv_path, 'rb') as f:
            schedule_file = ScheduleFile.objects.create(
                name=name,
                csv_file=File(f, name=os.path.basename(csv_path)),
                file_type=file_type
            )

        import_csv_schedule(schedule_file)
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {name}'))
