import requests

url = "http://127.0.0.1:8000/invoke"
data = {
    "text": "When do I take my medicine?",
    "flow_type": "onldssssine", #offline or online
    "qa": "",
    "topic": ""
}

response = requests.post(url, json=data)
print(response.json())
