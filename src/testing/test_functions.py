import json
import requests
import time

endpoint= "http://localhost:8001/steel"
max_requests = 100
json_test_wrong = "test_wrong.json"
json_test_correct = "test_correct.json"


def get_response(data, endpoint_url):
    start_time = time.time()
    response = requests.post(endpoint_url, json=data)
    end_time = time.time()

    response_time = end_time - start_time

    return response.status_code, response_time

def test_single_response():
    with open(json_test_correct, 'r') as file:
        data = json.load(file)
    response, timing = get_response(data, endpoint)
    print(f"Response single request: {timing}")
    assert response == 200, f"Request error {response}"

def test_total_time():
    total_time = 0
    with open(json_test_correct, 'r') as file:
        data = json.load(file)

    for _ in range(0, int(max_requests / 2)):
        response, timing = get_response(data, endpoint)
        if response == 200:
            total_time += timing

    average_time = total_time / (max_requests / 2)
    print(f"Average time: {average_time}")

    assert average_time > 0, "Average time must be greater than 0"


def test_error_rate():
    error_rate = 0
    with open(json_test_wrong, 'r') as file:
        data = json.load(file)

    for _ in range(0, int(max_requests / 2)):
        wrong_response, _ = get_response(data, endpoint)
        if wrong_response != 200:
            error_rate += 1

    print(f"Error rate: {error_rate}/{int(max_requests/2)}")

    assert error_rate == int(max_requests / 2), "Error rate mismatch"
