import json
import requests
import time

endpoint= "http://localhost:8001/pharma"
max_requests = 100
json_test_wrong = "test_wrong.json"
json_test_correct = "test_correct.json"

def send_json_to_endpoint(file_path: str, endpoint_url: str):
    with open(file_path, 'r') as file:
        data = json.load(file)

    start_time = time.time()
    response = requests.post(endpoint_url, json=data)
    end_time = time.time()

    response_time = end_time - start_time

    return response.status_code, response_time

def get_response(json_test_file, test_endpoint):
    response, timing = send_json_to_endpoint(file_path=json_test_file, endpoint_url=test_endpoint)
    return response, timing

def test_single_response():
    response, timing = get_response(json_test_correct, endpoint)
    if response == 200:
        print(f"Response single request: {time}")
        return True
    else:
        print(f"Response single request: {response}")
        return False

def test_multiple_responses():
    total_time = 0
    error_rate = 0
    for _ in range(0, int(max_requests/2)):
        response, timing = get_response(json_test_correct, endpoint)
        if response == 200:
            total_time += timing

        wrong_response, timing = get_response(json_test_wrong, endpoint)
        if wrong_response != 200:
            error_rate = error_rate + 1


    total_time = total_time/max_requests
    print(f"Total time: {total_time}")
    print(f"Total errors: {error_rate}")
    assert error_rate == int(max_requests/2)