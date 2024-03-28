from fastapi import FastAPI
from dagster import op

pharma = FastAPI()


@op
def process_message(context, message: dict):
    # Process the received message
    context.log.info(f"Received message: {message}")


@pharma.post("/pharma-endpoint")
async def webhook_handler(data: dict):
    process_message(context={}, message=data)
    return {"message": "Pipeline triggered successfully!"}
