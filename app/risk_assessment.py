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
