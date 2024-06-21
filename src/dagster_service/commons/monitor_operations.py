from dagster import op
import requests
import re


@op
def get_data(source_url: str
             ) -> dict:
    """
    Retrieve data from a given URL and return it as a dictionary.

    @param source_url: The URL to fetch data from.

    @return: A dictionary containing the retrieved data if the request is successful;
             otherwise, an empty dictionary.
    """

    response = requests.get(source_url)
    if response.status_code == 200:
        data = response.json()

        return data
    else:
        print("Failed to retrieve data from Orion. Status code:", response.status_code)
        print("Response:", response.text)
        return {}


@op
def get_data_from_notification(data_source: dict,
                               attributes: list[str],
                               ) -> list[float]:
    """
    Get data from received notification, returning valuable information.

    @param data_source: Dictionary containing data payload from notification.
    @param attributes: List of attribute names from which to gather values.

    @return: Relevant attribute values.
    """

    values = []
    for attribute in attributes:
        try:
            values.append(float(data_source[attribute]["value"]["value"]))
        except KeyError as e:
            print("An error occurred while retrieving data from notification", e)

    return values


@op
def get_data_from_wp3(data_source: dict,
                      attributes: list[str]
                      ) -> list[dict]:
    """
    Get data from received notification, returning valuable information.

    @param data_source: Dictionary containing data payload from notification.
    @param attributes: List of attribute names from which to gather values.

    @return: Relevant attribute values.
    """

    values = []
    for attribute in attributes:
        attr = [re.search(attribute, key, re.IGNORECASE) for key in data_source.keys()][0]
        try:
            values.append(data_source[attr]["value"])
        except KeyError as e:
            print("An error occurred while retrieving data from WP3 notification", e)

    return values
