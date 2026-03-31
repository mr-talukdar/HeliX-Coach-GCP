import datetime
import google.auth
from googleapiclient.discovery import build

# --- CONFIGURATION ---
# Replace this with the ID of the calendar you shared. 
# If you shared your primary personal calendar, use 'primary'. 
# If you created a new one, find its ID in the Calendar Settings (looks like a long email address).
CALENDAR_ID = 'd58d067ec327a5e2f88f0e0f19014b58d2aabb200d56b2ba25207b92c0152aea@group.calendar.google.com' 

def get_calendar_service():
    """Authenticates using the Cloud Shell / Cloud Run default service account."""
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return build('calendar', 'v3', credentials=credentials)

# --- ADK TOOLS ---

def check_todays_schedule() -> str:
    """Checks the user's Google Calendar for today to find busy times."""
    try:
        service = get_calendar_service()
        
        # Get the start and end of today
        now = datetime.datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=CALENDAR_ID, timeMin=start_of_day, timeMax=end_of_day,
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "The calendar is completely clear today. You can schedule a workout anytime!"
            
        schedule = "Here are the busy blocks for today:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'Busy')
            schedule += f"- {summary}: from {start} to {end}\n"
            
        return schedule
    except Exception as e:
        return f"Calendar Error: {str(e)}"

def book_workout_session(start_time_iso: str, end_time_iso: str, workout_title: str) -> str:
    """Books a workout session in the user's Google Calendar. Times must be in ISO format."""
    try:
        service = get_calendar_service()
        
        event = {
          'summary': f'🏋️ HeliX: {workout_title}',
          'description': 'AI Scheduled Workout Session via LeanX Coach.',
          'start': {
            'dateTime': start_time_iso,
            'timeZone': 'Asia/Kolkata', # Adjust to 'Asia/Kolkata' if you prefer local time
          },
          'end': {
            'dateTime': end_time_iso,
            'timeZone': 'UTC',
          },
          
        }

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"Successfully booked '{workout_title}' in Google Calendar! Event Link: {event.get('htmlLink')}"
    except Exception as e:
        return f"Failed to book calendar: {str(e)}"