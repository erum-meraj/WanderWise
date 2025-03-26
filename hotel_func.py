import requests
from datetime import datetime

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

def get_hotel_offers():
    """
    Get hotel offers from Amadeus API with static parameters:
    - hotelIds: ['MCLONGHM']
    - adults: 2
    - checkInDate: 2025-03-29
    - checkOutDate: 2025-03-31
    - roomQuantity: 1
    - currency: USD
    """
    params = {
        'hotelIds': ['MCLONGHM'],
        'adults': 2,
        'checkInDate': '2025-03-29',
        'checkOutDate': '2025-03-31',
        'roomQuantity': 1,
        'currency': 'USD'
    }

    if not ACCESS_TOKEN and not get_access_token():
        return {"error": "Failed to authenticate with Amadeus API"}
    
    url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Format all dates in the response
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
        
        return data.get('data', [])
    
    except Exception as e:
        return {"error": f"Error fetching hotel offers: {str(e)}"}

# Example usage
if __name__ == '__main__':
    # Initialize the access token
    get_access_token()
    
    # Get hotel offers with static parameters
    result = get_hotel_offers()
    
    print(result)