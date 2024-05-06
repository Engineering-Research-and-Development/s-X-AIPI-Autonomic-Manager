from dagster import op, OpExecutionContext
import numpy as np
from logging import Logger

from .utils import *

logger = Logger(__name__)


@op
def get_threshold_values_from_entity(context: OpExecutionContext,
                                     data_source: dict,
                                     lower_names: list[str],
                                     upper_names: list[str]
                                     ) -> tuple[list[float], list[float]]:
    """
    Get data from received notification, returning valuable information
    @param upper_names: names of attributes containing upper thresholds
    @param lower_names: names of attributes containing lower thresholds
    @param data_source: dictionary containing data payload from notification
    @return: relevant attribute values
    """
    try:
        upper_thresholds = [data_source[attribute]["value"]["value"] for attribute in upper_names]
        lower_thresholds = [data_source[attribute]["value"]["value"] for attribute in lower_names]
        return lower_thresholds, upper_thresholds
    except KeyError as e:
        print(e)
        return [], []


@op
def get_threshold_from_pct_range(context: OpExecutionContext,
                                 values: list[float],
                                 pct_list: list[float]
                                 ) -> tuple[list[float], list[float]]:
    """

    @param values: list of values from which to compute percentage
    @param pct_list: list of percentages to use for computing thresholds
    @return: list of upper and lower thresholds
    """
    lowers = []
    uppers = []
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


@op
def retrieve_values_from_historical_data(context: OpExecutionContext,
                                         historical_data: dict,
                                         attribute_names: list[str],
                                         ) -> tuple[list[float], list[str], list[str], str]:
    """
    Function to gather values for historical data given retrieved payload

    @param historical_data: historical entity data
    @param attribute_names: attributes to search in the historical entity
    @return: list of values (periods_in_state, acknowledgement_status, previous_state) and its context value
    """
    periods_list = []
    ack_list = []
    previous_list = []
    try:
        context = historical_data["@context"]
        for attribute_name in attribute_names:
            names = [n for n in build_historical_data_attribute_names(attribute_name)]
            periods, ack, previous = pick_historical_data_values(names, historical_data)
            periods_list.append(periods)
            ack_list.append(ack)
            previous_list.append(previous)
        return periods_list, ack_list, previous_list, context

    except KeyError as e:
        logger.error(e)
        return [], [], [], "None"
