from dagster import op
import requests
import json
from logging import Logger

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
