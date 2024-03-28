from fastapi import FastAPI
from dagster import solid, pipeline, execute_pipeline, ModeDefinition

pharma = FastAPI()


@solid
def process_message(context, message):
    # Process the received message
    context.log.info(f"Received message: {message}")


@pipeline(
    mode_defs=[
        ModeDefinition(name="production")
    ]
)
def message_processing_pipeline():
    process_message()


@pharma.post("/pharma-endpoint")
async def webhook_handler():

    _ = execute_pipeline(
        message_processing_pipeline,
        mode="production"
    )
    return {"message": "Pipeline triggered successfully!"}
