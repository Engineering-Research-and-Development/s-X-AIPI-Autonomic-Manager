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


def merge_yaml_files(folder_path) -> dict:
    """
    Merge yaml files found in a folder into a single data structure


    Args:
        folder_path (str): the folder to analyse


    Returns:
        A dictionary with the folder structure
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


def read_configs(folder_path) -> dict:
    """
    Reads the folder with the configuration of the solutions as well as the additional one

    Args:
        folder_path (str): the folder to analyse


    Returns:
        A dictionary with the folder structure
    """
    config = merge_yaml_files(folder_path)
    try:
        additional_config = merge_yaml_files("additional_" + folder_path)
        config.update(additional_config)
        print("Additional configuration folder loaded")
    except FileNotFoundError:
        pass

    return config


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = read_configs(folder_path=config_folder)

    for k in config.keys():
        service = config[k]
        topics[k] = service["kafka_topic"]
        service_config[k] = service["dag_config"]

    #         if not check_existing_subscriptions(service["orion_endpoint"], service["entity"],
    #                                             service["notification"]["url"]):
    #             await subscribe(service["entity"], service["attrs"], service["notification"]["url"],
    #                             service["notification"]["attrs"], service["notification"]["metadata"],
    #                             service["orion-host"])
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
