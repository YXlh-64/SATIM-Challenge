import requests
import os
from dotenv import load_dotenv

def test_api_key():
    load_dotenv()
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://localhost:5000",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": "Hello, are you working?"}]
    }
    
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=payload
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        print("API Key is working!")
        print("Response:", response.json()['choices'][0]['message']['content'])
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    test_api_key()