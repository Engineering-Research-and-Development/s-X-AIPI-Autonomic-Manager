from dagster import op
from typing import List
from logging import Logger

from utils import  *

logger = Logger(__name__)




@op
def discriminate_thresholds(
        lower_thresholds: List[float],
        upper_thresholds: List[float],
        values: List[float]
) -> List[str]:
    """
    :param values: (List[float]) values from OCB entity to be checked
    :param lower_thresholds: (List[float]) list of ordered lower thresholds to be respected
    :param upper_thresholds: (List[float]) list of ordered upper thresholds to be respected

    :return result_list: (List[str]) list of results from the previous analysis
    """

    if any(var is not len(values) for var in (len(lower_thresholds), len(upper_thresholds))):
        raise IndexError("Misconfiguration: list lengths are not equal")

    result_list = []
    try:
        for attr_value, low, up in zip(values, lower_thresholds, upper_thresholds):
            if attr_value > up:
                result_list.append(THRESHOLD_HIGH)
            elif attr_value < low:
                result_list.append(THRESHOLD_LOW)
            else:
                result_list.append(THRESHOLD_OK)
    except IndexError as e:
        # TODO: decide if insert error alarm or not
        # alarm = AmRuleBasedEngineAlarm(solution_name, "AM Error", "Generic", None, str(e))
        logger.error(e)

    return result_list


@op
def analyze_status(
        rules_results: List[str],
        check_rules: str = "all"
):
    """
    Function that analyze a set of rules to understand the current status.

    :param rules_results: List of results from rules analysis from which to understand if status is good or bad
    :param check_rules:
        "any" to check at least one met condition
        "all" to check if all conditions were met
    :return: (str) current status based on list of rule
    """
    if check_rules == "any":
        flag = any(broken for broken in rules_results if broken != THRESHOLD_OK)
    elif check_rules == "all":
        flag = all(not broken for broken in rules_results if broken != THRESHOLD_OK)
    else:
        raise ValueError("There was an error on checking rules")

    current_status = STATUS_BAD
    if flag:
        current_status = STATUS_GOOD

    return current_status


@op
def analyze_historical_data(current_status: str,
                            periods_in_state: int,
                            acknowledgement_status: str,
                            patience: int):
    """

        :param current_status: variable to understand current status value
        :param patience: maximum number of periods to wait before triggering alarms
        :param periods_in_state: periods in which current status is hold
        :param acknowledgement_status: current acknowledgement status from HITL

        :return:
            (str) It might return "No Alarm", "Good Change", "Bad Change"
        """

    if periods_in_state > patience:
        if current_status not in acknowledgement_status or acknowledgement_status == UNCONFIRMED:
            if current_status == STATUS_BAD:
                return STATUS_BAD + " Change"
            elif current_status == STATUS_GOOD:
                return STATUS_GOOD + " Change"
    return "No Alarm"


