import csv
import logging
from datetime import time, datetime
from django.utils import timezone
from .models import CourseSession

logger = logging.getLogger(__name__)

def get_time_slots():
    """Generate time slots for the schedule grid (8 AM to 7:30 PM)"""
    slots = []
    for hour in range(8, 20):  # 8 AM to 7 PM
        for minute in [0, 15, 30, 45]:
            time_obj = time(hour, minute)
            slots.append(time_obj)
    # Add 7:15 PM and 7:30 PM
    slots.append(time(19, 15))  # 7:15 PM
    slots.append(time(19, 30))  # 7:30 PM
    return slots

def get_current_day_letter():
    """Get the current day as a single letter (M, T, W, R, F)"""
    day_mapping = {
        0: 'M',  # Monday
        1: 'T',  # Tuesday
        2: 'W',  # Wednesday
        3: 'R',  # Thursday (R for Thursday to avoid confusion with Tuesday)
        4: 'F',  # Friday
        5: 'S',  # Saturday (if needed)
        6: 'U',  # Sunday (if needed)
    }
    
    current_day = datetime.now().weekday()
    return day_mapping.get(current_day, 'M')

def parse_time_range(time_str):
    """Parse a time range string like '9:00 AM-9:50 AM' into start and end time objects"""
    try:
        # Remove extra spaces and split by dash or hyphen
        time_str = time_str.strip()
        parts = time_str.replace('–', '-').replace('—', '-').split('-')
        
        if len(parts) != 2:
            logger.error(f"Invalid time format: {time_str}")
            return None, None
        
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        
        # Parse each time part
        start_time = parse_single_time(start_str)
        end_time = parse_single_time(end_str)
        
        return start_time, end_time
        
    except Exception as e:
        logger.error(f"Error parsing time range '{time_str}': {str(e)}")
        return None, None

def parse_single_time(time_str):
    """Parse a single time string like '9:00 AM' into a time object"""
    try:
        # Clean the time string
        time_str = time_str.strip().upper()
        
        # Handle different time formats
        if 'AM' in time_str or 'PM' in time_str:
            # 12-hour format
            time_part = time_str.replace('AM', '').replace('PM', '').strip()
            is_pm = 'PM' in time_str
            
            if ':' in time_part:
                hour_str, minute_str = time_part.split(':')
                hour = int(hour_str)
                minute = int(minute_str)
            else:
                hour = int(time_part)
                minute = 0
            
            # Convert to 24-hour format
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
                
        else:
            # 24-hour format
            if ':' in time_str:
                hour_str, minute_str = time_str.split(':')
                hour = int(hour_str)
                minute = int(minute_str)
            else:
                hour = int(time_str)
                minute = 0
        
        return time(hour, minute)
        
    except Exception as e:
        logger.error(f"Error parsing single time '{time_str}': {str(e)}")
        return None

def get_sessions_for_day(day_letter):
    """Get all active sessions for a specific day"""
    return CourseSession.objects.filter(
        schedule_file__is_active=True,
        days__contains=day_letter
    ).order_by('start_time', 'subject', 'course_number')

def get_sessions_for_time_slot(day_letter, slot_time):
    """Get sessions that are active during a specific time slot"""
    sessions = get_sessions_for_day(day_letter)
    active_sessions = []
    
    for session in sessions:
        if session.start_time <= slot_time < session.end_time:
            active_sessions.append(session)
    
    return active_sessions

def import_csv_schedule(schedule_file):
    """Import course sessions from a CSV file into the database"""
    logger.info(f"Starting import of {schedule_file.name}")
    
    # Clear existing sessions for this file
    existing_count = CourseSession.objects.filter(schedule_file=schedule_file).count()
    CourseSession.objects.filter(schedule_file=schedule_file).delete()
    logger.info(f"Deleted {existing_count} existing sessions")
    
    success_count = 0
    error_count = 0
    
    try:
        # Try UTF-8 with BOM first, then fallback to regular UTF-8
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1']
        
        for encoding in encodings_to_try:
            try:
                with open(schedule_file.csv_file.path, 'r', newline='', encoding=encoding) as csvfile:
                    logger.info(f"Successfully opened file with encoding: {encoding}")
                    break
            except UnicodeDecodeError:
                logger.warning(f"Failed to open with encoding: {encoding}")
                continue
        else:
            raise ValueError("Could not decode CSV file with any supported encoding")
        
        with open(schedule_file.csv_file.path, 'r', newline='', encoding=encoding) as csvfile:
            # Try to detect the delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            logger.info(f"Detected CSV delimiter: '{delimiter}'")
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Log the headers we found and clean them
            original_headers = reader.fieldnames
            logger.info(f"Original CSV headers: {original_headers}")
            
            # Clean the headers by stripping whitespace and BOM characters
            cleaned_headers = []
            for header in original_headers:
                # Remove BOM, whitespace, and other invisible characters
                cleaned_header = header.strip().strip('\ufeff').strip('\xef\xbb\xbf').strip()
                cleaned_headers.append(cleaned_header)
            
            logger.info(f"Cleaned CSV headers: {cleaned_headers}")
            
            # Create a mapping from original to cleaned headers
            header_mapping = dict(zip(original_headers, cleaned_headers))
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Clean the row data using the header mapping
                    cleaned_row = {}
                    for orig_key, value in row.items():
                        clean_key = header_mapping.get(orig_key, orig_key)
                        cleaned_row[clean_key] = value
                    
                    logger.debug(f"Processing row {row_num}: {cleaned_row}")
                    
                    # Parse time range
                    time_str = cleaned_row.get('Time', '').strip()
                    if not time_str:
                        logger.warning(f"Row {row_num}: Empty time field")
                        error_count += 1
                        continue
                    
                    start_time, end_time = parse_time_range(time_str)
                    
                    if start_time and end_time:
                        session = CourseSession.objects.create(
                            schedule_file=schedule_file,
                            subject=str(cleaned_row.get('Subj', '')).strip(),
                            course_number=str(cleaned_row.get('Crse', '')).strip(),
                            section=str(cleaned_row.get('Sec', '')).strip(),
                            title=str(cleaned_row.get('Title', '')).strip(),
                            days=str(cleaned_row.get('Days', '')).strip(),
                            start_time=start_time,
                            end_time=end_time,
                            instructor=str(cleaned_row.get('Instructor', '')).strip(),
                            location=str(cleaned_row.get('Location', '')).strip(),
                            date_range=str(cleaned_row.get('Date (MM/DD)', '')).strip()  # Only in lab files
                        )
                        success_count += 1
                        logger.debug(f"Created session: {session}")
                    else:
                        logger.error(f"Row {row_num}: Could not parse time '{time_str}'")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Row {row_num}: Error processing row: {str(e)}")
                    logger.error(f"Row data: {cleaned_row}")
                    error_count += 1
    
    except Exception as e:
        logger.error(f"Error importing CSV file: {str(e)}")
        raise
    
    logger.info(f"Import completed: {success_count} sessions created, {error_count} errors")
    return success_count, error_count
