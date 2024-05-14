from commons.utils import THRESHOLD_HIGH, THRESHOLD_LOW, THRESHOLD_OK, STATUS_GOOD, STATUS_BAD, HISTORY_BAD, \
    HISTORY_GOOD, UNCONFIRMED, THRESHOLD_BROKEN
from dagster import op


@op
def discriminate_thresholds(lower_thresholds: list[float],
                            upper_thresholds: list[float],
                            values: list[float]
                            ) -> list[str]:
    """
    Function to discriminate if values are in threshold

    :param values: (list[float]) values from OCB entity to be checked
    :param lower_thresholds: (list[float]) list of ordered lower thresholds to be respected
    :param upper_thresholds: (list[float]) list of ordered upper thresholds to be respected

    :return result_list: (list[str]) list of results from the previous analysis

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
    Checks two groups of threshold results applying a logical AND

    @param first_group: first set of results from threhshold
    @param second_group: second set of results from threshold

    :return result_list: (list[str]) list of results from the previous analysis


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
    Confront current values versus previous value to check for alarm generation

    @param acknowledgement_status_list: list of values for acknowledgement status for each attribute
    @param periods_in_state_list: list of values for periods_in_state status for each attribute
    @param rules_status: results from threshold analysis
    @param patience: number of periods for status
    @return: list(str) It might return "No Alarm", "Good Change", "Bad Change"
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