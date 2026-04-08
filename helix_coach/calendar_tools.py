import datetime
import google.auth
from googleapiclient.discovery import build


def get_calendar_service():
    """Authenticates using the Cloud Run default service account.
    This is the FALLBACK for when no per-user OAuth token is available.
    In Phase 2, this will be replaced by per-user credentials.
    """
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return build('calendar', 'v3', credentials=credentials)


# --- ADK TOOLS ---

def check_todays_schedule(user_id: str, calendar_id: str = 'primary') -> str:
    """Checks the user's Google Calendar for today to find busy times.
    
    Args:
        user_id: The authenticated user's Firebase UID.
        calendar_id: The calendar ID to check. Defaults to 'primary'.
    """
    try:
        service = get_calendar_service()
        
        now = datetime.datetime.now(datetime.timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id, timeMin=start_of_day, timeMax=end_of_day,
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


def book_workout_session(user_id: str, start_time_iso: str, end_time_iso: str, workout_title: str, timezone: str = 'Asia/Kolkata', calendar_id: str = 'primary') -> str:
    """Books a workout session in the user's Google Calendar. Times must be in ISO format.
    
    Args:
        user_id: The authenticated user's Firebase UID.
        start_time_iso: Start time in ISO 8601 format.
        end_time_iso: End time in ISO 8601 format.
        workout_title: Title description of the workout session.
        timezone: The user's timezone. Defaults to 'Asia/Kolkata'.
        calendar_id: The calendar ID to book into. Defaults to 'primary'.
    """
    try:
        service = get_calendar_service()
        
        event = {
          'summary': f'🏋️ HeliX: {workout_title}',
          'description': 'AI Scheduled Workout Session via HeliX Coach.',
          'start': {
            'dateTime': start_time_iso,
            'timeZone': timezone,
          },
          'end': {
            'dateTime': end_time_iso,
            'timeZone': timezone,  # FIXED: was previously mismatched (UTC vs Asia/Kolkata)
          },
        }

        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Successfully booked '{workout_title}' in Google Calendar! Event Link: {event.get('htmlLink')}"
    except Exception as e:
        return f"Failed to book calendar: {str(e)}"
