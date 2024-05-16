import numpy as np

from commons import (monitor_operations,
                     analysis_operations,
                     transform_operations,
                     plan_operations,
                     execute_operations)
from dagster import job, op
from kafka import KafkaProducer

from dagster_service.commons.utils import THRESHOLD_OK


@op
def elaborate_solution1(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_1"
    alarm_type = service_config[solution]["alarm_type"]
    inputs = service_config[solution]["inputs"]
    update_url = service_config['base_url'] + service_config['output_entity']
    context = incoming_data["@context"]

    # Solution to check for thresholds with met conditions
    for _, value in inputs.items():
        attrs = value["attrs"]
        lowers = value["lowers"]
        uppers = value["uppers"]
        values = monitor_operations.get_data_from_notification(incoming_data, attrs)
        thresholds = analysis_operations.discriminate_thresholds(lowers, uppers, values)

        # One or two values. If two values, the condition == 0 on second threshold is checked.
        # If condition is met, then delete last attribute (condition attr) and send alarm.
        if len(thresholds) == 2:
            if thresholds[0] != THRESHOLD_OK:
                continue
            thresholds = analysis_operations.merge_thresholds_and(thresholds[0], thresholds[1])
            attrs = attrs.pop()
            lowers = lowers.pop()
            uppers = uppers.pop()
            values = values.pop()

        alarms = plan_operations.create_alarm_threshold("Solution 1", alarm_type, attrs, thresholds,
                                                        values, lowers, uppers)
        payloads = transform_operations.create_alarm_payloads(alarms, context)
        execute_operations.produce_orion_multi_message(update_url, payloads)


@op
def elaborate_solution4(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_4"
    alarm_type = service_config[solution]["alarm_type"]
    attrs = service_config[solution]["inputs"]
    uppers = service_config[solution]["upper_thresholds"]
    lowers = service_config[solution]["lower_thresholds"]
    context = incoming_data["@context"]
    update_url = service_config['base_url'] + service_config['output_entity']

    values = monitor_operations.get_data_from_notification(incoming_data, attrs)
    thresholds = analysis_operations.discriminate_thresholds(lowers, uppers, values)
    alarms = plan_operations.create_alarm_threshold("Solution 4", alarm_type, attrs, thresholds,
                                                    values, lowers, uppers)
    payloads = transform_operations.create_alarm_payloads(alarms, context)
    execute_operations.produce_orion_multi_message(update_url, payloads)


@job
def process_asphalt(incoming_data, producer, service_config):

    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    #elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    #elaborate_solution3(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)
