from .utils import THRESHOLD_HIGH, THRESHOLD_LOW, THRESHOLD_OK, STATUS_GOOD, STATUS_BAD, HISTORY_BAD, \
    HISTORY_GOOD, UNCONFIRMED, THRESHOLD_BROKEN
from dagster import op


@op
def discriminate_thresholds(lower_thresholds: list[float],
                            upper_thresholds: list[float],
                            values: list[float]
                            ) -> list[str]:
    """
    Discriminate thresholds based on the provided values.

    @param lower_thresholds: List of lower thresholds for attributes.
    @param upper_thresholds: List of upper thresholds for attributes.
    @param values: List of current values for attributes.

    @return: List of threshold discrimination results (THRESHOLD_HIGH, THRESHOLD_LOW, THRESHOLD_OK).
    """

    result_list = []
    try:
        if any(var is not len(values) for var in (len(lower_thresholds), len(upper_thresholds))):
            raise IndexError("Misconfiguration: list lengths are not equal")

        for attr_value, low, up in zip(values, lower_thresholds, upper_thresholds):
            if attr_value > up:
                result_list.append(THRESHOLD_HIGH)
            elif attr_value < low:
                result_list.append(THRESHOLD_LOW)
            else:
                result_list.append(THRESHOLD_OK)
    except IndexError as e:
        # TODO: decide if insert error alarm or not
        print(e)

    return result_list


@op
def merge_thresholds_and(first_group: list[str],
                         second_group: list[str],
                         ) -> list[str]:
    """
    Merge two groups of threshold results using logical AND operation.

    @param first_group: First group of threshold results.
    @param second_group: Second group of threshold results.

    @return: Merged list of threshold results where THRESHOLD_OK is preserved only if both groups are THRESHOLD_OK,
             otherwise THRESHOLD_BROKEN is set.
    """

    result_list = []
    try:
        if len(first_group) != len(second_group):
            raise IndexError("Misconfiguration: list lengths are not equal")

        for first_result, second_result in zip(first_group, second_group):
            if first_result == second_result and first_result == THRESHOLD_OK:
                result_list.append(THRESHOLD_OK)
            else:
                result_list.append(THRESHOLD_BROKEN)

    except IndexError as e:
        # TODO: decide if insert error alarm or not
        print(e)

    return result_list


@op
def analyze_historical_data(periods_in_state_list: list[float],
                            acknowledgement_status_list: list[str],
                            rules_status: list[str],
                            patience: int
                            ) -> tuple[list[str], list[str]]:
    """
    Analyze historical data and determine alarm conditions.

    @param periods_in_state_list: List of periods in which the previous status is held for each attribute.
    @param acknowledgement_status_list: List of acknowledgement status for each attribute.
    @param rules_status: List of rule status (e.g., THRESHOLD_OK, THRESHOLD_HIGH, THRESHOLD_LOW) for each attribute.
    @param patience: Number of periods to wait before raising an alarm.

    @return: Tuple containing alarm list and current status list.
    """

    alarm_list = []
    current_status_list = []

    for periods_in_state, acknowledgement_status, result in zip(periods_in_state_list, acknowledgement_status_list,
                                                                rules_status):

        current_status = STATUS_GOOD if result == THRESHOLD_OK else STATUS_BAD
        current_status_list.append(current_status)

        if periods_in_state > patience:
            if current_status not in acknowledgement_status or acknowledgement_status == UNCONFIRMED:
                if current_status == STATUS_BAD:
                    alarm_list.append(HISTORY_BAD)
                elif current_status == STATUS_GOOD:
                    alarm_list.append(HISTORY_GOOD)
                else:
                    alarm_list.append(THRESHOLD_OK)

    return alarm_list, current_status_list
