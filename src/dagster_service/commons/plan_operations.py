from dagster import op
from logging import Logger
import requests
import json

from utils import *

logger = Logger(__name__)


@op
def update_historical_data(current_status: str,
                           context: str,
                           periods_in_state: int,
                           acknowledgement_status: str,
                           previous_status: str,
                           attribute_name: str,
                           ):
    """
        :param current_status: current status of a monitored system
        :param context: context for NGSI-LD entity to update
        :param periods_in_state: periods in which current status is hold
        :param acknowledgement_status: current acknowledgement status from HITL
        :param previous_status: previous status to confront
        :param attribute_name: base attribute name to "develop" into history parameters
        """

    update_names = build_historical_data_attribute_names(attribute_name)

    if current_status != previous_status:
        periods_in_state = 1
        acknowledgement_status = UNCONFIRMED
    else:
        periods_in_state += 1

    new_values = [periods_in_state, acknowledgement_status, current_status]
    payload = update_data(new_values, update_names, context)
    return payload


