import requests
import yaml

with ("config.yml", "r") as f:
    config = yaml.safe_load(f)


def check_existing_subscriptions(orion_endpoint: str, entity_type: str, callback_url: str) -> bool:
    """
    This function checks whether an active subscription already exists in the Orion Context Broker for a specific entity
    type and callback URL.

    Parameters:

        orion_endpoint (str): The URL endpoint of the Orion Context Broker instance.

        entity_type (str): The type of entity for which the subscription is being checked.

        callback_url (str): The callback URL associated with the subscription being checked.

    Returns:

        True if an active subscription matching the provided entity_type and callback_url is found.
        False if no active subscription matching the provided criteria is found or if there was an error while
        retrieving the subscriptions.

    Dependencies:

        requests: This function relies on the requests library to send HTTP requests.
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Make a GET request to retrieve existing subscriptions
    response = requests.get(orion_endpoint + '/v2/subscriptions', headers=headers)

    if response.status_code == 200:
        subscriptions = response.json()
        for subscription in subscriptions:
            if (subscription.get('subject', {}).get('entities', [{}])[0].get('type') == entity_type
                    and subscription.get('notification', {}).get('http', {}).get('url') == callback_url):
                return True
        return False
    else:
        print("Failed to retrieve subscriptions. Status code:", response.status_code)
        print("Response:", response.text)
        return False


def subscribe():
    """
    Perform the subscription to the entity using the parameters in the 'config' yaml file
    """
    subscription_payload = {
        "description": "Pharma subscription",
        "subject": {
            "entities": [{"idPattern": ".*", "type": config["entity"]}],
            "condition": {
                "attrs": config["attrs"]
            }
        },
        "notification": {
            "http": {
                "url": config["notification"]["url"]
            },
            "attrs": config["notification"]["attrs"],
            "metadata": config["notification"]["metadata"]
        },
        "throttling": 60
    }

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(config["orion-host"], json=subscription_payload, headers=headers)

    if response.status_code == 201:
        print("Subscription created successfully.")
    else:
        print(f"Failed to create subscription: {response.text}")


if __name__ == "__main__":
    """
    Check if the subscription is active and if not, subscribe to it
    """
    if not check_existing_subscriptions(config["orion_endpoint"], config["entities"], config["notification"]["url"]):
        subscribe()
