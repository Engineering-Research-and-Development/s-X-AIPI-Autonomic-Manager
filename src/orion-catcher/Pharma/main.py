from dagster import OpExecutionContext, job, op


@op
def make_elaboration(context: OpExecutionContext, message: str):
    # Process the received message
    context.log.info(f"Received message: {message}")


@job
def process_message(message: str):
    make_elaboration(message)
