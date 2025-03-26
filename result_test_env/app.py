from flask import Flask, render_template
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
FLIGHT_API_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"
HOTEL_API_URL = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"

# API credentials (in a real app, these should be in environment variables)
FLIGHT_API_KEY = "P0H5Nt1hmixtoHkwUD6w8T8PG45J"
HOTEL_API_KEY = "jH4yZd6iyZEy8XF3NrreWC9FgcSP"

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


def get_flight_offers():
    """Fetch flight offers from Amadeus API"""
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
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
            "maxFlightOffers": 2
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flight offers: {e}")
        return []

def get_hotel_offers():
    """Fetch hotel offers from Amadeus API"""
    url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    params = {
        'hotelIds': 'MCLONGHM',
        'adults': 2,
        'checkInDate': '2025-03-29',
        'checkOutDate': '2025-03-31',
        'roomQuantity': 1,
        'currency': 'USD'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching hotel offers: {e}")
        return []

@app.route('/final_trip_paln')
def search_results():
    # Fetch data from APIs
    flight_offers = get_flight_offers()
    hotel_offers = get_hotel_offers()
    
    # Prepare search parameters for the template
    search_params = {
        'originLocationCode': 'BOM',
        'destinationLocationCode': 'PAR',
        'checkInDate': '2025-03-29',
        'checkOutDate': '2025-03-31',
        'adults': 2,
        'roomQuantity': 1
    }
    
    # Render the combined template
    return render_template(
        'combined_results.html',
        offers=flight_offers,
        hotels=hotel_offers,
        search_params=search_params
    )

if __name__ == '__main__':
    app.run(debug=True)