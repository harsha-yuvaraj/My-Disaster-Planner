import requests
from flask import current_app

# This dictionary maps FEMA codes to their descriptions.
FLOOD_ZONE_DEFINITIONS = {
    'High Risk': {
        'codes': ['A', 'AE', 'AH', 'AO', 'A99', 'AR', 'V', 'VE'],
        'description': 'Area with a 1% or greater annual chance of flooding.'
    },
    'Moderate Risk': {
        'codes': ['B'],
        'description': 'Area with a 0.2% annual chance of flooding.'
    },
    'Minimal Risk': {
        'codes': ['C'],
        'description': 'Area is outside the high and moderate risk floodplains.'
    }
}

def get_flood_zone_details(zone_code_string):
    """
    Looks up the risk level and description for a given FEMA flood zone string.
    If multiple zones are provided (e.g., "AE, X"), it returns the description
    for the highest risk category found.
    """
    if not zone_code_string or zone_code_string == "No infomation available":
        return {'risk': '', 'description': ''}

    # Split the input string into a list of individual zone codes
    received_zones = [zone.strip() for zone in zone_code_string.split(',')]

    # Check for High Risk zones first (highest priority)
    for zone in received_zones:
        if any(zone.startswith(code_prefix) for code_prefix in FLOOD_ZONE_DEFINITIONS['High Risk']['codes']):
            return {'risk': 'High Risk', 'description': FLOOD_ZONE_DEFINITIONS['High Risk']['description']}

    # If no High Risk zones, check for Moderate Risk zones
    for zone in received_zones:
        if any(zone.startswith(code_prefix) for code_prefix in FLOOD_ZONE_DEFINITIONS['Moderate Risk']['codes']):
            return {'risk': 'Moderate Risk', 'description': FLOOD_ZONE_DEFINITIONS['Moderate Risk']['description']}

    # If no high or moderate risk zones are found, it's minimal risk or undetermined
    for zone in received_zones:
        if any(zone.startswith(code_prefix) for code_prefix in FLOOD_ZONE_DEFINITIONS['Minimal Risk']['codes']):
            return {'risk': 'Minimal Risk', 'description': FLOOD_ZONE_DEFINITIONS['Minimal Risk']['description']}

    # Fallback for any other codes
    return {'risk': 'Undetermined', 'description': 'This zone has an undetermined flood risk.'}


def geocode_address(address):
    """Geocodes an address string to latitude and longitude."""

    """
    try:
        geolocator = Nominatim(user_agent=f"my_disaster_planner")
        location = geolocator.geocode(address, timeout=10)
        if location:
            print("Geocoded using Nominatim.")
            return (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        pass
    """
        
    try:
        response = requests.get(current_app.config["GOOGLE_GEOCODE_API_URL"], params={'address': address, 'key': current_app.config["GOOGLE_API_KEY"]}, timeout=6)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK' and data.get('results'):
            return (data['results'][0]['geometry']['location']['lat'], data['results'][0]['geometry']['location']['lng'], data['results'][0]['formatted_address'])
        
    except requests.exceptions.RequestException as e:
        print(f"Google Geocode API request failed: {e}")
    
    return None


def get_flood_risk(lat, lon):
    """
    Queries FEMA and identifies all applicable high-risk flood zones for a location.
    """
    params = {
        'f': 'json', 'geometryType': 'esriGeometryPoint', 'geometry': f'{lon},{lat}',
        'sr': '4326', 'layers': 'all:28', 'tolerance': '1',
        'mapExtent': f'{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}', # Smaller extent for precision
        'imageDisplay': '400,300,96'
    }
    try:
        response = requests.get(current_app.config["FEMA_NFHL_IDENTIFY_URL"], params=params, timeout=6)
        response.raise_for_status()
        data = response.json()
        
        high_risk_zones = []
        if data.get('results'):
            # Loop through ALL results to find high-risk zones
            for result in data['results']:
                attrs = result.get('attributes', {})
                # Check the official FEMA flag for Special Flood Hazard Area
                if attrs.get('SFHA_TF') == 'T':
                    zone = attrs.get('FLD_ZONE')
                    if zone:
                        high_risk_zones.append(zone)

        # If we found any high-risk zones, report them
        if high_risk_zones:
            # Remove duplicates and sort for consistent output
            unique_zones = sorted(list(set(high_risk_zones)))
            zone_str = ", ".join(unique_zones)
            description = get_flood_zone_details(zone_str)

            # Return only the zone string
            return (zone_str, description)
        
        # If no high-risk zones, report the first available low-risk zone
        elif data.get('results'):
            first_zone = data['results'][0].get('attributes', {}).get('FLD_ZONE', '').strip()
            if first_zone == 'X':
                description = {'risk': data['results'][0].get('attributes', {}).get('ZONE_SUBTY', ""), 'description': ""}
            else:
                description = get_flood_zone_details(first_zone)

            # Return only the zone code
            return (first_zone, description)
        
        else:
            return ("No infomation available", {'risk': 'Undetermined', 'description': 'This zone has an undetermined flood risk.'})

    except (requests.exceptions.RequestException, KeyError, IndexError):
        print("Error querying FEMA NFHL identify service.")
        return ("No infomation available", {'risk': 'Undetermined', 'description': 'This zone has an undetermined flood risk.'})


