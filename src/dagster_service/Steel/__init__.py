from dagster import Definitions

from .main import process_steel

Definitions(jobs=[process_steel])

