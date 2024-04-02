from typing import Union, Type
import json


class BrokenRule:
    def __init__(self, name: str, value: float, up: float, low: float, cause: str):
        """

        :param name: name of parameter causing the broken rule
        :param value: current value of parameter causing the broken rule
        :param up: upper threshold value
        :param low: lower threshold value
        :param cause: cause of the broken rule: upper, lower threshold
        """
        self.parameter = name
        self.value = value
        self.upper_threshold = up,
        self.lower_threshold = low
        self.cause = cause


class AmAlarm:
    def __init__(self,
                 sol_name: str,
                 alarm_type: str,
                 cause: str,
                 rule: Union[BrokenRule, None]):
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

        :param rule: rule causing the alarm
        """
        if rule:
            self.parameter = rule.parameter
            self.value = rule.value
            self.upper_threshold = rule.upper_threshold
            self.lower_threshold = rule.lower_threshold
            self.cause = rule.cause
        else:
            self.parameter = None
            self.value = None
            self.upper_threshold = None
            self.lower_threshold = None

    def get_json_string(self):
        """

        :return: string -> object as json stringed message
        """
        return json.dumps(self.__dict__)
