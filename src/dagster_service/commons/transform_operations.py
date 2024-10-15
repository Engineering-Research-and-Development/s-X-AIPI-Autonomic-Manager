from dagster import op
import numpy as np

from .utils import update_data, build_historical_data_attribute_names, pick_historical_data_values, get_value_from_data


@op
def expand_threshold(value: list[float], number: int) -> list[float]:
    """
    Expand a threshold value by repeating it a certain number of times.

    @param value: Threshold value to be expanded.
    @param number: Number of times the threshold should be repeated.

    @return: List of threshold values.
    """

    return value * number


@op
def get_threshold_values_from_entity(data_source: dict,
                                     lower_names: list[str],
                                     upper_names: list[str]
                                     ) -> tuple[list[float], list[float]]:
    """
    Retrieve lower and upper threshold values from the entity data source.

    @param data_source: Dictionary containing data payload from the entity.
    @param lower_names: List of attribute names representing lower thresholds.
    @param upper_names: List of attribute names representing upper thresholds.

    @return: Tuple containing lists of lower and upper threshold values.
    """

    try:
        labels = [get_value_from_data(data_source[upper_name]) for upper_name in upper_names]
        upper_thresholds = [float(data_source[attribute]["value"][labels[idx]]) for idx, attribute in enumerate(upper_names)]
        lower_thresholds = [float(data_source[attribute]["value"][labels[idx]]) for idx, attribute in enumerate(lower_names)]
        return lower_thresholds, upper_thresholds
    except KeyError as e:
        print("An error occurred while transforming data: get_threshold_values_from_entity failed", e)
        return [], []


@op
def get_threshold_from_pct_range(values: list[float],
                                 pct_list: list[float]
                                 ) -> tuple[list[float], list[float]]:
    """
    Calculate threshold ranges based on percentage change from the provided values.

    @param values: List of values to calculate thresholds from.
    @param pct_list: List of percentages representing the range of threshold values.

    @return: Tuple containing lists of lower and upper threshold values.
    """

    lowers = []
    uppers = []
    try:
        for value, pct in zip(values, pct_list):
            if pct < 0 or pct > 100:
                raise ValueError("Misconfiguration: Percentage value out of range")
            pct_change = pct / 100
            val_range = np.abs(value) * pct_change
            up = value + val_range
            low = value - val_range
            lowers.append(low)
            uppers.append(up)

        return lowers, uppers
    except ValueError as e:
        print("An error occurred while transforming data: get_threshold_from_pct_range failed", e)
        return [], []


@op
def retrieve_values_from_historical_data(historical_data: dict,
                                         attribute_names: list[str],
                                         ) -> tuple[list[int], list[str], list[str], list[float], str]:
    """
    Retrieve values from historical data for the given attribute names.

    @param historical_data: Dictionary containing historical data.
    @param attribute_names: List of attribute names for which values are to be retrieved.

    @return: Tuple containing lists of periods, acknowledgment statuses, previous statuses, old values, and historical context.
    """

    periods_list = []
    ack_list = []
    previous_list = []
    old_value_list = []
    try:
        historical_context = historical_data["@context"]
        for attribute_name in attribute_names:
            names = [n for n in build_historical_data_attribute_names(attribute_name)]
            periods, ack, previous, old_value = pick_historical_data_values(names, historical_data)
            periods_list.append(periods)
            ack_list.append(ack)
            previous_list.append(previous)
            old_value_list.append(float(old_value))
        return periods_list, ack_list, previous_list, old_value_list, historical_context

    except KeyError as e:
        print("An error occurred while transforming data: retrieve_values_from_historical_data failed", e)
        return [], [], [], [], "None"


@op
def create_alarm_payloads(values: list[dict],
                          payload_context: str,
                          metadata = None) -> list[dict]:
    """
    Create alarm payloads based on the provided values and payload context.

    @param values: List of dictionaries representing alarm values.
    @param payload_context: Context for NGSI-LD entity to update.
    @param metadata (optional): if present, list of additional data to add payload

    @return: List of dictionaries representing the alarm payloads.
    """

    payloads = []

    for idx, val in enumerate(values):
        obj = update_data([val], ["AM_Generated_Alarm"], payload_context)
        if metadata:
            obj["AM_Generated_Alarm"]["metadata"] = metadata[idx]

        payloads.append(obj)
    return payloads