def get_flood_risk_by_address(address):
    """
    Geocodes an address and queries FEMA to identify high-risk flood zones.
    """
    geocode_result = geocode_address(address)

    if not geocode_result:
        formatted_address = address
        lat, lon = '', ''
        flood_risk_zones, risk_meta_data = "No infomation available", {'risk': '', 'description': ''}
    else:
        lat, lon, formatted_address = geocode_result
        flood_risk_zones, risk_meta_data = get_flood_risk(lat, lon)

    return {
        'address': formatted_address,
        'flood_risk_zones': flood_risk_zones,
        'risk_level': risk_meta_data['risk'],
        'risk_description': risk_meta_data['description'],
        'latitude': lat,
        'longitude': lon
    }


def get_travel_distance_and_time(address_pairs):
    """
    Calculates the distance and travel time using the Google Routes API.

    Args:
        address_pairs (dict): A dictionary containing travel mode and address pairs.
            Example:
            {
              "travel_by": "car",
              "route1": {'source': '123 Main St, Anytown, USA', 'dest': '456 Oak Ave, Anytown, USA'}
            }

    Returns:
        dict: A dictionary with the same keys as the input address pairs, with values
              containing the distance in miles and the travel time in hours and minutes.
    """
    travel_by = address_pairs.get("travel_by", "car")
    # Google Routes API uses 'DRIVE' for car and 'TRANSIT' for bus
    google_travel_mode = "TRANSIT" if travel_by == "bus" else "DRIVE"

    results = {}
    api_key = current_app.config.get("GOOGLE_API_KEY")
    api_url = current_app.config.get("GOOGLE_ROUTES_API_URL")

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters'
    }

    for key, addresses in address_pairs.items():
        if key == "travel_by":
            continue

        source = addresses.get('source')
        dest = addresses.get('dest')

        if not source or not dest:
            results[key] = {
                'distance_miles': 'N/A',
                'time_hours': 'N/A',
                'time_minutes': 'N/A',
                'error': 'Source or destination address is missing.'
            }
            continue

        payload = {
            'origin': {'address': source},
            'destination': {'address': dest},
            'travelMode': google_travel_mode,
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()  # Raises an exception for 4xx/5xx errors
            data = response.json()

            # A successful request with no route found returns an empty JSON object {}
            if data and data.get('routes'):
                route = data['routes'][0]
                distance_meters = route.get('distanceMeters', 0)
                # Convert meters to miles (1 mile = 1609.34 meters)
                distance_miles = round(distance_meters / 1609.34, 1)

                # Duration is a string ending in 's' (e.g., "359s").
                duration_str = route.get('duration', '0s')
                duration_seconds = int(duration_str.rstrip('s'))
                
                time_hours = duration_seconds // 3600
                time_minutes = (duration_seconds % 3600) // 60

                results[key] = {
                    'distance_miles': distance_miles,
                    'time_hours': time_hours,
                    'time_minutes': time_minutes
                }
            else:
                # Handle cases where no route is found or API returns an error object
                error_message = data.get('error', {}).get('message', 'No route found.')
                results[key] = {
                    'distance_miles': 'N/A',
                    'time_hours': 'N/A',
                    'time_minutes': 'N/A',
                    'error': error_message
                }

        except requests.exceptions.RequestException as e:
            print(f"Google Routes API request failed for key '{key}': {e}")
            results[key] = {
                'distance_miles': 'N/A',
                'time_hours': 'N/A',
                'time_minutes': 'N/A',
                'error': 'API request failed.'
            }
        except (KeyError, IndexError, ValueError):
            # Handles issues with parsing the response (e.g., unexpected format, int conversion)
            results[key] = {
                'distance_miles': 'N/A',
                'time_hours': 'N/A',
                'time_minutes': 'N/A',
                'error': 'Could not parse API response.'
            }

    return results