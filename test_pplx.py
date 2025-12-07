import os
import requests
from dotenv import load_dotenv

# --- 1. SETUP ---
# Load the API key from your .env file, just like your main app.
print("--- Perplexity API Key Tester ---")
load_dotenv()
API_KEY = os.getenv("PERPLEXITY_API_KEY")

# --- 2. VALIDATE THE KEY ---
# Check if the key was found and isn't a placeholder.
if not API_KEY or "your-secret" in API_KEY or "paste-your" in API_KEY:
    print("❌ FAILURE: Your PERPLEXITY_API_KEY is missing or is still a placeholder in the .env file.")
    print("Please make sure your .env file is in the same folder and has the correct key.")
    exit()

print(f"🔑 Key Found: Starting with '{API_KEY[:5]}...{API_KEY[-4:]}'")

# --- 3. PREPARE THE API CALL ---
# This is the same information your tool uses.
URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar"
PROMPT = "Hello, world!"

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": PROMPT}]
}
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {API_KEY}"
}

# --- 4. EXECUTE AND REPORT ---
print(f"📞 Calling the Perplexity API with the '{MODEL}' model...")
try:
    # Make the request with a timeout
    response = requests.post(URL, json=payload, headers=headers, timeout=15)

    # This line will automatically raise an error for bad status codes (like 401, 400, 500)
    response.raise_for_status()

    # If we get here, the request was successful (200 OK)
    data = response.json()
    response_text = data['choices'][0]['message']['content']

    print("\n✅ SUCCESS! The API call worked.")
    print(f"🤖 Perplexity responded: '{response_text}'")

except requests.exceptions.HTTPError as e:
    print("\n❌ FAILURE: The API returned an error.")
    if e.response.status_code == 401:
        print("   Error Type: 401 Unauthorized")
        print("   This means your PERPLEXITY_API_KEY is incorrect or invalid.")
    elif e.response.status_code == 400:
        print("   Error Type: 400 Bad Request")
        print("   This means the request was malformed. This is unlikely with this test script.")
    else:
        print(f"   HTTP Error: {e}")

except Exception as e:
    print(f"\n❌ FAILURE: An unexpected error occurred: {e}")