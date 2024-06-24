from dagster import op
import requests
import json
from kafka import KafkaProducer


@op
def patch_orion(url: str, payload):
    """
    Patch the Orion Context Broker with the provided payload for updating a historical entity.

    @param url: URL of the historical entity to update.
    @param payload: Payload to pass for update.

    @return: None
    """
    url = url + "/attrs/"
    headers = {"Content-Type": "application/ld+json"}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(response.text, response.status_code)
    except requests.exceptions.RequestException as e:
        print("An error occurred while posting new data on Orion:", e)


@op
def produce_kafka(producer: KafkaProducer,
                  topic: str,
                  messages: list[dict]):
    """
    Produce messages to a Kafka topic using the provided KafkaProducer instance.

    @param producer: KafkaProducer instance used for producing messages.
    @param topic: The Kafka topic to which messages will be sent.
    @param messages: A list of dictionaries representing messages to be sent.

    @return: None
    """
    for message in messages:
        producer.send(topic, json.dumps(message).encode('utf-8'))


@op
def produce_orion_multi_message(url: str,
                                messages: list[dict]):
    """
    Produce multiple messages to an Orion Context Broker for updating attributes.

    @param url: URL of the historical entity to update.
    @param messages: A list of dictionaries representing messages to be sent.

    @return: None
    """

    url = url + "/attrs/"
    headers = {"Content-Type": "application/ld+json"}

    for message in messages:
        print(json.dumps(message))
        try:
            response = requests.post(url, headers=headers, data=json.dumps(message))
            print(response.text, response.status_code)
        except requests.exceptions.RequestException as e:
            print("An error occurred while posting multiple new data on Orion:", e)
