import random
import re
import subprocess
import json
import requests
import fastapi
from datetime import datetime, timedelta
from dagster import asset

with open("/opt/airflow/dags/configs/pharma.json", "r") as f:
    config = json.load(f)


@asset
def monitor_data(data) -> dict:
    conf_dict = {}

    for key, value in data:
        conf_dict[key] = value

    print(conf_dict)
    return conf_dict

