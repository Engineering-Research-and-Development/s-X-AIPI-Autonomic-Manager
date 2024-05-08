from dagster import op

'''
@op
def get_data(context: OpExecutionContext,
             source_url: str
             ) -> dict:
    """
    Function taking as input an entity url and retrieving data

    @param source_url: url from which to get historical source entity from Orion
    """

    response = requests.get(source_url)
    if response.status_code == 200:
        data = response.json()

        return data
    else:
        print("Failed to retrieve data. Status code:", response.status_code)
        print("Response:", response.text)
        return {}
'''


@op
def get_data_from_notification(data_source: dict,
                               attributes: list[str]
                               ) -> list[float]:
    """
    Get data from received notification, returning valuable information
    @param data_source: dictionary containing data payload from notification
    @param attributes: list of attribute names from which to gather values

    @return: relevant attribute values
    """

    try:
        for attribute in attributes:
            print(data_source[attribute]["value"]["value"], attribute)
        values = [float(data_source[attribute]["value"]["value"]) for attribute in attributes]
        return values
    except KeyError as e:
        print(e)
        return []
