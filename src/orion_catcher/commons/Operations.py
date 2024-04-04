from dagster import graph_asset, graph_multi_asset, op
from typing import List, Union
from logging import Logger

from RuleBasedEngine import ThresholdRule

logger = Logger(__name__)


@op
def get_previous_state(
        entity_url: str,
        attribute_name: str
) -> dict:
    pass


@op
def discriminate_thresholds(
        solution_name: str,
        values: dict,
        lower_thresholds: List[float],
        upper_thresholds: List[float],
        attrs: List[str]
) -> List[ThresholdRule]:
    """
    :param solution_name: solution name
    :param values: dictionary of values from OCB
    :param lower_thresholds: list of ordered lower thresholds to be respected
    :param upper_thresholds: list of ordered upper thresholds to be respected
    :param attrs: list of attributes to confront with thresholds

    :return broken_rule_list: list of dictionary containing information about attributes which broke the thresholds
    """

    if any(var is not len(attrs) for var in (len(lower_thresholds), len(upper_thresholds))):
        raise IndexError("Misconfiguration: list lengths are not equal")

    broken_rule_list = []
    try:
        for attr, low, up in zip(attrs, lower_thresholds, upper_thresholds):
            try:
                attr_value = values[attr]['value']['value']
            except KeyError:
                logger.error("Unable to find key in subscription payload")
                continue
            rule = ThresholdRule(attr, attr_value, up, low)
            if rule.is_broken:
                broken_rule_list.append(rule)
    except IndexError as e:
        # TODO: decide if insert error alarm or not
        # alarm = AmRuleBasedEngineAlarm(solution_name, "AM Error", "Generic", None, str(e))
        logger.error(e)

    return broken_rule_list

