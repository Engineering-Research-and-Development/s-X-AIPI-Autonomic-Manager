from dagster import Definitions

from .main import process_pharma

Definitions(jobs=[process_pharma])

