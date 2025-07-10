import csv
from datetime import datetime

# Parse time into datetime.time object for sorting
def parse_time_range(time_str):
    start, _ = time_str.split('-')
    return datetime.strptime(start.strip(), "%I:%M %p").time()

def parse_lecture_csv(file_path):
    lectures = []
    with open(file_path, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            lectures.append({
                "type": "Lecture",
                "title": row["Title"],
                "days": row["Days"],
                "time": row["Time"],
                "start_time": parse_time_range(row["Time"]),
                "instructors": [row["Instructor"]],
                "location": row["Location"]
            })
    return lectures

def parse_lab_csv(file_path):
    labs = []
    with open(file_path, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            labs.append({
                "type": "Lab",
                "title": row["Title"],
                "days": row["Days"],
                "time": row["Time"],
                "start_time": parse_time_range(row["Time"]),
                "instructors": [i.strip() for i in row["Instructor"].split(",")],
                "date_range": row["Date (MM/DD)"],
                "location": row["Location"]
            })
    return labs
