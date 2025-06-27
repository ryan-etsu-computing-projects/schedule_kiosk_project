# Updated views.py with debugging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import models
from datetime import datetime, time
from .models import ScheduleFile, CourseSession
from .utils import import_csv_schedule, get_time_slots, get_sessions_for_day, get_current_day_letter
import logging

# Set up logging for debugging
logger = logging.getLogger(__name__)

class KioskView(View):
    """Main kiosk display view with auto-rotating slides"""
    def get(self, request):
        # Debug: Check if we have any data in the database
        total_sessions = CourseSession.objects.count()
        active_files = ScheduleFile.objects.filter(is_active=True).count()
        
        logger.info(f"Kiosk view: {total_sessions} total sessions, {active_files} active files")
        
        context = {
            'current_time': datetime.now(),
            'current_day': get_current_day_letter(),
            'debug_info': {
                'total_sessions': total_sessions,
                'active_files': active_files,
            }
        }
        return render(request, 'schedule_kiosk/kiosk.html', context)

class TodayScheduleView(View):
    """API endpoint for today's schedule data"""
    def get(self, request):
        try:
            current_day = get_current_day_letter()
            logger.info(f"Today API called for day: {current_day}")
            
            # Debug: Get all sessions and filter manually to see what's happening
            all_sessions = CourseSession.objects.filter(schedule_file__is_active=True)
            logger.info(f"Total active sessions: {all_sessions.count()}")
            
            # Debug: Check what days we have
            all_days = set(session.days for session in all_sessions)
            logger.info(f"Available days in data: {all_days}")
            
            sessions = get_sessions_for_day(current_day)
            logger.info(f"Sessions for {current_day}: {sessions.count()}")
            
            # Debug: Print some session details
            for session in sessions[:3]:  # First 3 sessions
                logger.info(f"Session: {session.subject} {session.course_number} - {session.days} - {session.start_time}")
            
            time_slots = get_time_slots()
            logger.info(f"Time slots generated: {len(time_slots)}")
            
            # Build schedule data
            schedule_data = []
            sessions_found = 0
            
            for slot in time_slots:
                slot_sessions = []
                for session in sessions:
                    if session.start_time <= slot < session.end_time:
                        sessions_found += 1
                        slot_sessions.append({
                            'course_code': session.full_course_code,
                            'title': session.title,
                            'instructor': session.instructor,
                            'location': session.location,
                            'time_range': session.time_range,
                            'start_time': session.start_time.strftime('%H:%M'),
                            'end_time': session.end_time.strftime('%H:%M'),
                        })
                
                schedule_data.append({
                    'time': slot.strftime('%-I:%M %p'),
                    'time_24': slot.strftime('%H:%M'),
                    'sessions': slot_sessions
                })
            
            logger.info(f"Sessions found in time slots: {sessions_found}")
            
            response_data = {
                'day': current_day,
                'day_name': {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'R': 'Thursday', 'F': 'Friday'}.get(current_day, 'Today'),
                'schedule': schedule_data,
                'current_time': datetime.now().strftime('%H:%M'),
                'debug': {
                    'total_sessions': sessions.count(),
                    'sessions_in_slots': sessions_found,
                    'time_slots_count': len(time_slots)
                }
            }
            
            logger.info(f"Returning response with {len(schedule_data)} time slots")
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Error in TodayScheduleView: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': str(e),
                'day': 'Error',
                'day_name': 'Error',
                'schedule': [],
                'current_time': datetime.now().strftime('%H:%M')
            })

