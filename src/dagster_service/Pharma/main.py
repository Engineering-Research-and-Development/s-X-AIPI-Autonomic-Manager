import numpy as np
from kafka import KafkaProducer

from dagster import job, op

from .pharma_operations import compute_OCT_probe_status, create_probe_status_payload
from commons.monitor_operations import get_data_from_notification, get_data_from_wp3
from commons.utils import update_data
from commons.analysis_operations import discriminate_thresholds
from commons.execute_operations import produce_kafka
from commons.plan_operations import create_alarm_threshold
from commons.transform_operations import get_threshold_values_from_entity


@op
def elaborate_solution1(data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_1"
    attrs = service_config[solution]["inputs"]
    lowers = service_config[solution]["lower_thresholds"]
    uppers = service_config[solution]["upper_thresholds"]
    topic = service_config[solution]["kafka_topic"]
    values, _ = get_data_from_notification(data, attrs)

    if len(values) > 1:
        alarms = discriminate_thresholds(lowers, uppers, values)
        new_status = compute_OCT_probe_status(alarms)
        values[0] = new_status
        payload = create_probe_status_payload(values, attrs, data['@context'])
        produce_kafka(producer, topic, [payload])


@op
def elaborate_solution2(data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_2"
    attrs_1 = service_config[solution]["inputs_1"]
    attrs_2 = service_config[solution]["inputs_2"]
    uppers = service_config[solution]["upper_thresholds_2"]
    pct = service_config[solution]["pct_change_2"]
    topic = service_config[solution]["kafka_topic"]
    values_1 = get_data_from_wp3(data, attrs_1)
    values_2, _ = get_data_from_notification(data, attrs_2)
    alarm_type_2 = service_config[solution]["alarm_type_2"]

    if len(values_1) > 0 and data['id'] == service_config["wp3_alarms"]:
        payload = update_data(values_1, attrs_1, data['@context'])
        produce_kafka(producer, topic, [payload])

    print(values_2)
    if len(values_2) > 0 and data['id'] == service_config["small_window"]:
        _, upper_thresh_2 = get_threshold_values_from_entity(data, [], uppers)
        up_val = upper_thresh_2[0] * pct[0] / 100
        lowers = [-np.inf]
        uppers = [up_val]
        alarms = discriminate_thresholds(lowers, uppers, values_2)
        payloads = create_alarm_threshold("Solution 2", alarm_type_2, attrs_2,
                                          alarms, values_2, lowers, uppers)
        produce_kafka(producer, topic, payloads)


@op
def elaborate_solution3(data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_3"
    if data['id'] != service_config["wp3_alarms"]:
        return
    attrs = service_config[solution]["inputs"]
    topic = service_config[solution]["kafka_topic"]
    values = get_data_from_wp3(data, attrs)
    print(values)

    if len(values) > 0:
        payload = update_data(values, attrs, data['@context'])
        produce_kafka(producer, topic, [payload])


@op
def elaborate_solution4(data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_4"
    if data['id'] != service_config["wp3_alarms"]:
        return
    attrs = service_config[solution]["inputs"]
    topic = service_config[solution]["kafka_topic"]
    values = get_data_from_wp3(data, attrs)

    if len(values) > 0:
        payload = update_data(values, attrs, data['@context'])
        produce_kafka(producer, topic, [payload])


@op
def elaborate_solution5(data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_5"
    if data['id'] != service_config["wp3_alarms"]:
        return
    attrs = service_config[solution]["inputs"]
    topic = service_config[solution]["kafka_topic"]
    values = get_data_from_wp3(data, attrs)

    if len(values) > 0:
        payload = update_data(values, attrs, data['@context'])
        produce_kafka(producer, topic, [payload])


@job
def process_pharma(incoming_data, producer, service_config):
    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    # elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    elaborate_solution3(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)

    # SOLUTION 5
    elaborate_solution5(incoming_data, producer, service_config)
