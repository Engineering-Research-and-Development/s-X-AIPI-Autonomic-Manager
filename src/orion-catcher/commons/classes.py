from typing import Union, Type
import numpy as np
import json


class ThresholdRule:
    def __init__(self, name: str, value: float, up: float, low: float):
        """
        Represent a Rule-Based-Engine Threshold rule

        :param name: name of parameter causing the broken rule
        :param value: current value of parameter causing the broken rule
        :param up: upper threshold value
        :param low: lower threshold value
        :param cause: cause of the broken rule: upper, lower threshold
        """
        self.parameter = name
        self.value = value
        self.upper_threshold = up if up is not None else np.infty
        self.lower_threshold = low if low is not None else -np.infty
        self.is_broken = False
        self.__evaluate_cause()

    def __evaluate_cause(self):
        if self.value > self.upper_threshold:
            self.cause = "upper threshold"
            self.is_broken = True
        elif self.value < self.lower_threshold:
            self.cause = "lower threshold"
            self.is_broken = True



class AmRuleBasedEngineAlarm:
    def __init__(self,
                 sol_name: str,
                 alarm_type: str,
                 cause: str,
                 rule: Union[ThresholdRule, None]):
        """

        :param sol_name: solution name which caused the alarm
        :param alarm_type: type of the alarm
        :param cause: cause of the alarm (it may be overwritten by rules)
        :param rule: optional rule that caused the alarm, if any
        """

        self.solution = sol_name
        self.alarm_type = alarm_type
        self.cause = cause
        self.__set_rule(rule)

    def __set_rule(self, rule):
        """
        Adds a threshold rule to an alarm to specify what caused it

        :param rule: rule causing the alarm
        """
        self.parameter = rule.parameter if rule is not None else None
        self.value = rule.value if rule is not None else None
        self.upper_threshold = rule.upper_threshold if rule is not None else None
        self.lower_threshold = rule.lower_threshold if rule is not None else None

        if rule is not None: self.cause = rule.cause

    def get_json_string(self):
        """

        :return: string -> object as json stringed message
        """
        return json.dumps(self.__dict__)
