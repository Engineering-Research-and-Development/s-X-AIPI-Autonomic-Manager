import numpy as np
from kafka import KafkaProducer

from commons import (monitor_operations,
                     analysis_operations,
                     transform_operations,
                     plan_operations,
                     execute_operations)
from dagster import job, op

@op
def elaborate_solution1(incoming_data, producer, service_config):
    solution = "solution_1"
    alarm_type = service_config[solution]["alarm_type"]
    inputs = service_config[solution]["inputs"]
    update_url = service_config['base_url'] + service_config['output_entity']
    for _, value in inputs.items():
        attrs = value["attrs"]
        lowers = value["lowers"]
        uppers = value["uppers"]
        values = monitor_operations.get_data_from_notification(incoming_data, attrs)
        thresholds = analysis_operations.discriminate_thresholds(lowers, uppers, values)
        if len(thresholds) == 2:
            result_thresholds = analysis_operations.merge_thresholds_and([thresholds[0]], [thresholds[1]])
        alarms = plan_operations.create_alarm_threshold("Solution 1", alarm_type, attrs, thresholds,
                                                        values, lowers, uppers)
        payloads = transform_operations.create_alarm_payloads(alarms, incoming_data["@context"])
        execute_operations.produce_orion_multi_message(update_url, payloads)

    pass


@job
def process_asphalt(incoming_data, producer, service_config):
    # incoming_data, producer, service_config = unpack_data()

    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    #elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    #elaborate_solution3(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)