import os
import yaml
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from dagster_service.Pharma.main import process_pharma
from dagster_service.Steel.main import process_steel
from dagster_service.Asphalt.main import process_asphalt

from kafka import KafkaProducer
from orion_catcher.subscription import check_existing_subscriptions, subscribe

config_file = os.getenv('ORION-CONFIG')
producer = KafkaProducer(bootstrap_servers=os.getenv('KAFKA-BROKER'))
topics = {}
service_config = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

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
async def webhook_handler(data: dict):
    result = process_pharma.execute_in_process(input_values={"incoming_data": data,
                                                             "producer": producer,
                                                             "service_config": service_config["pharma"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.post("/asphalt")
async def webhook_handler(data: dict):
    result = process_asphalt.execute_in_process(input_values={"incoming_data": data,
                                                              "producer": producer,
                                                              "service_config": service_config["asphalt"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.post("/steel")
async def webhook_handler(data: dict):
    result = process_steel.execute_in_process(input_values={"incoming_data": data,
                                                            "producer": producer,
                                                            "service_config": service_config["steel"]})
    if result.success:
        return {"message": "Pipeline executed successfully", "details": str(result)}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute pipeline")


@orion_catcher.post("/aluminium")
async def webhook_handler(data: dict):
    # process_message(context={}, message=data)
    return {"message": "Pipeline triggered successfully!"}


# For debug purposes
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(orion_catcher, host="0.0.0.0", port=8010)
