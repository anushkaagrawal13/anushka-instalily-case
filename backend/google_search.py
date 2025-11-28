# google_search.py
import os
import requests

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def google_partselect_search(query: str, num_results=3):
    """
    Use Google Custom Search, restricted to site:partselect.com
    Returns a list of (snippet, link).
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID in environment.")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": f"{query} site:partselect.com",
        "num": num_results
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" not in data:
        return []

    results = []
    for item in data["items"]:
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        results.append((snippet, link))
    return results

if __name__ == "__main__":
    # Test the search function manually
    query = "GE fridge model WR55X10942 control board"
    results = google_partselect_search(query, num_results=5)

    if not results:
        print("❌ No results found from PartSelect Google search.")
    else:
        print("\n🔍 **Google Search Results for PartSelect:**")
        for title, snippet, link in results:
            print(f"🔹 {title}\n   {snippet}\n   {link}\n")