class WeeklyScheduleView(View):
    """API endpoint for weekly schedule data"""
    def get(self, request):
        try:
            schedule_type = request.GET.get('type', 'mw')
            logger.info(f"Weekly API called for type: {schedule_type}")
            
            if schedule_type == 'mw':
                days = ['M', 'T', 'W']
                day_names = ['Monday', 'Tuesday', 'Wednesday']
            else:
                days = ['R', 'F']
                day_names = ['Thursday', 'Friday']
            
            time_slots = get_time_slots()
            schedule_data = []
            total_sessions_found = 0
            
            for slot in time_slots:
                slot_data = {
                    'time': slot.strftime('%-I:%M %p'),
                    'time_24': slot.strftime('%H:%M'),
                    'days': {}
                }
                
                for day, day_name in zip(days, day_names):
                    sessions = get_sessions_for_day(day)
                    slot_sessions = []
                    
                    for session in sessions:
                        if session.start_time <= slot < session.end_time:
                            total_sessions_found += 1
                            slot_sessions.append({
                                'course_code': session.full_course_code,
                                'title': session.title,
                                'instructor': session.instructor,
                                'location': session.location,
                                'time_range': session.time_range,
                            })
                    
                    slot_data['days'][day] = {
                        'name': day_name,
                        'sessions': slot_sessions
                    }
                
                schedule_data.append(slot_data)
            
            logger.info(f"Weekly {schedule_type}: {total_sessions_found} sessions found")
            
            response_data = {
                'type': schedule_type,
                'days': days,
                'day_names': day_names,
                'schedule': schedule_data,
                'debug': {
                    'total_sessions_found': total_sessions_found,
                    'time_slots_count': len(time_slots)
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Error in WeeklyScheduleView: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': str(e),
                'type': schedule_type,
                'days': [],
                'day_names': [],
                'schedule': []
            })

class AdminView(View):
    """Admin interface for managing CSV files"""
    def get(self, request):
        files = ScheduleFile.objects.all()
        
        # Debug info for admin
        debug_info = {}
        for file in files:
            sessions = CourseSession.objects.filter(schedule_file=file)
            debug_info[file.id] = {
                'sessions_count': sessions.count(),
                'days': list(set(session.days for session in sessions)),
                'time_range': {
                    'earliest': sessions.aggregate(models.Min('start_time'))['start_time__min'],
                    'latest': sessions.aggregate(models.Max('end_time'))['end_time__max'],
                } if sessions.exists() else None
            }
        
        context = {
            'files': files,
            'debug_info': debug_info
        }
        return render(request, 'schedule_kiosk/admin.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class UploadCSVView(View):
    """Handle CSV file uploads"""
    def post(self, request):
        try:
            csv_file = request.FILES['csv_file']
            name = request.POST.get('name', csv_file.name)
            file_type = request.POST.get('file_type', 'lecture')
            
            logger.info(f"Uploading CSV: {name} ({file_type})")
            
            # Create schedule file record
            schedule_file = ScheduleFile.objects.create(
                name=name,
                csv_file=csv_file,
                file_type=file_type
            )
            
            # Import data from CSV
            import_csv_schedule(schedule_file)
            
            # Debug: Check how many sessions were created
            sessions_count = CourseSession.objects.filter(schedule_file=schedule_file).count()
            logger.info(f"Created {sessions_count} sessions from {name}")
            
            messages.success(request, f'Successfully uploaded and imported {name} ({sessions_count} sessions)')
            return redirect('admin')
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            messages.error(request, f'Error uploading file: {str(e)}')
            return redirect('admin')

class DeleteFileView(View):
    """Delete a schedule file"""
    def post(self, request, file_id):
        schedule_file = get_object_or_404(ScheduleFile, id=file_id)
        file_name = schedule_file.name
        schedule_file.delete()
        logger.info(f"Deleted schedule file: {file_name}")
        messages.success(request, f'Deleted {file_name}')
        return redirect('admin')

class ToggleFileView(View):
    """Toggle active status of a schedule file"""
    def post(self, request, file_id):
        schedule_file = get_object_or_404(ScheduleFile, id=file_id)
        schedule_file.is_active = not schedule_file.is_active
        schedule_file.save()
        status = 'activated' if schedule_file.is_active else 'deactivated'
        logger.info(f"Schedule file {schedule_file.name} {status}")
        messages.success(request, f'{schedule_file.name} {status}')
        return redirect('admin')
