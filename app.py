import csv
from datetime import datetime
from collections import defaultdict
from flask import Flask, render_template
from flask_cors import CORS
from datetime import datetime, date

app = Flask(__name__)
CORS(app, origins=["http://0.0.0.0:5000", "http://127.0.0.1:5000", "http://localhost:5000", "https://random-d.uk"])

# Map each day character to the full day name
DAYS_MAP = {
    'M': 'Monday',
    'T': 'Tuesday',
    'W': 'Wednesday',
    'R': 'Thursday',
    'F': 'Friday',
    'S': 'Saturday',
    'Su': 'Sunday'
}

def _get_current_announcement(announcements):
    """
    Find the announcement that should be displayed for today's date.
    
    Args:
        announcements: List of announcement dictionaries with 'start_date', 'end_date', 
                      'title', and 'announcement' keys
    
    Returns:
        Dictionary of the current announcement, or None if no announcement is active
    """
    today = date.today()
    current_year = today.year
    
    for announcement in announcements:
        # Parse the MM/DD format dates and assume current year
        start_month, start_day = map(int, announcement['start_date'].split('/'))
        end_month, end_day = map(int, announcement['end_date'].split('/'))
        
        start_date = date(current_year, start_month, start_day)
        end_date = date(current_year, end_month, end_day)
        
        # Handle year boundary crossing (e.g., 12/15 to 01/15)
        if end_date < start_date:
            # If today is after start_date in current year, or before end_date in current year
            if today >= start_date or today <= end_date:
                print(announcement['title'])
                return announcement
        else:
            # Normal case: start and end in same year
            if start_date <= today <= end_date:
                return announcement
    
    return None

def _standardize_uit_name(event):
    if event['title'].lower().startswith('using info'):
        event['title'] = 'CSCI-1150'
        if event['type'] == 'Lecture': event['title'] = 'CSCI-1100'
    return event

# Helper functions to parse the CSV files
def parse_lecture_csv(file_path):
    lectures = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event = {
                    'subj': row['Subj'],
                    'crse': row['Crse'],
                    'sec': row['Sec'],
                    'title': row['Title'],
                    'days': row['Days'],
                    'time': row['Time'],
                    'instructor': row['Instructor'],
                    'location': row['Location'],
                    'type': 'Lecture'
                }
                event['start_time'] = convert_time_to_24hr(event['time'].split('-')[0])
                event = _standardize_uit_name(event)
                lectures.append(event)
    except Exception as e:
        print(f"Error parsing lecture file: {e}")
    return lectures

def parse_lab_csv(file_path):
    labs = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event = {
                    'subj': row['Subj'],
                    'crse': row['Crse'],
                    'sec': row['Sec'],
                    'title': row['Title'],
                    'days': row['Days'],
                    'time': row['Time'],
                    'instructor': row['Instructor'],
                    'location': row['Location'],
                    'date_range': row['Date (MM/DD)'],
                    'type': 'Lab'
                }
                event['start_time'] = convert_time_to_24hr(event['time'].split('-')[0])
                event = _standardize_uit_name(event)
                labs.append(event)
    except Exception as e:
        print(f"Error parsing lab file: {e}")
    return labs

def parse_announcements_file_csv(file_path):
    announcements = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                announcement = {
                    'start_date': row['StartDate'],
                    'end_date': row['EndDate'],
                    'title': row['Title'],
                    'announcement': row['Announcement']
                }
                announcements.append(announcement)
    except Exception as e:
        print(f"Error parsing lab file: {e}")
    return announcements

def convert_time_to_24hr(time_str):
    try:
        return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        print(f"Invalid time format: {time_str}")
        return "00:00"

