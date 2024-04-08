import requests
import logging


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
        logging.error(f"Failed to retrieve subscriptions. Status code: {response.status_code}")
        logging.debug(f"Response: {response.text}")
        return False


def subscribe(entity: str, attrs: str, notification_url: str, notification_attrs: str, notification_metadata: str,
              orion_host: str, throttling: int = 60) -> None:
    """
    Perform the subscription to the entity using the parameters in the 'config' yaml file

    Parameters:
        entity: the entity to subscribe

        attrs: the condition attributes

        notification_url: the URL where to get the notifications

        notification_attrs: the attributes of the notification

        notification_metadata: the notification metadata

        orion_host: the Orion endpoint

        throttling: the throttling timing, default 60
    """
    subscription_payload = {
        "description": "Pharma subscription",
        "subject": {
            "entities": [{"idPattern": ".*", "type": entity}],
            "condition": {
                "attrs": attrs
            }
        },
        "notification": {
            "http": {
                "url": notification_url
            },
            "attrs": notification_attrs,
            "metadata": notification_metadata
        },
        "throttling": throttling
    }

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(orion_host, json=subscription_payload, headers=headers)

    if response.status_code == 201:
        logging.info("Subscription created successfully.")
    else:
        logging.error(f"Failed to create subscription: {response.text}")
