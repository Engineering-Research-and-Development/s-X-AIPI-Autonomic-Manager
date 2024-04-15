from dagster import op
import requests
import json
from logging import Logger
from kafka import KafkaProducer

logger = Logger(__name__)


@op
def patch_orion(historical_source_url, payload):
    """

    :param historical_source_url: url of the historical entity to update
    :param payload: payload to pass for update
    :return:
    """
    url = historical_source_url + "/attrs/"
    headers = {"Content-Type": "application/ld+json"}

    try:
        requests.post(url, headers=headers, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@op
def produce_kafka(producer: KafkaProducer, topic: str, message: str):
    """
    :param producer: Instance of Kafka Broker
    :param topic: Topic in which to write message
    :param message: stringed message to be written in Kafka topic
    """
    producer.send(topic, message.encode())


