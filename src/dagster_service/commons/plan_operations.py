from dagster import op
from logging import Logger

from utils import *

logger = Logger(__name__)


@op
def update_historical_data(current_status: List(str),
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


@op
def update_historical_data(current_status_list: List(str),
                           periods_in_state_list: List[float],
                           acknowledgement_status_list: List[str],
                           previous_status_list: List[str],
                           attribute_names: List[str],
                           context: str,
                           ) -> dict:
    """
        :param current_status_list: current status of a monitored system for each attribute
        :param context: context for NGSI-LD entity to update
        :param periods_in_state_list: periods in which current status is hold
        :param acknowledgement_status_list: current acknowledgement status from HITL
        :param previous_status_list: previous status to confront
        :param attribute_names: base attribute name to "develop" into history parameters
        """

    try:
        if (len(attribute_names) != len(periods_in_state_list) or
                len(attribute_names) != len(acknowledgement_status_list) or
            len(attribute_names) != len(previous_status_list) or
                len(attribute_names) != len(current_status_list)):
            raise IndexError("List values are not the same")
    except IndexError as e:
        logger.error(e)

    payload = {}
    for idx, attribute_name in enumerate(attribute_names):

        update_names = build_historical_data_attribute_names(attribute_name)
        current_status = current_status_list[idx]
        previous_status = previous_status_list[idx]
        acknowledgement_status = acknowledgement_status_list[idx]
        periods_in_state = periods_in_state_list[idx]

        if current_status != previous_status:
            periods_in_state = 1
            acknowledgement_status = UNCONFIRMED
        else:
            periods_in_state += 1

        new_values = [periods_in_state, acknowledgement_status, current_status]
        payload = update_data(new_values, update_names, context)

    return payload



