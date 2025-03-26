import requests
from datetime import datetime

# Amadeus API credentials
CLIENT_ID = "Xwjs1dXdMvJYJhoOuZWON44ImGCwpZZI"
CLIENT_SECRET = "6ugKGuGqpHORjpCd"
ACCESS_TOKEN = None
TOKEN_EXPIRATION = None

def get_access_token():
    """Get access token from Amadeus API"""
    global ACCESS_TOKEN, TOKEN_EXPIRATION
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        ACCESS_TOKEN = token_data["access_token"]
        expires_in = token_data.get("expires_in", 1800)
        TOKEN_EXPIRATION = datetime.now().timestamp() + expires_in
        return True
    except Exception as e:
        print(f"Error obtaining access token: {e}")
        return False

def format_datetime(dt_str):
    """Format datetime string to a more readable format"""
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%b %d, %Y %H:%M')
    except:
        return dt_str

def get_flight_offers():
    """
    Get flight offers from Amadeus API with static parameters:
    - Origin: BOM (Mumbai)
    - Destination: PAR (Paris)
    - Date: March 29, 2025 (formatted as 2025-03-29)
    - 2 adults
    - USD currency
    - Maximum 2 flight offers
    """
    flight_data = {
        "originDestinations": [
            {
                "id": "1",
                "originLocationCode": "BOM",
                "destinationLocationCode": "PAR",
                "departureDateTimeRange": {
                    "date": "2025-03-29"
                }
            }
        ],
        "travelers": [
            {
                "id": "1",
                "travelerType": "ADULT",
                "fareOptions": ["STANDARD"]
            },
            {
                "id": "2",
                "travelerType": "ADULT",
                "fareOptions": ["STANDARD"]
            }
        ],
        "sources": ["GDS"],
        "searchCriteria": {
            "maxFlightOffers": 2  # Changed to return maximum 2 flight offers
        },
        "currencyCode": "USD"
    }
    
    # Get access token if needed
    if not ACCESS_TOKEN or datetime.now().timestamp() >= TOKEN_EXPIRATION:
        if not get_access_token():
            return {"error": "Failed to authenticate with Amadeus API"}
    
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=flight_data)
        response.raise_for_status()
        flight_offers = response.json()
        
        # Format datetime strings in the response
        for offer in flight_offers.get('data', []):
            for itinerary in offer.get('itineraries', []):
                for segment in itinerary.get('segments', []):
                    segment['departure']['at'] = format_datetime(segment['departure']['at'])
                    segment['arrival']['at'] = format_datetime(segment['arrival']['at'])
        
        return flight_offers.get('data', [])
    
    except Exception as e:
        return {"error": f"Error fetching flight offers: {str(e)}"}

# Example usage
if __name__ == '__main__':
    # Initialize the access token
    get_access_token()
    
    # Get flight offers with static parameters
    result = get_flight_offers()
    
    print(result)