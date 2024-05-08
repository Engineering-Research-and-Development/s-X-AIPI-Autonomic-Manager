from dagster import op, OpExecutionContext
import requests
import json
from kafka import KafkaProducer


@op
def patch_orion(context: OpExecutionContext, url: str, payload):
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
        context.log.error(e)


@op
def produce_kafka(producer: KafkaProducer,
                  topic: str,
                  messages: list[dict]):
    """
    :param producer: Instance of Kafka Broker
    :param topic: Topic in which to write message
    :param messages: list of dict message to be written in Kafka topic
    """
    if type(messages) is not list:
        producer.send(topic, json.dumps(messages))
        return

    for message in messages:
        producer.send(topic, json.dumps(message))


@op
def produce_orion_multi_message(context: OpExecutionContext,
                                url: str,
                                messages: list[dict]):
    """
    :param url: url of alarm entity on OCB
    :param messages: list of dict message to be written in Kafka topic
    """
    url = url + "/attrs/"
    headers = {"Content-Type": "application/ld+json"}

    for message in messages:
        try:
            requests.post(url, headers=headers, data=json.dumps(message))
        except requests.exceptions.RequestException as e:
            context.log.error(e)
