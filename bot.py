import requests

def get_ai_response(messages):
    api_url = "https://ai-aihackthonhub282549186415.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2025-01-01-preview"
    api_key = "Fj1KPt7grC6bAkNja7daZUstpP8wZTXsV6Zjr2FOxkO7wsBQ5SzQJQQJ99BCACHYHv6XJ3w3AAAAACOGL3Xg"

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    data = {
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def itinerary_planner():
    print("Welcome to the AI-assisted Itinerary Planner!")

    messages = [
        {"role": "system", "content": "You are a helpful travel assistant who creates and updates detailed and personalized travel itineraries. Take feedback and adjust the plan accordingly. Continue the conversation until the user says 'thanks'."}
    ]

    # Collect initial user inputs
    destination = input("Where do you want to travel? ")
    duration = input("How many days will you stay? ")
    interests = input("What are your interests? (e.g., adventure, culture, relaxation, food) ")
    budget = input("What is your budget level? (e.g., low, medium, high) ")

    # Create initial prompt
    user_message = f"I want to travel to {destination} for {duration} days. My interests are {interests}, and my budget is {budget}. Can you plan a detailed itinerary for me?"

    messages.append({"role": "user", "content": user_message})

    while True:
        # Get AI-generated itinerary
        itinerary = get_ai_response(messages)

        if itinerary:
            print("\nHere is your personalized travel itinerary:\n")
            print(itinerary)

        # Get user feedback
        feedback = input("\nWould you like any changes or additions to your itinerary? (Type 'thanks' to end) ")

        if feedback.lower() == "thanks":
            print("You're welcome! Enjoy your trip!")
            break

        # Add user feedback to messages and continue conversation
        messages.append({"role": "user", "content": feedback})

if __name__ == "__main__":
    itinerary_planner()
