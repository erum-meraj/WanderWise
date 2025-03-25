from flask import Flask, request, jsonify
from openai import AzureOpenAI  # Updated import
import json
import re

app = Flask(__name__)


client = AzureOpenAI(
    api_key="Fj1KPt7grC6bAkNja7daZUstpP8wZTXsV6Zjr2FOxkO7wsBQ5SzQJQQJ99BCACHYHv6XJ3w3AAAAACOGL3Xg",
    api_version="2023-05-15",  # Updated to a valid API version
    azure_endpoint="https://aiiitphackathon797339300099.openai.azure.com/"
)

DEPLOYMENT_NAME = "gpt-35-turbo"

def extract_parameters(text):
    
    system_message = """
    You are a helpful assistant that extracts travel information from text. Extract the following parameters in JSON format:

    Hotel parameters:
    - adults: number of adults (convert to integer)
    - checkInDate: check-in date in YYYY-MM-DD format
    - checkOutDate: check-out date in YYYY-MM-DD format
    - roomQuantity: number of rooms (convert to integer)
    - currency: currency code (default to USD if not specified)

    Flight parameters:
    - originDestinations: array of origin and destination objects with id, originLocationCode, destinationLocationCode, departureDateTime
    - travelers: array of traveler objects with id, travelerType (ADULT, CHILD, etc.)
    - sources: always set to ["GDS"]
    - searchCriteria: object with maxFlightOffers (default to 1 if not specified)

    Return ONLY the JSON object with the extracted parameters. Do not include any additional text or explanations.
    """

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Extract travel parameters from: {text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # Extract and parse the JSON content
        content = response.choices[0].message.content
        return json.loads(content)
    
    except json.JSONDecodeError:
        # If the response isn't valid JSON, try to extract just the JSON portion
        try:
            json_str = content[content.find('{'):content.rfind('}')+1]
            return json.loads(json_str)
        except:
            return None
    except Exception as e:
        print(f"Error extracting parameters: {str(e)}")
        return None

def extract_travel_info(text):
    if not text.strip():
        return {"error": "Empty text provided"}
    
    extracted_data = extract_parameters(text)
    
    if extracted_data is None:
        return {"error": "Failed to extract parameters from text"}
    
    # Structure the response
    response = {
        "hotel": {
            "adults": extracted_data.get("hotel", {}).get("adults"),
            "checkInDate": extracted_data.get("hotel", {}).get("checkInDate"),
            "checkOutDate": extracted_data.get("hotel", {}).get("checkOutDate"),
            "roomQuantity": extracted_data.get("hotel", {}).get("roomQuantity"),
            "currency": extracted_data.get("hotel", {}).get("currency", "USD")
        },
        "flights": {
            "originDestinations": extracted_data.get("flights", {}).get("originDestinations", []),
            "travelers": extracted_data.get("flights", {}).get("travelers", []),
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": extracted_data.get("flights", {}).get("searchCriteria", {}).get("maxFlightOffers", 1)
            }
        }
    }
    
    return response


print(extract_travel_info("I need to book a hotel in New York for 2 adults from 2023-12-15 to 2023-12-20. We need 1 room. Also, I need flights from LAX to JFK on December 14th for 2 adults."))