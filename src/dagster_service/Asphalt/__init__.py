from dagster import Definitions

from .main import process_asphalt

Definitions(jobs=[process_asphalt])