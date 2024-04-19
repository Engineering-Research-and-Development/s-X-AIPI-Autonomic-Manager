from dagster import op
from logging import Logger

from utils import *

logger = Logger(__name__)


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


@op
def create_alarm_threshold(solution_name: str,
                           alarm_type: List[str],
                           attribute_names: List[str],
                           rule_results: List[str],
                           values: List[float],
                           lower_thresholds: List[float],
                           upper_thresholds: List[float]
                           ):
    """

    Args:
        solution_name: name of solution which triggers the alarm
        alarm_type: type or types of the caused alarm. Some solution may have multiple alarm types
        attribute_names: names of attributes from solution
        rule_results: results of RBE
        values: current values of attributes
        lower_thresholds: lower threshold of attributes
        upper_thresholds: upper threshold of attributes

    Returns: List[dict] list of alarms to send

    """

    list_results = []
    for attr, value, lt, ut, result in zip(attribute_names, values, lower_thresholds,
                                           upper_thresholds, rule_results):
        if result == THRESHOLD_OK:
            continue

        obj = {
            "solution": solution_name,
            "type": alarm_type,
            "attribute": attr,
            "cause": result,
            "deviation": value,
            "lowerThresh": lt,
            "upperThresh": ut
        }
        list_results.append(obj)

    return list_results


@op
def create_alarm_history(solution_name: str,
                         alarm_type: List[str],
                         attribute_names: List[str],
                         rule_results: List[str],
                         values: List[float],
                         periods: List[int],
                         acknowledged_status_list : List[str]
                         ):
    """

    Args:
        solution_name: name of solution which triggers the alarm
        alarm_type: type or types of the caused alarm. Some solution may have multiple alarm types
        attribute_names: names of attributes from solution
        rule_results: results of RBE
        values: current values of attributes
        periods: periods in which the current status changed
        acknowledged_status_list: List of acknowledge status

    Returns: List[dict] list of alarms to send

    """

    list_results = []
    for attr, value, period, ack, result in zip(attribute_names, values, periods,
                                           acknowledged_status_list, rule_results):
        if result == THRESHOLD_OK:
            continue

        obj = {
            "solution": solution_name,
            "type": alarm_type,
            "attribute": attr,
            "cause": result,
            "deviation": value,
            "periods": period,
            "last_acknowledged": ack
        }
        list_results.append(obj)

    return list_results


@op
def create_alarm_payloads(values: List[dict], context: str):
    """
    Takes a list of alarm results and returns a payload for OCB
    Args:
        values: list of alarm value dictionaries
        context: inject context of alarm entity

    Returns: list of payloads

    """
    payloads = []

    for val in values:
        obj = update_data([val], ["AM_Generated_Alarm"], context)
        payloads.append(obj)
    return payloads
