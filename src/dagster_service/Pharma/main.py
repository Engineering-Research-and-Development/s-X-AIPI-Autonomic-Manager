from kafka import KafkaProducer
from src.dagster_service.commons import (monitor_operations,
                                         analysis_operations,
                                         transform_operations,
                                         plan_operations,
                                         execute_operations)
from pharma_operations import *
from dagster import OpExecutionContext, job, op
import yaml
import os


@op
def make_elaboration(context: OpExecutionContext, message: dict):
    # Process the received message
    context.log.info(f"Received message: {message}")
    data = message["data"]
    context = data['@context']
    return data, context


'''
@op
def read_configuration(context: OpExecutionContext, message: dict):
    attrs_solution_1 = config["solution_1"]["inputs"]
    attrs_lowers_1 = config["solution_1"]["lower_thresholds"]
    attrs_uppers_1 = config["solution_1"]["upper_thresholds"]

    attrs_solution_2_1 = config["solution_2"]["inputs_1"]
    attrs_solution_2_2 = config["solution_2"]["inputs_2"]
    attrs_uppers_2_2 = config["solution_2"]["upper_thresholds_2"]
    attrs_pct_change2_2 = config["solution_2"]["pct_change_2"]

    attrs_solution_3 = config["solution_3"]["inputs"]

    attrs_solution_4 = config["solution_4"]["inputs"]
'''


@job
def process_message(message: str, producer: KafkaProducer, config: dict):
    data, context = make_elaboration(message)

    # SOLUTION 1
    attrs_solution_1 = config["solution_1"]["inputs"]
    lowers_1 = config["solution_1"]["lower_thresholds"]
    uppers_1 = config["solution_1"]["upper_thresholds"]
    topic = config["solution_1"]["kafka_topic"]
    values_1 = monitor_operations.get_data_from_notification(data, attrs_solution_1)
    if len(values_1) > 1:
        alarms = analysis_operations.discriminate_thresholds(lowers_1, uppers_1, values_1)
        status = compute_OCT_probe_status(alarms)
        values_1[0] = status
        payload = create_probe_status_payload(values_1, attrs_solution_1, context)
        execute_operations.produce_kafka(producer, topic, payload)
