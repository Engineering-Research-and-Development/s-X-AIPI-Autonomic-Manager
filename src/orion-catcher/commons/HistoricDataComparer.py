from typing import Union, List
import json
from datetime import datetime
import requests
from RuleBasedEngine import ThresholdRule

UNCONFIRMED = "Unconfirmed"
BAD = "Bad"
GOOD = "Good"


def add_param_to_body(body, param_name, param_value, now):
    if param_value is not None:
        body[param_name] = {}
        body[param_name]["type"] = "Property"
        body[param_name]["value"] = {}
        body[param_name]["value"]["value"] = param_value
        body[param_name]["value"]["dateUpdated"] = now

    return body


class HistoricDataComparer:
    """
    This class is meant to check in the historic archive (or a storage entity in Orion)
    for a particular attribute and, based on a list of thresholds, check if status
    changed for a particular period of time and notifies the need of an alarm
    """
    def __init__(self, url: str, attribute: str, patience: int, current_rules: List[ThresholdRule]):
        """

        :param url: base url of the historic data entity on Orion Context Broker
        :param attribute: attribute name to search in historic data
        :param patience: maximum number of periods to wait before triggering alarms
        :param current_rules: ThresholdRules that should be not broken to confirm "Positive" Status
        """
        self.historical_source_url = url
        self.attribute_name = attribute
        self.patience = patience
        self.current_rules = current_rules
        self.context: str = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
        self.periods_in_state: Union[int, None] = None  # Number of time periods passed in the current status
        # Confirmation Status from HITL. Choose between "Unconfirmed", "Confirmed Good", "Confirmed Bad"
        self.acknowledgement_status: Union[str, None] = None
        self.previous_happened: Union[str, None] = None  # Previous registered status. Choose between "Good", "Bad"
        self.__get_orion_data()

    def __build_attribute_names(self):
        """
        Programmatically builds attribute names from the historical data to gather

        """
        suffixes = ["_periods", "_status", "_previous"]
        names = [self.attribute_name + suffix for suffix in suffixes]
        return names

    def __get_orion_data(self):
        """
        Gather entity data from Orion Context Broker by picking only built attributes
        Populates Historic Data Fields
        periods_in_state: int
        acknowledgement_status: str
        previous_confirmed: str

        """
        names = self.__build_attribute_names()
        url = self.historical_source_url + "?attrs=" + ",".join(names)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            values = [data[name]["value"]["value"] for name in names]
            self.periods_in_state = values[0]
            self.acknowledgement_status = values[1]
            self.previous_happened = values[2]
            self.context = data["@context"]
        else:
            print("Failed to retrieve data. Status code:", response.status_code)
            print("Response:", response.text)

    def __update_data(self, values: List):
        """
        Update data in Orion Context Broker upon change detection
        :param values: List(int, str, str) contains value for a body to be updated
        values contains updated period, acknowledgement status and status
        """
        names = self.__build_attribute_names()
        url = self.historical_source_url + "/attrs/"
        headers = {"Content-Type": "application/ld+json"}
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {'@context': self.context}

        for name, value in zip(names, values):
            body = add_param_to_body(body, name, value, now)

        r = requests.post(url, headers=headers, data=json.dumps(body))
        print(r.status_code, r.text)
        return

    def confront_historical_data(self, check_rules: str = "all"):
        """

        :param check_rules:
            "any" to check at least one met condition
            "all" to check if all conditions were met
        :return:
            (str) It might return "No Alarm", "Good Change", "Bad Change"
        """

        rules_status = [rule.is_broken for rule in self.current_rules]
        if check_rules == "any":
            flag = any(not broken for broken in rules_status)
        elif check_rules == "all":
            flag = all(not broken for broken in rules_status)
        else:
            raise ValueError("There is an error on checking rules")

        current_status = BAD
        if flag:
            current_status = GOOD

        # Updating previous data if status is the same.
        if current_status != self.previous_happened:
            self.periods_in_state = 1
            self.acknowledgement_status = UNCONFIRMED
            self.previous_happened = current_status
        else:
            self.periods_in_state += 1
            self.previous_happened = current_status
        self.__update_data(([self.periods_in_state + 1, self.acknowledgement_status, current_status]))

        # Return answer
        if self.periods_in_state > self.patience:
            if current_status not in self.acknowledgement_status or self.acknowledgement_status == UNCONFIRMED:
                if current_status == BAD:
                    return BAD + " Change"
                elif current_status == GOOD:
                    return GOOD + " Change"
        return "No Change"
