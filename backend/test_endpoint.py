import requests

try:
    response = requests.get("http://127.0.0.1:8000/records?machine=SSB1080&rtype=Spindle")
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
