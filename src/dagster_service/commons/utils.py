from datetime import datetime
import re

THRESHOLD_OK = "Ok"
THRESHOLD_LOW = "Lower_Threshold"
THRESHOLD_HIGH = "Upper_Threshold"
THRESHOLD_BROKEN = "Rule_Broken"
THRESHOLD_ERROR = "AM_Error"

UNCONFIRMED = "Unconfirmed"
STATUS_BAD = "Bad"
STATUS_GOOD = "Good"

HISTORY_BAD = "Deteriorating_Change"
HISTORY_GOOD = "Improving_Change"


HISTORICAL_DATA_SUFFIXES = ["_periods", "_status", "_previous", "_old_val"]


def build_historical_data_attribute_names(attribute_name) -> list[str]:
    """
    Programmatically builds attribute names from the historical data to gather.

    @param attribute_name: The base attribute name.
    @return: List of attribute names with suffixes.
    """

    names = [attribute_name + suffix for suffix in HISTORICAL_DATA_SUFFIXES]
    return names


def pick_historical_data_values(names: list[str], entity: dict) -> list[int | str | float]:
    """
    Pick historical data values from the entity based on the provided attribute names.

    @param names: List of attribute names to pick values from.
    @param entity: Dictionary containing historical data.

    @return: List of historical data values.
    @raise KeyError: If any attribute name is not found in the entity.
    """

    try:
        return [entity[name]["value"]["value"] for name in names]
    except KeyError:
        raise KeyError


def add_param_to_body(body: dict, param_name: str, param_value, now: str):
    """
    Add a parameter with its value and timestamp to the body of a request.

    @param body: Dictionary representing the body of the request.
    @param param_name: Name of the parameter to be added.
    @param param_value: Value of the parameter to be added.
    @param now: Current timestamp.

    @return: Updated body dictionary with the added parameter.
    """

    if param_value is not None:
        body[param_name] = {}
        body[param_name]["type"] = "Property"
        body[param_name]["value"] = {}
        body[param_name]["value"]["value"] = param_value
        body[param_name]["value"]["dateUpdated"] = now

    return body


def update_data(values: [], names: [str], payload_context: str):
    """
    Update data with values and corresponding names into a payload body.

    @param values: List of values to be updated.
    @param names: List of names corresponding to the values.
    @param payload_context: Context for the payload.

    @return: Updated payload body.
    """

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {'@context': payload_context}

    for name, value in zip(names, values):
        body = add_param_to_body(body, name, value, now)

    return body


def get_value_from_data(data_dict):

    labels = [re.search("value", key, re.IGNORECASE) for key in list(data_dict["value"].keys())]
    print(list(data_dict["value"].keys()))
    print(labels)
    if "value" in labels:
        return "value"
    elif "avgValue" in labels:
        return "avgValue"
    else:
        return None

