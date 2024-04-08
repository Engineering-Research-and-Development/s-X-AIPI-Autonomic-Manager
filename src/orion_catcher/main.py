import yaml
from fastapi import FastAPI
from dagster_service.Pharma.main import process_message
from .subscription import check_existing_subscriptions, subscribe

orion_catcher = FastAPI()
config_file = "config.yml"


# @orion_catcher.on_event("startup")
# async def subscribe():
#     with open(config_file, "r") as f:
#         config = yaml.safe_load(f)
#
#     for k in config.keys():
#         service = config[k]
#         if not check_existing_subscriptions(service["orion_endpoint"], service["entity"],
#                                             service["notification"]["url"]):
#             await subscribe(service["entity"], service["attrs"], service["notification"]["url"],
#                             service["notification"]["attrs"], service["notification"]["metadata"],
#                             service["orion-host"])


@orion_catcher.post("/pharma")
async def webhook_handler(data: dict):
    process_message.execute_in_process(input_values=data)
    return {"message": "Pipeline triggered successfully!"}


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
    uvicorn.run(orion_catcher, host="0.0.0.0", port=8000)
