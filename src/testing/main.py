from functions import send_json_to_endpoint


if __name__ == '__main__':
    response, time = send_json_to_endpoint(file_path="test.json", endpoint_url="http://s-x-aipi-orion-catcher/pharma")
    if response == 200:
        print(f"Response single request: {time}")

    total_time = 0
    max_requests = 1000
    for _ in range(0,max_requests):
        response, time = send_json_to_endpoint(file_path="test.json", endpoint_url="http://s-x-aipi-orion-catcher/pharma")
        if response == 200:
            total_time += time
    total_time = total_time/max_requests
    print(f"Total time: {total_time}")