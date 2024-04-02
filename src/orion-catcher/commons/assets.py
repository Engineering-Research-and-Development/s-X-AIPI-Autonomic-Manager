from dagster import graph_asset, graph_multi_asset, op
from typing import List, Union
from logging import Logger

import requests

from classes import *

logger = Logger(__name__)


@op
def get_previous_state(
        entity_url: str,
) -> dict:
    pass


@op
def discriminate_thresholds(
        solution_name: str,
        values: dict,
        lower_thresholds: List[float],
        upper_thresholds: List[float],
        attrs: List[str]
) -> List[Union[BrokenRule, AmAlarm]]:
    """
    :param solution_name: solution name
    :param values: dictionary of values from OCB
    :param lower_thresholds: list of ordered lower thresholds to be respected
    :param upper_thresholds: list of ordered upper thresholds to be respected
    :param attrs: list of attributes to confront with thresholds

    :return broken_rule_list: list of dictionary containing information about attributes which broke the thresholds
    """

    if any(var is not len(attrs) for var in (len(lower_thresholds), len(upper_thresholds))):
        raise Exception("Misconfiguration: list lengths are not equal")

    broken_rule_list = []
    try:
        for index, attr in enumerate(attrs):
            lower_threshold = -99999999 if lower_thresholds[index] is not None else lower_thresholds[index]
            upper_threshold = 99999999 if upper_thresholds[index] is not None else upper_thresholds[index]
            attr_value = values[attr]['value']['value']
            cause = None
            if attr_value < lower_threshold:
                cause = "lower threshold"
            elif attr_value > upper_threshold:
                cause = "upper threshold"
            if cause:
                broken_rule = BrokenRule(attr, attr_value, upper_threshold, lower_threshold, cause)
                broken_rule_list.append(broken_rule)
    except Exception as e:
        # TODO: decide if insert error alarm or not
        '''
        alarm = AmAlarm(solution_name, "AM Error", None, e, None, 
                                None, None)
        broken_rule_list.append(alarm.get_json_string())
        '''
        logger.error(e)

    return broken_rule_list

