from flask import Flask, request, jsonify, session
import requests
import json

app = Flask(__name__)


# Configuration
API_KEY = "Fj1KPt7grC6bAkNja7daZUstpP8wZTXsV6Zjr2FOxkO7wsBQ5SzQJQQJ99BCACHYHv6XJ3w3AAAAACOGL3Xg"
API_URL = "https://aiiitphackathon797339300099.openai.azure.com/openai/deployments/gpt-35-turbo/chat/completions?apiversion=2025-01-01-preview"
DEPLOYMENT_NAME = "gpt-35-turbo"

def extract_travel_info(user_message):
    try:
        
        # System message with instructions
        system_message = {
            "role": "system",
            "content": """You are a helpful assistant that extracts travel information from text. Extract the following parameters in JSON format:

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

            Return ONLY the JSON object with the extracted parameters. Do not include any additional text or explanations."""
        }

        # Prepare messages for the API call
        messages = [
            system_message,
            {"role": "user", "content": f"Extract travel parameters from: {user_message}"}
        ]

        headers = {
            "Content-Type": "application/json",
            "api-key": API_KEY,
        }

        payload = {
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            # Parse the response
            ai_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            
            try:
                # Handle potential markdown formatting
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0].strip()
                
                extracted_data = json.loads(ai_response)
                
                # Structure the response
                result = {
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
                print(result)
                return jsonify(result)
                
            except json.JSONDecodeError:
                return jsonify({"error": "Failed to parse AI response"}), 500
            except Exception as e:
                return jsonify({"error": f"Error processing response: {str(e)}"}), 500
                
        else:
            error_msg = f"API error: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text[:200]}"
            return jsonify({"error": error_msg}), response.status_code
            
    except Exception as e:
        print(f"Internal server error: {str(e)}")
        # return jsonify({"error": f"Internal server error: {str(e)}"}), 500

extract_travel_info("I need to book a hotel in New York for 2 adults from 2023-12-15 to 2023-12-20. We need 1 room. Also, I need flights from LAX to JFK on December 14th for 2 adults.")