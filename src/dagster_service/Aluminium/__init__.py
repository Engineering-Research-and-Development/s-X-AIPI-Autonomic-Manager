from dagster import Definitions

from .main import process_aluminium

Definitions(jobs=[process_aluminium])