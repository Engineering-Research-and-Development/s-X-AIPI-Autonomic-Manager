import json
import requests
import time

def send_json_to_endpoint(file_path: str, endpoint_url: str):
    with open(file_path, 'r') as file:
        data = json.load(file)

    start_time = time.time()
    response = requests.post(endpoint_url, json=data)
    end_time = time.time()

    response_time = end_time - start_time

    return response.status_code, response_time
