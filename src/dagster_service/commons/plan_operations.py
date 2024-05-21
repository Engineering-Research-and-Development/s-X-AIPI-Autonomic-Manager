from .utils import build_historical_data_attribute_names, UNCONFIRMED, update_data, THRESHOLD_OK
from dagster import op


@op
def update_historical_data(current_status_list: list[str],
                           periods_in_state_list: list[float],
                           acknowledgement_status_list: list[str],
                           previous_status_list: list[str],
                           old_value_list: list[float],
                           attribute_names: list[str],
                           payload_context: str,
                           ) -> dict:
    """
    Updates the historical data of a monitored system's attributes based on their current and previous statuses,
    periods in which the current status is held, and acknowledgment status. This function constructs a payload
    to update the NGSI-LD entity context.

    @param current_status_list: List of current statuses of a monitored system for each attribute.
    @param periods_in_state_list: List of periods in which the current status is held for each attribute.
    @param acknowledgement_status_list: List of current acknowledgment statuses from Human-In-The-Loop (HITL) for each attribute.
    @param previous_status_list: List of previous statuses to compare against the current statuses for each attribute.
    @param old_value_list: List of new values (presumably old values from a previous state) for each attribute.
    @param attribute_names: List of base attribute names to develop into history parameters.
    @param payload_context: Context for NGSI-LD entity to update, typically a JSON-LD payload context.

    @return: A dictionary representing the payload for updating the NGSI-LD entity context.
    """

    try:
        if (len(attribute_names) != len(periods_in_state_list) or
                len(attribute_names) != len(acknowledgement_status_list) or
                len(attribute_names) != len(previous_status_list) or
                len(attribute_names) != len(current_status_list) or
                len(attribute_names) != len(old_value_list)):
            raise IndexError("list values are not the same")
    except IndexError as e:
        print(e)

    payload = {}
    for idx, attribute_name in enumerate(attribute_names):

        update_names = build_historical_data_attribute_names(attribute_name)
        current_status = current_status_list[idx]
        previous_status = previous_status_list[idx]
        acknowledgement_status = acknowledgement_status_list[idx]
        periods_in_state = periods_in_state_list[idx]
        old_value = old_value_list[idx]

        if current_status != previous_status:
            periods_in_state = 1
            acknowledgement_status = UNCONFIRMED
        else:
            periods_in_state += 1

        new_values = [periods_in_state, acknowledgement_status, current_status, old_value]
        payload = update_data(new_values, update_names, payload_context)

    return payload


@op
def create_alarm_threshold(solution_name: str,
                           alarm_type: str,
                           attribute_names: list[str],
                           rule_results: list[str],
                           values: list[float],
                           lower_thresholds: list[float],
                           upper_thresholds: list[float]
                           ) -> list[dict]:
    """
    Generate a list of alarms based on the provided thresholds and rule results for each attribute.


    @param solution_name: The name of the solution which triggers the alarm.
    @param alarm_type: The type of the caused alarm.
    @param attribute_names: The names of the attributes from the solution.
    @param rule_results: The results of the Rule-Based Engine (RBE) for each attribute.
    @param values: The current values of the attributes.
    @param lower_thresholds: The lower thresholds for the attributes.
    @param upper_thresholds: The upper thresholds for the attributes.

    @return: A list of dictionaries representing the alarms to be sent.

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
                         alarm_type: list[str],
                         attribute_names: list[str],
                         rule_results: list[str],
                         periods: list[int],
                         acknowledged_status_list: list[str]
                         ) -> list[dict]:
    """
    Generate a list of historical alarms based on the provided rule results and other parameters.

    @param solution_name: The name of the solution which triggers the alarm.
    @param alarm_type: The types of the caused alarm.
    @param attribute_names: The names of the attributes from the solution.
    @param rule_results: The results of the Rule-Based Engine (RBE) for each attribute.
    @param periods: The periods in which the current status is held for each attribute.
    @param acknowledged_status_list: The current acknowledgement status for each attribute.

    @return: A list of dictionaries representing the historical alarms.
    """

    list_results = []
    for attr, period, ack, result in zip(attribute_names, periods,
                                         acknowledged_status_list, rule_results):
        if result == THRESHOLD_OK:
            continue

        obj = {
            "solution": solution_name,
            "type": alarm_type,
            "attribute": attr,
            "cause": result,
            "periods": period,
            "last_acknowledged": ack
        }
        list_results.append(obj)

    return list_results
