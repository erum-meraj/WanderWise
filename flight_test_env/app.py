from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

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

def validate_airport_code(code):
    """Validate airport IATA code format"""
    return len(code) == 3 and code.isalpha()

def format_datetime(dt_str):
    """Format datetime string to a more readable format"""
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%b %d, %Y %H:%M')
    except:
        return dt_str

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        flight_data = {
            "originDestinations": [],
            "travelers": [],
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": int(request.form.get('max_offers', 1))
            }
        }
        
        # Process flight legs
        i = 1
        while True:
            origin = request.form.get(f'origin_{i}')
            if not origin:
                break
            destination = request.form.get(f'destination_{i}')
            date = request.form.get(f'date_{i}')
            
            flight_data["originDestinations"].append({
                "id": str(i),
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDateTimeRange": {
                    "date": date
                }
            })
            i += 1
        
        # Process travelers
        num_adults = int(request.form.get('num_adults', 1))
        for i in range(1, num_adults + 1):
            flight_data["travelers"].append({
                "id": str(i),
                "travelerType": "ADULT",
                "fareOptions": ["STANDARD"]
            })
        
        # Get flight offers
        if not ACCESS_TOKEN or datetime.now().timestamp() >= TOKEN_EXPIRATION:
            if not get_access_token():
                return render_template('error.html', message="Failed to authenticate with Amadeus API")
        
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=flight_data)
            response.raise_for_status()
            flight_offers = response.json()
            
            # Format datetime strings before passing to template
            for offer in flight_offers.get('data', []):
                for itinerary in offer.get('itineraries', []):
                    for segment in itinerary.get('segments', []):
                        segment['departure']['at'] = format_datetime(segment['departure']['at'])
                        segment['arrival']['at'] = format_datetime(segment['arrival']['at'])
            
            return render_template('results.html', offers=flight_offers.get('data', []))
        except Exception as e:
            return render_template('error.html', message=f"Error fetching flight offers: {str(e)}")
    
    return render_template('index.html')

if __name__ == '__main__':
    get_access_token()
    app.run(debug=True)