import json
import os
import requests

collection_path = 'collection.json'
orion_ip = "136.243.156.113"
output_folder = './outputs'


def load_postman_collection(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def extract_after_urn(url):
    urn_index = url.find("urn:")
    if urn_index != -1:  # If "urn:" is found in the URL
        return url[urn_index + len("urn:"):]
    else:
        return None  # Return None if "urn:" is not found


def find_requests_with_window(item):
    requests_with_window = []

    if isinstance(item, dict) and 'item' in item:
        for sub_item in item['item']:
            requests_with_window.extend(find_requests_with_window(sub_item))
    elif 'name' in item and 'Get Smaller Window' in item['name']:
        requests_with_window.append(item)
    elif 'name' in item and 'Get Larger Window' in item['name']:
        requests_with_window.append(item)

    return requests_with_window


def replace_placeholders(url, ip):
    return url.replace('{{orion}}', ip)


def make_requests(requests_with_window, ip):
    responses = []
    for request in requests_with_window:
        method = request['request']['method'].lower()
        raw_url = request['request']['url']['raw']
        url = replace_placeholders(raw_url, ip)

        if method == 'get':
            response = requests.get(url)
        elif method == 'post':
            response = requests.post(url, data=request['request'].get('body', {}).get('raw', ''))
        else:
            print(f"Method {method.upper()} not supported in this example.")
            continue

        responses.append((url, response.status_code, response.text, response.json()))
    return responses


def json_to_turtle(json_data):
    turtle_lines = [
        '@prefix dcat: <http://www.w3.org/ns/dcat#> .',
        '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
        '@prefix ex: <http://example.org/> .',
        ''
    ]
    try:
        entity_id = json_data["id"].split(":")[-1]
    except KeyError:
        print(json_data)
        exit(1)
    entity_type = json_data["type"]

    turtle_lines.append(f"ex:{entity_id} a ex:{entity_type} ;")

    for key, value in json_data.items():
        if key not in ["@context", "id", "type"]:
            prop_value = value["value"]
            prop_lines = [f"    ex:{key} [", "        a dcat:Property ;"]

            for prop_key, prop_val in prop_value.items():
                if prop_key == "value":
                    try:
                        val = float(prop_val)
                        if val.is_integer():
                            prop_lines.append(f"        ex:{prop_key} \"{int(val)}\"^^xsd:integer ;")
                        else:
                            prop_lines.append(f"        ex:{prop_key} \"{val}\"^^xsd:decimal ;")
                    except ValueError:
                        prop_lines.append(f"        ex:{prop_key} \"{prop_val}\" ;")
                elif prop_key == "dateObserved":
                    prop_lines.append(f"        ex:{prop_key} \"{prop_val}\"^^xsd:dateTime ;")
                elif prop_key == "timeWindowLengthMinutes":
                    prop_lines.append(f"        ex:{prop_key} \"{int(prop_val)}\"^^xsd:integer ;")
                else:
                    prop_lines.append(f"        ex:{prop_key} \"{prop_val}\" ;")

            prop_lines[-1] = prop_lines[-1].replace(" ;", "")
            prop_lines.append("    ] ;")
            turtle_lines.extend(prop_lines)

    turtle_lines[-1] = turtle_lines[-1].replace(" ;", " .")

    return "\n".join(turtle_lines)


def main():

    collection = load_postman_collection(collection_path)
    requests_with_window = find_requests_with_window(collection)

    if requests_with_window:
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
        responses = make_requests(requests_with_window, orion_ip)
        for url, status_code, text, json_response in responses:
            turtle_data = json_to_turtle(json_response)
            output_file = f"{output_folder}/{extract_after_urn(url)}.ttl"
            with open(output_file, 'w') as file:
                file.write(turtle_data)


if __name__ == "__main__":
    main()
