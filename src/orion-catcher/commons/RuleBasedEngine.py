import numpy as np


class ThresholdRule:
    def __init__(self, name: str, value: float, up: float, low: float):
        """
        Represent a Rule-Based-Engine Threshold rule

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

    def __evaluate_cause(self):
        if self.value > self.upper_threshold:
            self.cause = "upper threshold"
            self.is_broken = True
        elif self.value < self.lower_threshold:
            self.cause = "lower threshold"
            self.is_broken = True

