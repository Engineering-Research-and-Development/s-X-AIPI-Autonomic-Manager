from dagster import (
    asset,
    AssetExecutionContext,
    AssetIn,
    Definitions,
    define_asset_job,
    AssetSelection,
    ScheduleDefinition)
from typing import List

group_name = "test_assets"


@asset(group_name=group_name)
def my_first_asset(context: AssetExecutionContext):
    """
    This is the first asset used for testing
    :return: List
    """
    print("This is a text print message")
    context.log.info("This is a INFO log")
    return [1, 2, 3]


# @asset(deps=[my_first_asset]) to set dependencies using assets as parameters needs the use of assets after context
# definition explicit dependency: @asset(ins={"upstream" : AssetIn(key="my_first_asset")}) -> Follows that parameter
# is not the function name but upstream, now
@asset(key="my_awesome_second_asset", group_name=group_name)
def second_asset(context: AssetExecutionContext, my_first_asset: List):
    """
    This is our second asset
    :return: 
    """
    data = my_first_asset + [4, 5, 6]
    context.log.info(f"Output data is {data}")
    return data


# Remember: for defining AssetIn you should use keys, not function name
# Remember: default key is function name. You can define it again
@asset(ins={
    "first_upstream": AssetIn(key="my_first_asset"),
    "second_upstream": AssetIn(key="my_awesome_second_asset")
},
    key="alternative_third_asset_name",
    group_name=group_name)
def third_asset(
        context: AssetExecutionContext,
        first_upstream: List,
        second_upstream: List
):
    """
    Picking two assets as input.
    :return:
    """
    data = {
        "first_asset": first_upstream,
        "second_asset": second_upstream,
        "third_asset": second_upstream + [7, 8]

    }
    return data


# Here we define assets that are used. If we define only first and second asset, third will disappear from DAG
defs = Definitions(
    assets=[my_first_asset, second_asset, third_asset],
    jobs=[
        define_asset_job(
            name="hello_dagster_job",
            # selection=[my_first_asset, second_asset, third_asset], alternatively
            # selection=AssetSelection.key_prefix("prefix")
            # selection=AssetSelection.groups("group_name")
            selection=AssetSelection.all()
        )
    ],
    schedules=[
        ScheduleDefinition(
            name="hello_dagster_schedule",
            job_name="hello_dagster_job",
            cron_schedule="@hourly",
        )
    ]
)
