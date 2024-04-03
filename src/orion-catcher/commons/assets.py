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
) -> List[Union[ThresholdRule, AmRuleBasedEngineAlarm]]:
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
        for attr, low, up in zip(attrs, lower_thresholds, upper_thresholds):
            attr_value = values[attr]['value']['value']
            rule = ThresholdRule(attr, attr_value, up, low)
            if rule.is_broken: broken_rule_list.append(rule)
    except Exception as e:
        # TODO: decide if insert error alarm or not
        '''
        alarm = AmAlarm(solution_name, "AM Error", None, e, None, 
                                None, None)
        broken_rule_list.append(alarm.get_json_string())
        '''
        logger.error(e)

    return broken_rule_list

