from datetime import datetime

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


HISTORICAL_DATA_SUFFIXES = ["_periods", "_status", "_previous"]


def build_historical_data_attribute_names(attribute_name) -> list[str]:
    """
    Programmatically builds attribute names from the historical data to gather

    """
    names = [attribute_name + suffix for suffix in HISTORICAL_DATA_SUFFIXES]
    return names


def pick_historical_data_values(names: list[str], entity: dict) -> list[float]:
    """

    @param names: list of names from which to pick data
    @param entity: json payload from Orion Context Broker
    @return: List[float] containing periods_in_state, acknowledgement_status, previous_state
    """
    try:
        return [float(entity[name]["value"]["value"]) for name in names]
    except KeyError as e:
        raise KeyError


def add_param_to_body(body: dict, param_name: str, param_value, now: str):
    """
    Updates an NGSI-LD payload with new attributes
    :param body: starting object to populate
    :param param_name: attribute name to add
    :param param_value: value of the attribute
    :param now: ISO Time stringed date
    :return: (dict) -> Updated object
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
    Update data in Orion Context Broker upon change detection

    :param values: contains values for a body to be updated
    :param names: contains names of parameters
    :param payload_context: NGSI-LD context

    values contains updated period, acknowledgement status and status (if historical data)
    """

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {'@context': payload_context}

    for name, value in zip(names, values):
        body = add_param_to_body(body, name, value, now)

    return body
