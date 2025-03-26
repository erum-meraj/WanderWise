from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# Amadeus API credentials
CLIENT_ID = "Xwjs1dXdMvJYJhoOuZWON44ImGCwpZZI"
CLIENT_SECRET = "6ugKGuGqpHORjpCd"
ACCESS_TOKEN = None

def get_access_token():
    """Get access token from Amadeus API"""
    global ACCESS_TOKEN
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
        ACCESS_TOKEN = response.json()["access_token"]
        return True
    except Exception as e:
        print(f"Error obtaining access token: {e}")
        return False

def format_date(date_str):
    """Format date from YYYY-MM-DD to Month Day, Year"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except:
        return date_str

def format_room_description(desc):
    """Format room description by replacing newlines with HTML breaks"""
    if not desc:
        return ""
    return desc.replace("\n", "<br>")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        params = {
            'hotelIds': request.form['hotelIds'].split(','),
            'adults': int(request.form['adults']),
            'checkInDate': request.form['checkInDate'],
            'checkOutDate': request.form['checkOutDate'],
            'roomQuantity': int(request.form['roomQuantity']),
            'currency': request.form['currency']
        }

        if not ACCESS_TOKEN and not get_access_token():
            return render_template('error.html', message="Failed to authenticate with Amadeus API")
        
        url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        try:
            print(headers, params)
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Format all dates before passing to template
            for hotel in data.get('data', []):
                hotel['formatted_checkInDate'] = format_date(params['checkInDate'])
                hotel['formatted_checkOutDate'] = format_date(params['checkOutDate'])
                for offer in hotel.get('offers', []):
                    offer['formatted_checkInDate'] = format_date(offer['checkInDate'])
                    offer['formatted_checkOutDate'] = format_date(offer['checkOutDate'])
                    offer['room']['description']['formatted_text'] = format_room_description(
                        offer['room']['description']['text']
                    )
                    # Format dates in price variations
                    if 'variations' in offer['price'] and 'changes' in offer['price']['variations']:
                        for change in offer['price']['variations']['changes']:
                            change['formatted_startDate'] = format_date(change['startDate'])
                            change['formatted_endDate'] = format_date(change['endDate'])
            
            return render_template('results.html', 
                                hotels=data.get('data', []),
                                search_params=params,
                                format_date=format_date)  # Pass the function to template
        except Exception as e:
            return render_template('error.html', message=f"Error fetching hotel offers: {str(e)}")
    
    # Set default dates
    default_check_in = datetime.now().strftime('%Y-%m-%d')
    default_check_out = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    return render_template('index.html', 
                        default_check_in=default_check_in,
                        default_check_out=default_check_out)
if __name__ == '__main__':
    get_access_token()
    app.run(debug=True)