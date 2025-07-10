# University Schedule Kiosk Display

A Flask-based web application that displays university course schedules, lab sessions, and announcements in a 16:9 kiosk format. Perfect for displaying in hallways, computer labs, or department offices.

<p align="center">
    <img src="img/kiosk-display-widescreen.png" alt="Kiosk display screenshot">
</p>

## Features

- **Dynamic Schedule Display**: Shows lecture and lab schedules organized by day of the week
- **Smart Pagination**: Automatically creates slides to handle busy days with many events
- **Time-based Announcements**: Displays relevant announcements based on current date
- **Responsive Design**: Clean, readable interface suitable for kiosk displays
- **Multiple View Modes**: Both paginated and simple view options

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project files** to your desired directory:
   ```bash
   cd /path/to/your/project
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install required dependencies**:
   ```bash
   pip install flask flask-cors
   ```

5. **Create the data directory and CSV files** (see Data Setup section below)

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the kiosk display**:
   - Main display (paginated): http://localhost:5000
   - Simple display: http://localhost:5000/simple

## Project Structure

```
your-project/
├── app.py                     # Main Flask application
├── data/                      # Data directory
│   ├── lecture_schedule.csv   # Lecture schedule data
│   ├── lab_schedule.csv       # Lab schedule data
│   └── announcements.csv      # Announcements data
├── static/                    # Static files
│   └── styles.css             # Global style rules
├── templates/                 # HTML templates (not included in provided code)
│   ├── schedule.html          # Main paginated schedule template
└── .venv/                     # Virtual environment (created during setup)
```

## Data Setup

Create a `data/` directory in your project root and add the following CSV files:

### 1. announcements.csv

Controls what announcements are displayed based on date ranges.

**Format:**
```csv
StartDate,EndDate,Title,Announcement
08/25,08/31,Week 1: Module Name,"This week we will introduce the course and begin our first module..."
09/01,09/07,Week 2: Module Name,"This week we continue with..."
```

**Fields:**
- `StartDate`: Start date in MM/DD format
- `EndDate`: End date in MM/DD format  
- `Title`: Announcement title
- `Announcement`: Full announcement text (use quotes if contains commas)

### 2. lecture_schedule.csv

Contains regular lecture schedules.

**Format:**
```csv
Subj,Crse,Sec,Title,Days,Time,Instructor,Location
CSCI,1100,1,Using Info Tech Lecture,M,08:15 am-10:15 am,"Chelsie Dubay, Ryan Haas",Rogers Stout Hall 118
CSCI,1100,2,Using Info Tech Lecture,TWR,10:30 am-11:50 am,"John Smith",Rogers Stout Hall 102
```

**Fields:**
- `Subj`: Subject code (e.g., CSCI)
- `Crse`: Course number (e.g., 1100)
- `Sec`: Section number
- `Title`: Course title
- `Days`: Days of week (M=Monday, T=Tuesday, W=Wednesday, R=Thursday, F=Friday, S=Saturday, Su=Sunday)
- `Time`: Time range in 12-hour format
- `Instructor`: Instructor name(s)
- `Location`: Classroom location

### 3. lab_schedule.csv

Contains lab schedules with date ranges.

**Format:**
```csv
Subj,Crse,Sec,Title,Days,Time,Instructor,Date (MM/DD),Location
CSCI,1150,001,Using Information Tech Lab,M,08:55 am-10:15 am,"Chelsie Dubay, Ryan Haas",08/25-12/11,Sam Wilson Hall 320
```

**Fields:**
- Same as lecture_schedule.csv, plus:
- `Date (MM/DD)`: Date range when lab is active (MM/DD-MM/DD format)

## Usage

### Running the Application

1. **Activate your virtual environment** (if not already activated):
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Start the Flask application**:
   ```bash
   python app.py
   ```

3. **Access the application**:
   - Main kiosk display: http://localhost:5000
   - Simple view: http://localhost:5000/simple

### Display Features

- **Automatic Pagination**: Days with many events are automatically split across slides
- **Time-based Announcements**: Only shows announcements that are currently active
- **Smart Grouping**: Events are grouped by day and sorted by start time
- **Special Handling**: "Using Info Tech" courses are automatically renamed to CSCI 1100/1150

### Deployment Options

#### For Production Deployment

1. **Use a production WSGI server** like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. **Set up a reverse proxy** (nginx recommended) to serve the application

3. **Consider using systemd** or similar to manage the service

#### For Kiosk Display

1. **Set up auto-refresh** in your browser to reload the page periodically
2. **Use fullscreen mode** for best kiosk experience
3. **Consider using a dedicated kiosk browser** or kiosk mode in Chrome/Firefox

## Customization

### Modifying Display Layout

- Adjust `max_events_per_day` in the `paginate_schedule()` function call (currently set to 5)
- Modify the `DAYS_MAP` dictionary to change day abbreviations
- Update the `_standardize_uit_name()` function to handle other course naming conventions

### Adding New Data Sources

The application can be extended to read from databases or other data sources by modifying the parsing functions:
- `parse_lecture_csv()`
- `parse_lab_csv()`
- `parse_announcements_file_csv()`

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure your virtual environment is activated and dependencies are installed
2. **File not found errors**: Ensure the `data/` directory exists and contains the required CSV files
3. **Date parsing issues**: Check that date formats in CSV files match the expected MM/DD format
4. **Display issues**: Verify that your HTML templates are properly configured

### Debug Mode

The application runs in debug mode by default, which provides helpful error messages. For production, change:
```python
app.run(debug=False)
```

## Contributing

When adding new features or modifying the application:

1. Test with sample data to ensure CSV parsing works correctly
2. Verify that pagination handles edge cases (very busy days, empty days)
3. Check that announcements display correctly across date boundaries
4. Ensure the kiosk display remains readable and professional

## License

This project is designed for educational use in university computing departments.