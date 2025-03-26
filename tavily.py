# Tavily Search API Integration in Python

import requests
import json

def tavily_search(query, api_key, max_results=5):
    """Fetch search results from the Tavily Search API."""
    url = "https://api.tavily.com/search"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "api_key": api_key,
        "max_results": max_results
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        if "results" in data:
            return data["results"]
        else:
            print("No results found.")
            return []

    except requests.RequestException as e:
        print(f"Error fetching search results: {e}")
        return []

def display_results(results):
    """Display the search results in a readable format."""
    for index, result in enumerate(results, start=1):
        print(f"\nResult {index}:")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")
        print(f"Snippet: {result.get('snippet', 'N/A')}")

if __name__ == "__main__":
    # Replace 'your_api_key' with your actual Tavily API key
    TAVILY_API_KEY = "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"

    user_query = input("Enter your search query: ")

    print("\nSearching...\n")
    search_results = tavily_search(user_query, TAVILY_API_KEY)

    if search_results:
        display_results(search_results)
    else:
        print("No search results found.")
