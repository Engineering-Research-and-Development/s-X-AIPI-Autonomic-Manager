from fastapi import FastAPI

from Pharma.main import process_message
orion_catcher = FastAPI()


@orion_catcher.post("/pharma")
async def webhook_handler(data: dict):
    process_message(context={}, message=data)
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