def paginate_schedule(schedule_by_day, ordered_days, max_events_per_day=6):
    """
    Paginate schedule into slides based on max events per day
    Returns list of slide configurations
    """
    slides = []
    
    # Filter to only days that have events
    days_with_events = [day for day in ordered_days if day in schedule_by_day and schedule_by_day[day]]
    
    i = 0
    while i < len(days_with_events):
        day = days_with_events[i]
        day_events = len(schedule_by_day[day])
        
        # If this day has more than max_events_per_day, give it its own slide with 2-column layout
        if day_events > max_events_per_day:
            slide = {
                'type': 'screen-2-col',  # Will be handled specially in template
                'days': [day],
                'events': {day: schedule_by_day[day]},
                'max_events': day_events,
                'split_day': True  # Flag to indicate this day should be split
            }
            slides.append(slide)
            i += 1
        else:
            # Try to group days that fit within the limit
            current_group = []
            current_group_max_events = 0
            
            # Try to fit up to 3 days in a slide, respecting the max events limit
            while len(current_group) < 3 and i < len(days_with_events):
                day = days_with_events[i]
                day_events = len(schedule_by_day[day])
                
                # Check if this day can fit in the current slide
                potential_max = max(current_group_max_events, day_events)
                
                # If this is the first day in the group, or it fits within limits
                if len(current_group) == 0 or potential_max <= max_events_per_day:
                    current_group.append(day)
                    current_group_max_events = potential_max
                    i += 1
                else:
                    # This day won't fit, break to start new slide
                    break
            
            # Create slide for the current group
            if current_group:
                # Determine slide layout based on number of days
                if len(current_group) <= 2:
                    slide_type = "screen-2-col"
                else:
                    slide_type = "screen-3-col"
                
                slide = {
                    'type': slide_type,
                    'days': current_group,
                    'events': {day: schedule_by_day[day] for day in current_group},
                    'max_events': current_group_max_events,
                    'split_day': False
                }
                slides.append(slide)
    
    return slides

@app.route('/')
def display_schedule():
    # Paths to CSV files
    lecture_file = 'data/lecture_schedule.csv'
    lab_file = 'data/lab_schedule.csv'
    announcements_file = 'data/announcements.csv'

    # Parse the lecture and lab files
    lectures = parse_lecture_csv(lecture_file)
    labs = parse_lab_csv(lab_file)
    announcements = parse_announcements_file_csv(announcements_file)
    current_announcement = _get_current_announcement(announcements)

    # Combine lectures and labs into a single list of events
    all_events = lectures + labs

    # Group events by day of the week
    schedule_by_day = defaultdict(list)
    for event in all_events:
        for day_char in event["days"]:
            day_name = DAYS_MAP.get(day_char, "Unknown")
            schedule_by_day[day_name].append(event)

    # Sort each day's events by start time
    for day in schedule_by_day:
        schedule_by_day[day].sort(key=lambda x: x["start_time"])

    # Sort days in logical order
    ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Paginate the schedule into slides
    slides = paginate_schedule(schedule_by_day, ordered_days, max_events_per_day=5)
    
    # Debug output to see slide structure
    print(f"Generated {len(slides)} slides:")
    for i, slide in enumerate(slides):
        print(f"  Slide {i+1}: {slide['type']} with days {slide['days']} (max events: {slide['max_events']})")

    return render_template("schedule.html", slides=slides, schedule=schedule_by_day, days=ordered_days, current_announcement=current_announcement)

# Alternative route for testing without pagination
@app.route('/simple')
def display_simple_schedule():
    # Paths to CSV files
    lecture_file = 'data/lecture_schedule.csv'
    lab_file = 'data/lab_schedule.csv'

    # Parse the lecture and lab files
    lectures = parse_lecture_csv(lecture_file)
    labs = parse_lab_csv(lab_file)

    # Combine lectures and labs into a single list of events
    all_events = lectures + labs

    # Group events by day of the week
    schedule_by_day = defaultdict(list)
    for event in all_events:
        for day_char in event["days"]:
            day_name = DAYS_MAP.get(day_char, "Unknown")
            schedule_by_day[day_name].append(event)

    # Sort each day's events by start time
    for day in schedule_by_day:
        schedule_by_day[day].sort(key=lambda x: x["start_time"])

    # Sort days in logical order
    ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return render_template("schedule_simple.html", schedule=schedule_by_day, days=ordered_days)

if __name__ == '__main__':
    app.run(debug=True)