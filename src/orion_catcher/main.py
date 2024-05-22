import os
import yaml
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from dagster_service.Pharma.main import process_pharma
from dagster_service.Steel.main import process_steel
from dagster_service.Asphalt.main import process_asphalt
from dagster_service.Aluminium.main import process_aluminium

from kafka import KafkaProducer
from orion_catcher.orion_subscription import check_existing_subscriptions, subscribe

config_folder = os.getenv('ORION-CONFIG')
producer = KafkaProducer(bootstrap_servers=os.getenv('KAFKA-BROKER'))
topics = {}
service_config = {}


def merge_yaml_files(folder_path: str) -> dict:
    """
    Merge YAML files from a given folder into a single dictionary.

    @param folder_path: The path to the folder containing YAML files.
    @return: A dictionary containing the merged content of all YAML files.
    """

    merged_dict = {}

    for filename in os.listdir(folder_path):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                content = yaml.safe_load(file)
                if content:
                    merged_dict.update(content)

    return merged_dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifespan of an application asynchronously.

    @param app: The FastAPI application instance.
    @return: None
    """

    config = merge_yaml_files(config_folder)

    for k in config.keys():
        service = config[k]
        topics[k] = service["kafka_topic"]
        service_config[k] = service["dag_config"]
        subscription_config = service["subscriptions"]

        orion_endpoint = subscription_config["orion_endpoint"]
        print(orion_endpoint)
        subscription_endpoint = subscription_config["subscription_ld_endpoint"]
        notification_endpoint = subscription_config["notification_endpoint"]
        context = subscription_config["context"]
        for entity in subscription_config["to_subscribe"]:
            if not check_existing_subscriptions(orion_endpoint, entity['id'], notification_endpoint, entity['attrs']):
                subscribe(entity['id'], entity['type'], entity['attrs'], notification_endpoint, entity['conditions'],
                          subscription_endpoint, context, 5)

    yield


orion_catcher = FastAPI(lifespan=lifespan)


@orion_catcher.post("/pharma")
async def pharma_handler(data: dict):
    result = process_pharma.execute_in_process(input_values={"incoming_data": data,
                                                             "producer": producer,
                                                             "service_config": service_config["pharma"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.post("/asphalt")
async def asphalt_handler(data: dict):
    result = process_asphalt.execute_in_process(input_values={"incoming_data": data,
                                                              "producer": producer,
                                                              "service_config": service_config["asphalt"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.post("/steel")
async def steel_handler(data: dict):
    result = process_steel.execute_in_process(input_values={"incoming_data": data,
                                                            "producer": producer,
                                                            "service_config": service_config["steel"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.post("/aluminium")
async def aluminum_handler(data: dict):
    result = process_aluminium.execute_in_process(input_values={"incoming_data": data,
                                                                "producer": producer,
                                                                "service_config": service_config["aluminium"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.get("/healthcheck")
def get_healthcheck():
    return "Ok"


# For debug purposes
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(orion_catcher, host="0.0.0.0", port=8010)
