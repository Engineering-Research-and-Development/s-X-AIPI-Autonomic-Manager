from kafka import KafkaProducer
from src.dagster_service.commons import (monitor_operations,
                                         analysis_operations,
                                         transform_operations,
                                         plan_operations,
                                         execute_operations)
from pharma_operations import *
from dagster import OpExecutionContext, job, op


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
def process_pharma(message: str, producer: KafkaProducer, config: dict):
    data, context = make_elaboration(message)

    # SOLUTION 1
    attrs_solution_1 = config["solution_1"]["inputs"]
    lowers_1 = config["solution_1"]["lower_thresholds"]
    uppers_1 = config["solution_1"]["upper_thresholds"]
    topic_1 = config["solution_1"]["kafka_topic"]
    values_1 = monitor_operations.get_data_from_notification(data, attrs_solution_1)

    if len(values_1) > 1:
        alarms = analysis_operations.discriminate_thresholds(lowers_1, uppers_1, values_1)
        new_status = compute_OCT_probe_status(alarms)
        values_1[0] = new_status
        payload = create_probe_status_payload(values_1, attrs_solution_1, context)
        execute_operations.produce_kafka(producer, topic_1, payload)

    # SOLUTION 2
    attrs_solution_2_1 = config["solution_2"]["inputs_1"]
    attrs_solution_2_2 = config["solution_2"]["inputs_2"]
    uppers_2 = config["solution_2"]["upper_thresholds_2"]
    pct_2 = config["solution_2"]["pct_change_2"]
    topic_2 = config["solution_2"]["kafka_topic"]
    values_2_1 = monitor_operations.get_data_from_notification(data, attrs_solution_2_1)
    values_2_2 = monitor_operations.get_data_from_notification(data, attrs_solution_2_2)
    alarm_type_2 = config["solution_2"]["alarm_type_2"]

    if len(values_2_1) > 1 and data['id'] == config["wp3_alarms"]:
        payload = update_data([values_2_1], [attrs_solution_2_1], context)
        execute_operations.produce_kafka(producer, topic_2, payload)

    if len(values_2_2) > 1 and data['id'] == config["small"]:
        _, upper_thresh_2 = transform_operations.get_threshold_values_from_entity(data, [], uppers_2)
        up_val = upper_thresh_2[0] * pct_2[0] / 100
        lowers_2_2 = [None]
        uppers_2_2 = [up_val]
        alarms_2_2 = analysis_operations.discriminate_thresholds(lowers_2_2, uppers_2_2, values_2_2)
        payloads_2_2 = plan_operations.create_alarm_threshold("Solution 2", alarm_type_2, attrs_solution_2_2,
                                                              alarms_2_2, values_2_2, lowers_2_2, uppers_2_2)
        execute_operations.produce_kafka(producer, topic_2, payloads_2_2)

    # SOLUTION 3
    attrs_solution_3 = config["solution_3"]["inputs"]
    topic_3 = config["solution_3"]["kafka_topic"]
    values_3 = monitor_operations.get_data_from_notification(data, attrs_solution_3)

    if len(values_3) > 1 and data['id'] == config["wp3_alarms"]:
        payload = update_data([values_3], [attrs_solution_3], context)
        execute_operations.produce_kafka(producer, topic_3, payload)

    # SOLUTION 4
    attrs_solution_4 = config["solution_4"]["inputs"]
    topic_4 = config["solution_4"]["kafka_topic"]
    values_4 = monitor_operations.get_data_from_notification(data, attrs_solution_4)

    if len(values_4) > 1 and data['id'] == config["wp3_alarms"]:
        payload = update_data([values_4], [attrs_solution_4], context)
        execute_operations.produce_kafka(producer, topic_4, payload)
