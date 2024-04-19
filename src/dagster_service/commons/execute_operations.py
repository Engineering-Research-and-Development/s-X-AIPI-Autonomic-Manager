from dagster import op
import requests
import json
from logging import Logger
from kafka import KafkaProducer
from typing import List

logger = Logger(__name__)


@op
def patch_orion(url: str, payload):
    """

    :param url: url of the historical entity to update
    :param payload: payload to pass for update
    :return:
    """
    url = url + "/attrs/"
    headers = {"Content-Type": "application/ld+json"}

    try:
        requests.post(url, headers=headers, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        logger.error(e)


@op
def produce_kafka(producer: KafkaProducer, topic: str, messages: List[dict]):
    """
    :param producer: Instance of Kafka Broker
    :param topic: Topic in which to write message
    :param messages: List of dict message to be written in Kafka topic
    """
    for message in messages:
        producer.send(topic, json.dumps(message))


@op
def produce_orion_multi_message(url: str, messages: List[dict]):
    """
    :param url: url of alarm entity on OCB
    :param messages: List of dict message to be written in Kafka topic
    """
    url = url + "/attrs/"
    headers = {"Content-Type": "application/ld+json"}

    for message in messages:
        try:
            requests.post(url, headers=headers, data=json.dumps(message))
        except requests.exceptions.RequestException as e:
            logger.error(e)
