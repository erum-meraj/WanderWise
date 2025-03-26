import requests
import json

# Azure OpenAI API Configuration
AZURE_OPENAI_ENDPOINT = "https://ai-aihackthonhub282549186415.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2025-01-01-preview"
API_KEY = "Fj1KPt7grC6bAkNja7daZUstpP8wZTXsV6Zjr2FOxkO7wsBQ5SzQJQQJ99BCACHYHv6XJ3w3AAAAACOGL3Xg"  # Replace with your Azure API Key

def get_ai_response(messages):
    headers = {
        'Content-Type': 'application/json',
        'api-key': API_KEY
    }

    payload = {
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }

    response = requests.post(AZURE_OPENAI_ENDPOINT, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        print("Error:", response.status_code, response.text)
        return "Sorry, I am having trouble processing your request."

def travel_bot():
    print("Welcome to the Travel Assistant Bot! Please let me know how can I help you!")

    messages = [{"role": "system", "content": "You are a helpful travel assistant that helps users plan trips and answer travel queries."}]

    while True:
        user_input = input("You: ")

        if user_input.lower() == "thanks":
            print("Bot: You're welcome! Have a safe journey!")
            break

        messages.append({"role": "user", "content": user_input})

        ai_response = get_ai_response(messages)
        print("Bot:", ai_response)

        # Store bot response for context
        messages.append({"role": "assistant", "content": ai_response})

if __name__ == "__main__":
    travel_bot()