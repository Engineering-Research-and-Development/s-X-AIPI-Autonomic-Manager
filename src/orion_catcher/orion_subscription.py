import requests
import logging
import json


def check_existing_subscriptions(orion_endpoint: str, entity_id: str, callback_url: str, attrs: list[str]) -> bool:
    """
    @param orion_endpoint: The endpoint of the Orion Context Broker.
    @param entity_id: The id of the entity to check for subscription.
    @param callback_url: The callback URL to check for subscription.
    @param attrs: attributes to check in subscriptions

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
    response = requests.get(orion_endpoint, headers=headers)

    if response.status_code == 200:
        subscriptions = response.json()
        for subscription in subscriptions:
            if (subscription.get('entities', [{}])[0].get('id') == entity_id
                    and subscription.get('notification', {}).get('endpoint', {}).get('uri') == callback_url):

                if len(attrs) > 0 and set(subscription.get('notification', {}).get('attributes', [])) == set(attrs):
                    return True
                elif len(attrs) == 0 and len(subscription.get('notification', {}).get('attributes', [])) == 0:
                    return True
        return False
    else:
        logging.error(f"Failed to retrieve subscriptions. Status code: {response.status_code}")
        logging.debug(f"Response: {response.text}")
        return False


def subscribe(entity_id: str, entity_type: str, attrs: list[str], notification_url: str, condition_attrs: list[str],
              orion_host: str, context: str, throttling: int = 60) -> None:
    """
    Create a subscription in Orion Context Broker for a given entity.

    @param entity_id: The id of the entity to subscribe to.
    @param entity_type: The type of the entity to subscribe to
    @param attrs: The attributes of the entity to be included in the subscription notification.
    @param notification_url: The URL where notifications should be sent.
    @param condition_attrs: The attributes to be included in the conditions.
    @param orion_host: The host URL of the Orion Context Broker to post new subscriptions.
    @param context: The Context for NGSI-LD subscription
    @param throttling: The throttling period for the subscription (default is 60 seconds).

    @return: None
    """
    subscription_name = f"{entity_id} subscription to Dagster"
    subscription_payload = {
        "@context": context,
        "description": subscription_name,
        "type": "Subscription",
        "entities": [{"id": entity_id, "type": entity_type}],
        "notification": {
            "endpoint": {
                "uri": notification_url,
                "accept": "application/json"
            },
            "format": "normalized",
        },
        "throttling": throttling,
        "expires": "2099-01-01T14:00:00.00Z"
    }

    if len(attrs) > 0:
        subscription_payload["notification"]["attributes"] = attrs

    if len(condition_attrs) > 0:
        subscription_payload["watchedAttributes"] = condition_attrs

    headers = {
        "Content-Type": "application/ld+json",
    }
    response = requests.post(orion_host, data=json.dumps(subscription_payload), headers=headers)
    print(response.status_code)
    print(json.dumps(subscription_payload))

    if response.status_code == 201:
        logging.info("Subscription created successfully.")
    else:
        logging.error(f"Failed to create subscription: {response.text}")
