from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.transport.requests import AuthorizedSession
import pytz
import os
from .models import BusinessHours, Service, Booking
from django.utils import timezone

class DjangoCalendarService:
    def __init__(self, business):
        self.business = business
        self.timezone = pytz.timezone('America/New_York')  # Consider making this dynamic based on business timezone
        
        # Google Calendar setup
        SCOPES = [
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        try:
            # Load Google credentials
            if 'GOOGLE_CREDENTIALS' in os.environ:
                temp_creds_path = '/tmp/google-credentials.json'
                with open(temp_creds_path, 'w') as f:
                    f.write(os.environ['GOOGLE_CREDENTIALS'])
                
                credentials = service_account.Credentials.from_service_account_file(
                    temp_creds_path, scopes=SCOPES)
                os.remove(temp_creds_path)
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    'silentwash-4b7a2b2c111e.json', scopes=SCOPES)
            
            # Create an authorized session
            self.session = AuthorizedSession(credentials)
            
            # Build the service with custom session
            self.service = build(
                'calendar', 
                'v3', 
                credentials=credentials,
                cache_discovery=False  # Disable file cache
            )
            
            # Get calendar ID from business model
            self.calendar_id = business.calendar_id
            if not self.calendar_id:
                print("Notice: No calendar ID set for business. Google Calendar integration disabled.")
            
        except Exception as e:
            print(f"Error initializing calendar service: {str(e)}")
            raise

        # Dictionary to track pending bookings
        self.pending_bookings = {}

    def get_business_hours(self, date):
        """Get business hours for a specific date"""
        day_of_week = date.weekday()
        try:
            return BusinessHours.objects.get(
                business=self.business,
                day_of_week=day_of_week,
                is_closed=False
            )
        except BusinessHours.DoesNotExist:
            return None

    def get_available_slots(self, date_str, service_id, destination_address=None):
        """Get available time slots for a given date and service"""
        try:
            # Parse date and get service
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            service = Service.objects.get(id=service_id, business=self.business)
            
            # Get business hours for the day
            hours = self.get_business_hours(date)
            if not hours:
                return []
            
            # Generate time slots
            slots = []
            current_time = timezone.make_aware(
                datetime.combine(date, hours.start_time),
                timezone=self.timezone
            )
            end_time = timezone.make_aware(
                datetime.combine(date, hours.end_time),
                timezone=self.timezone
            )
            
            # If it's today, start from current time
            now = timezone.now().astimezone(self.timezone)
            if date == now.date():
                rounded_now = self._round_up_to_next_slot(now)
                current_time = max(current_time, rounded_now)
                print(f"Today's date - adjusted start time to: {current_time}")
                
                # If we're past business hours, return empty list
                if current_time >= end_time:
                    print("Current time is past business hours")
                    return []

            while current_time + timedelta(minutes=service.duration) <= end_time:
                slot_end = current_time + timedelta(minutes=service.duration)
                
                # Debug print
                print(f"Checking slot: {current_time.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}")
                
                if self._is_slot_available(current_time, service.duration):
                    slots.append(current_time.strftime('%I:%M %p').lstrip('0'))
                current_time += timedelta(minutes=30)  # 30-minute intervals

            return slots

        except Exception as e:
            print(f"Error getting available slots: {str(e)}")
            raise

    def _is_slot_available(self, start_time, duration):
        """Check if a time slot is available"""
        end_time = start_time + timedelta(minutes=duration)
        
        # Debug print
        print(f"\nChecking availability for: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}")
        
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            business=self.business,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['pending', 'confirmed']
        ).exists()
        
        if overlapping_bookings:
            print("❌ Found overlapping booking in database")
            return False
        
        # Check for overlapping Google Calendar events
        calendar_events = self._get_calendar_events(start_time, end_time)
        if calendar_events:
            print(f"❌ Found {len(calendar_events)} overlapping calendar events")
            return False
        
        # Check pending bookings
        slot_key = start_time.strftime('%Y-%m-%d %H:%M')
        is_pending = slot_key in self.pending_bookings
        if is_pending:
            print("❌ Slot is currently held")
            return False
        
        print("✓ Slot is available")
        return True

    def _round_up_to_next_slot(self, dt):
        """Round up to the next available slot time"""
        minutes = dt.minute
        if minutes % 30:
            minutes = ((minutes + 29) // 30) * 30
        
        # Create new datetime with rounded minutes
        rounded = dt.replace(minute=minutes, second=0, microsecond=0)
        
        # If we rounded down, add 30 minutes
        if rounded <= dt:
            rounded = rounded + timedelta(minutes=30)
        
        return rounded

    def _get_calendar_events(self, start_time, end_time):
        """Get Google Calendar events for a time period"""
        try:
            # If no calendar ID is set, return empty list
            if not self.calendar_id:
                return []
                
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Debug print
            if events:
                print("\nFound calendar events:")
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    print(f"- {event.get('summary', 'No title')}: {start} - {end}")
            
            return events
            
        except Exception as e:
            print(f"Error fetching calendar events: {str(e)}")
            return []

    def hold_slot(self, date_str, time_str, service_id):
        """Place a temporary hold on a time slot"""
        try:
            # Clean expired holds
            self._clean_expired_holds()
            
            # Create datetime for the slot
            dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %I:%M %p')
            slot_key = dt.strftime('%Y-%m-%d %H:%M')
            
            if slot_key in self.pending_bookings:
                return {
                    'status': 'error',
                    'message': 'This slot is currently being booked by another customer'
                }
            
            service = Service.objects.get(id=service_id)
            self.pending_bookings[slot_key] = {
                'expires': timezone.now() + timedelta(minutes=5),
                'duration': timedelta(minutes=service.duration)
            }
            
            return {
                'status': 'success',
                'message': 'Slot held for 5 minutes',
                'expires_in': '5 minutes'
            }
            
        except Exception as e:
            print(f"Error holding slot: {str(e)}")
            raise

    def _clean_expired_holds(self):
        """Remove expired holds"""
        now = timezone.now()
        expired = [
            slot for slot, data in self.pending_bookings.items()
            if data['expires'] < now
        ]
        for slot in expired:
            del self.pending_bookings[slot]

    def _filter_slots_with_travel_time(self, slots, destination_address):
        """Filter slots based on travel time to/from location"""
        # Import travel calculator only if needed
        from directions import TravelTimeCalculator
        travel_calculator = TravelTimeCalculator()
        
        # For now, just return the slots unchanged
        # You can implement the travel time filtering logic here later
        return slots 