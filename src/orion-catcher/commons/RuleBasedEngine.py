import numpy as np
from typing import Union


class ThresholdRule:
    def __init__(self, name: str, value: float, up: float, low: float):
        """
        Represent a Rule-Based-Engine Threshold base rule

        :param name: name of parameter causing the broken rule
        :param value: current value of parameter causing the broken rule
        :param up: upper threshold value
        :param low: lower threshold value
        """
        self.parameter = name
        self.value = value
        self.upper_threshold = up if up is not None else np.infty
        self.lower_threshold = low if low is not None else -np.infty
        self.is_broken = False
        self.__evaluate_cause()

    @classmethod
    def from_percentage_range(cls, name: str, value: float, pct: float):
        """

        :param name: (str) name of the attribute
        :param value: (float) value of the attribute
        :param pct: (float) percentage number (from 0 to 100) of displacement from value
        :return: (ThresholdRule) alternative instance of class
        """
        if pct < 0 or pct > 100:
            raise ValueError("Misconfiguration: Percentage value out of range")
        pct_change = pct / 100
        val_range = np.abs(value) * pct_change
        up = value + val_range
        low = value - val_range
        return cls(name, value, up, low)

    @classmethod
    def from_other_attributes(cls, name: str, value: str, upper_attribute_url: Union[None, str],
                              lower_attribute_url: Union[None, str]):
        # TODO: Fill the class with requests from Orion to check other attributes (if todo)
        pass

    def __evaluate_cause(self):
        if self.value > self.upper_threshold:
            self.cause = "upper threshold"
            self.is_broken = True
        elif self.value < self.lower_threshold:
            self.cause = "lower threshold"
            self.is_broken = True
