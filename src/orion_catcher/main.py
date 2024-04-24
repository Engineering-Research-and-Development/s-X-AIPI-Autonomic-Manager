import os
import yaml
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.dagster_service.Pharma.main import process_message
from kafka import KafkaProducer
from src.orion_catcher.subscription import check_existing_subscriptions, subscribe

config_file = os.getenv('ORION-CONFIG')
producer = KafkaProducer(bootstrap_servers=os.getenv('KAFKA-BROKER'))
topics = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    for k in config.keys():
        service = config[k]
        topics[k] = service["kafka_topic"]

#         if not check_existing_subscriptions(service["orion_endpoint"], service["entity"],
#                                             service["notification"]["url"]):
#             await subscribe(service["entity"], service["attrs"], service["notification"]["url"],
#                             service["notification"]["attrs"], service["notification"]["metadata"],
#                             service["orion-host"])
    yield

orion_catcher = FastAPI(lifespan=lifespan)


@orion_catcher.post("/pharma")
async def webhook_handler(data: dict):
    process_message.execute_in_process(input_values=data)
    producer.send(topics["pharma"], "Pharma pipeline triggered successfully!".encode())
    return {"message": "Pharma pipeline triggered successfully!"}


@orion_catcher.post("/asphalt")
async def webhook_handler(data: dict):
    process_message(context={}, message=data)
    return {"message": "Pipeline triggered successfully!"}


@orion_catcher.post("/steel")
async def webhook_handler(data: dict):
    process_message(context={}, message=data)
    return {"message": "Pipeline triggered successfully!"}


@orion_catcher.post("/aluminium")
async def webhook_handler(data: dict):
    process_message(context={}, message=data)
    return {"message": "Pipeline triggered successfully!"}


# For debug purposes
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(orion_catcher, host="0.0.0.0", port=8010)
