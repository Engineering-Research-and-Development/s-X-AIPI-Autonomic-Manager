from dagster import op

@op
def process_message(context, message: dict):
    # Process the received message
    context.log.info(f"Received message: {message}")
