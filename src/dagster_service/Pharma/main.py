from kafka import KafkaProducer

from dagster_service.commons import (monitor_operations,
                                     analysis_operations,
                                     transform_operations,
                                     plan_operations,
                                     execute_operations)
from .pharma_operations import *
from dagster import job, multi_asset, AssetOut, Output


@multi_asset(outs={"incoming_data": AssetOut(), "producer": AssetOut(), "service_config": AssetOut()})
def unpack_data(data: dict):
    yield Output(data["incoming_data"], output_name="incoming_data")
    yield Output(data["producer"], output_name="producer")
    yield Output(data["service_config"], output_name="service_config")


@op
def elaborate_solution1(data: dict, producer: KafkaProducer, config: dict):
    attrs = config["solution_1"]["inputs"]
    lowers = config["solution_1"]["lower_thresholds"]
    uppers = config["solution_1"]["upper_thresholds"]
    topic = config["solution_1"]["kafka_topic"]
    values = monitor_operations.get_data_from_notification(data, attrs)

    if len(values) > 1:
        alarms = analysis_operations.discriminate_thresholds(lowers, uppers, values)
        new_status = compute_OCT_probe_status(alarms)
        values[0] = new_status
        payload = create_probe_status_payload(values, attrs)
        execute_operations.produce_kafka(producer, topic, payload)


@op
def elaborate_solution2(data: dict, producer: KafkaProducer, config: dict):
    attrs_1 = config["solution_2"]["inputs_1"]
    attrs_2 = config["solution_2"]["inputs_2"]
    uppers = config["solution_2"]["upper_thresholds_2"]
    pct = config["solution_2"]["pct_change_2"]
    topic = config["solution_2"]["kafka_topic"]
    values_1 = monitor_operations.get_data_from_notification(data, attrs_1)
    values_2 = monitor_operations.get_data_from_notification(data, attrs_2)
    alarm_type_2 = config["solution_2"]["alarm_type_2"]

    if len(values_1) > 1 and data['id'] == config["wp3_alarms"]:
        payload = update_data([values_1], [attrs_1])
        execute_operations.produce_kafka(producer, topic, payload)

    if len(values_2) > 1 and data['id'] == config["small"]:
        _, upper_thresh_2 = transform_operations.get_threshold_values_from_entity(data, [], uppers)
        up_val = upper_thresh_2[0] * pct[0] / 100
        lowers_2_2 = [None]
        uppers_2_2 = [up_val]
        alarms_2_2 = analysis_operations.discriminate_thresholds(lowers_2_2, uppers_2_2, values_2)
        payloads_2_2 = plan_operations.create_alarm_threshold("Solution 2", alarm_type_2, attrs_2,
                                                              alarms_2_2, values_2, lowers_2_2, uppers_2_2)
        execute_operations.produce_kafka(producer, topic, payloads_2_2)


@op
def elaborate_solution3(data: dict, producer: KafkaProducer, config: dict):
    attrs = config["solution_3"]["inputs"]
    topic = config["solution_3"]["kafka_topic"]
    values = monitor_operations.get_data_from_notification(data, attrs)

    if len(values) > 1 and data['id'] == config["wp3_alarms"]:
        payload = update_data([values], [attrs])
        execute_operations.produce_kafka(producer, topic, payload)


@op
def elaborate_solution4(data: dict, producer: KafkaProducer, config: dict):
    attrs = config["solution_4"]["inputs"]
    topic = config["solution_4"]["kafka_topic"]
    values = monitor_operations.get_data_from_notification(data, attrs)

    if len(values) > 1 and data['id'] == config["wp3_alarms"]:
        payload = update_data([values], [attrs])
        execute_operations.produce_kafka(producer, topic, payload)


@job
def process_pharma():
    incoming_data, producer, config = unpack_data()

    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, config)

    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, config)

    # SOLUTION 3
    elaborate_solution3(incoming_data, producer, config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, config)
