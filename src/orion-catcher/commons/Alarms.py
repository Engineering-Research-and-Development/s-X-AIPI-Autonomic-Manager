from typing import Union
import json
from RuleBasedEngine import ThresholdRule


class AmRuleBasedEngineAlarm:
    def __init__(self,
                 sol_name: str,
                 alarm_type: str,
                 cause: str,
                 threshold_rule: Union[ThresholdRule, None],
                 description: str):
        """

        :param sol_name: solution name which caused the alarm
        :param alarm_type: type of the alarm
        :param cause: cause of the alarm (it may be overwritten by rules)
        :param threshold_rule: optional rule that caused the alarm, if any
        """

        self.description = description
        self.solution = sol_name
        self.alarm_type = alarm_type
        self.cause = cause
        self.parameter = threshold_rule.parameter if threshold_rule is not None else None
        self.value = threshold_rule.value if threshold_rule is not None else None
        self.upper_threshold = threshold_rule.upper_threshold if threshold_rule is not None else None
        self.lower_threshold = threshold_rule.lower_threshold if threshold_rule is not None else None

    def set_rule(self, rule):
        """
        Adds a threshold rule to an alarm to specify what caused it

        :param rule: rule causing the alarm
        """
        if rule is not None:
            self.cause = rule.cause
            self.parameter = rule.parameter
            self.value = rule.value
            self.upper_threshold = rule.upper_threshold
            self.lower_threshold = rule.lower_threshold

    def get_json_string(self):
        """

        :return: string -> object as json stringed message
        """
        return json.dumps(self.__dict__)
