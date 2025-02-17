import googlemaps
import os
from datetime import datetime, timedelta
from functools import lru_cache

class TravelTimeCalculator:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])
    
    @lru_cache(maxsize=128)
    def get_travel_times(self, origins, destinations, departure_time):
        """Batch query travel times using Distance Matrix API"""
        try:
            # Convert tuples/strings to lists for the API call
            if isinstance(origins, (str, tuple)):
                origins = [origins] if isinstance(origins, str) else list(origins)
            if isinstance(destinations, (str, tuple)):
                destinations = [destinations] if backend.pyisinstance(destinations, str) else list(destinations)
            
            # For future dates, we need to use the time of day but set to today
            now = datetime.now()
            departure_hour = departure_time.hour
            departure_minute = departure_time.minute
            
            # Set departure time to today at the same time
            adjusted_departure = now.replace(
                hour=departure_hour,
                minute=departure_minute,
                second=0,
                microsecond=0
            )
            
            # If the time has already passed today, set to tomorrow
            if adjusted_departure < now:
                adjusted_departure += timedelta(days=1)
            
            print(f"Calculating travel time using departure: {adjusted_departure.strftime('%Y-%m-%d %H:%M')}")
            
            result = self.gmaps.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode="driving",
                departure_time=adjusted_departure
            )
            
            # Extract durations into a more usable format
            travel_times = {}
            for i, origin in enumerate(origins):
                travel_times[str(origin)] = {}
                for j, dest in enumerate(destinations):
                    element = result['rows'][i]['elements'][j]
                    travel_times[str(origin)][str(dest)] = {
                        'text': element['duration']['text'],
                        'minutes': element['duration']['value'] // 60  # Convert seconds to minutes
                    }
            
            return travel_times
        except Exception as e:
            print(f"✗ Error calculating travel times: {str(e)}")
            return None

    def get_place_suggestions(self, input_text, location=(39.0458, -76.6413), radius=50000):
        """Get place suggestions using Google Places Autocomplete API
        
        Args:
            input_text (str): The text to search for
            location (tuple, optional): Lat/lng tuple to bias results. Defaults to Maryland center
            radius (int, optional): Radius in meters to bias results. Defaults to 50km
            
        Returns:
            list: List of place suggestions with their details
        """
        try:
            params = {
                'input_text': input_text,
                'components': {'country': 'us'},
                'strict_bounds': True
            }
            
            # Add location bias
            if location:
                params['location'] = {'lat': location[0], 'lng': location[1]}
                if radius:
                    params['radius'] = radius

            result = self.gmaps.places_autocomplete(**params)
            
            # Format the results
            suggestions = [{
                'place_id': place['place_id'],
                'description': place['description'],
                'main_text': place.get('structured_formatting', {}).get('main_text', ''),
                'secondary_text': place.get('structured_formatting', {}).get('secondary_text', '')
            } for place in result]
            
            return suggestions
            
        except Exception as e:
            print(f"✗ Error getting place suggestions: {str(e)}")
            return []

def calculate_travel_scenario(current_location, next_booking_location, home_location, 
                            current_booking_end, next_booking_start):
    """Calculate optimal travel scenario between bookings"""
    calculator = TravelTimeCalculator()
    
    # Convert lists to tuples for caching
    origins = tuple([current_location, home_location])
    destinations = tuple([next_booking_location, home_location])
    
    travel_times = calculator.get_travel_times(origins, destinations, current_booking_end)
    
    # Use string keys when accessing the dictionary
    direct_travel = travel_times[str(current_location)][str(next_booking_location)]
    to_home = travel_times[str(current_location)][str(home_location)]
    from_home = travel_times[str(home_location)][str(next_booking_location)]
    
    # Calculate time gap in minutes
    time_gap = (next_booking_start - current_booking_end).total_seconds() / 60
    direct_minutes = _convert_time_to_minutes(direct_travel)
    
    if time_gap < (direct_minutes + 60):
        return {
            'recommendation': 'direct',
            'travel_time': direct_travel,
            'adjusted_start': next_booking_start - timedelta(minutes=direct_minutes + 30)
        }
    
    to_home_minutes = _convert_time_to_minutes(to_home)
    from_home_minutes = _convert_time_to_minutes(from_home)
    time_at_home = time_gap - (to_home_minutes + from_home_minutes)
    
    if time_at_home > 90:
        return {
            'recommendation': 'home',
            'travel_time_to_home': to_home,
            'travel_time_from_home': from_home,
            'time_at_home': f"{time_at_home} minutes",
            'adjusted_start': next_booking_start - timedelta(minutes=from_home_minutes + 30)
        }
    
    return {
        'recommendation': 'direct',
        'travel_time': direct_travel,
        'adjusted_start': next_booking_start - timedelta(minutes=direct_minutes + 30)
    }

def _convert_time_to_minutes(time_str):
    """Convert Google Maps time string to minutes"""
    try:
        if 'hour' in time_str.lower():
            parts = time_str.split()
            hours = int(parts[0])
            minutes = int(parts[2]) if len(parts) > 3 else 0
            return hours * 60 + minutes
        else:
            return int(time_str.split()[0])
    except Exception as e:
        raise

if __name__ == "__main__":
    # Test scenario
    current_location = "New Jersey"
    next_location = "Washington DC"
    home = "5159 Pooks Hill Rd, Bethesda, MD"
    
    current_end = datetime.now()
    next_start = current_end + timedelta(hours=3)
    
    try:
        # First call will query the API
        result1 = calculate_travel_scenario(
            current_location, next_location, home,
            current_end, next_start
        )
        print("\nFirst Query Results:")
        for key, value in result1.items():
            print(f"{key}: {value}")
            
        # Second call with same locations will use cached results
        result2 = calculate_travel_scenario(
            current_location, next_location, home,
            current_end, next_start
        )
        print("\nSecond Query Results (from cache):")
        for key, value in result2.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error calculating travel scenario: {e}")


