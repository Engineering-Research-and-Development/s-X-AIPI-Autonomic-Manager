import requests
import logging


def check_existing_subscriptions(orion_endpoint: str, entity_type: str, callback_url: str) -> bool:
    """
    @param orion_endpoint: The endpoint of the Orion Context Broker.
    @param entity_type: The type of the entity to check for subscription.
    @param callback_url: The callback URL to check for subscription.

    @return:
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
    Create a subscription in Orion Context Broker for a given entity.

    @param entity: The type of the entity to subscribe to.
    @param attrs: The attributes of the entity to be included in the subscription.
    @param notification_url: The URL where notifications should be sent.
    @param notification_attrs: The attributes to be included in the notification.
    @param notification_metadata: The metadata to be included in the notification.
    @param orion_host: The host URL of the Orion Context Broker.
    @param throttling: The throttling period for the subscription (default is 60 seconds).

    @return: None
    """
    subscription_name = f"{entity} subscription"
    subscription_payload = {
        "description": subscription_name,
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
