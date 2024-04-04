from dagster import Definitions
from .main import process_message

Definitions(
    jobs=[process_message]
)
