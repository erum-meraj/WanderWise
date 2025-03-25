import requests
import json
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
        expires_in = token_data.get("expires_in", 1800)  # Default to 30 minutes if not provided
        TOKEN_EXPIRATION = datetime.now().timestamp() + expires_in
        print("Successfully obtained access token")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining access token: {e}")
        if response.status_code == 401:
            print("Invalid API credentials. Please check your CLIENT_ID and CLIENT_SECRET.")
        return False

def is_token_valid():
    """Check if the current token is still valid"""
    if not ACCESS_TOKEN or not TOKEN_EXPIRATION:
        return False
    return datetime.now().timestamp() < TOKEN_EXPIRATION - 60  # 1 minute buffer

def get_flight_offers(origin_destinations, travelers, max_offers=1):
    """Fetch flight offers from Amadeus API"""
    if not is_token_valid():
        if not get_access_token():
            return None
    
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "originDestinations": origin_destinations,
        "travelers": travelers,
        "sources": ["GDS"],
        "searchCriteria": {
            "maxFlightOffers": max_offers
        }
    }
    
    try:
        print("\nSearching for flight offers...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        if response.status_code == 401:  # Token might be expired
            print("Attempting to refresh access token...")
            if get_access_token():
                return get_flight_offers(origin_destinations, travelers, max_offers)
        return None
    except Exception as e:
        print(f"Error fetching flight offers: {e}")
        return None

def validate_airport_code(code):
    """Validate airport IATA code format"""
    return len(code) == 3 and code.isalpha()

def validate_date(date_str):
    """Validate date format (YYYY-MM-DD) and ensure it's in the future"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date.date() < datetime.now().date():
            print("Warning: Date is in the past.")
        return True
    except ValueError:
        return False

def get_user_input():
    """
    Get flight details from user input with validation
    Returns a dictionary with all collected flight search parameters
    """
    input_data = {
        "originDestinations": [],
        "travelers": [],
        "searchCriteria": {
            "maxFlightOffers": 1
        }
    }

    print("Enter your flight itinerary (enter 'done' when finished):")
    i = 1
    while True:
        print(f"\nFlight Leg {i}:")
        origin = input("  - Origin airport code (3 letters, e.g., MAD): ").strip().upper()
        if origin.lower() == 'done':
            if i == 1:
                print("Please enter at least one flight leg.")
                continue
            break
            
        if not validate_airport_code(origin):
            print("Invalid airport code. Must be 3 letters (e.g., MAD, JFK).")
            continue
            
        destination = input("  - Destination airport code (3 letters, e.g., PAR): ").strip().upper()
        if not validate_airport_code(destination):
            print("Invalid airport code. Must be 3 letters (e.g., MAD, JFK).")
            continue
            
        date = input("  - Departure date (YYYY-MM-DD): ").strip()
        if not validate_date(date):
            print("Invalid date format. Please use YYYY-MM-DD.")
            continue
            
        input_data["originDestinations"].append({
            "id": str(i),
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDateTimeRange": {
                "date": date
            }
        })
        i += 1
    
    print("\nTraveler Information:")
    while True:
        try:
            num_adults = int(input("Number of adult travelers (1-9): "))
            if 1 <= num_adults <= 9:
                break
            print("Please enter a number between 1 and 9.")
        except ValueError:
            print("Please enter a valid number.")
    
    for i in range(1, num_adults + 1):
        input_data["travelers"].append({
            "id": str(i),
            "travelerType": "ADULT",
            "fareOptions": ["STANDARD"]
        })
    
    print("\nSearch Options:")
    while True:
        try:
            max_offers = int(input("Maximum number of flight offers to return (1-10): "))
            if 1 <= max_offers <= 10:
                input_data["searchCriteria"]["maxFlightOffers"] = max_offers
                break
            print("Please enter a number between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Add additional required fields
    input_data["sources"] = ["GDS"]
    
    return input_data

def display_flight_offers(flight_offers):
    """Display flight offers in a readable format"""
    if not flight_offers or 'data' not in flight_offers or not flight_offers['data']:
        print("\nNo flight offers found for your search criteria.")
        return
    
    print("\n" + "="*50)
    print("Flight Offers Results".center(50))
    print("="*50)
    
    for i, offer in enumerate(flight_offers['data'], 1):
        print(f"\n➤ Offer {i}:")
        print(f"  Price: {offer['price']['total']} {offer['price']['currency']}")
        print(f"  Booking Options: {len(offer['itineraries'])} itinerary options available")
        
        for idx, itinerary in enumerate(offer['itineraries'], 1):
            print(f"\n  Itinerary {idx}:")
            total_duration = itinerary['duration']
            print(f"  Total Duration: {total_duration}")
            
            for segment in itinerary['segments']:
                print(f"\n    Flight: {segment['carrierCode']}{segment['number']}")
                print(f"    Departure: {segment['departure']['iataCode']} at {segment['departure']['at']}")
                print(f"    Arrival: {segment['arrival']['iataCode']} at {segment['arrival']['at']}")
                print(f"    Duration: {segment['duration']}")
                if 'aircraft' in segment:
                    print(f"    Aircraft: {segment['aircraft']['code']}")
                if 'operating' in segment:
                    print(f"    Operated by: {segment['operating']['carrierCode']}{segment['operating']['number']}")
        
        print("\n" + "-"*50)



def flight_details():
    if not get_access_token():
        print("Unable to connect to Amadeus API. Please check your credentials and internet connection.")
        return
    

    origin_destinations, travelers, max_offers = get_user_input()
    flight_offers = get_flight_offers(origin_destinations, travelers, max_offers)
    
    if flight_offers:
        display_flight_offers(flight_offers)
        
                
def main():
    flight_details() 

if __name__ == "__main__":
    main()