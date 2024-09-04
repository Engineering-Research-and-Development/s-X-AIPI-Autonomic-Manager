from dagster import job, op
from kafka import KafkaProducer

from commons.analysis_operations import discriminate_thresholds, merge_thresholds
from commons.execute_operations import produce_orion_multi_message, patch_orion
from commons.monitor_operations import get_data_from_notification, get_data
from commons.plan_operations import create_alarm_threshold, create_output_entity
from commons.transform_operations import create_alarm_payloads
from commons.utils import THRESHOLD_OK


@op
def elaborate_solution1(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_1"

    # Sub Solution Sensor Alarms on first window
    if incoming_data['id'] != service_config["small_window"]:
        alarm_type = service_config[solution]["alarm_type"]
        inputs = service_config[solution]["inputs"]
        update_url = service_config['base_url'] + service_config['output_entity']
        context = incoming_data["@context"]

        # Solution to check for thresholds with met conditions
        for _, value in inputs.items():
            attrs = value["attrs"]
            lowers = value["lowers"]
            uppers = value["uppers"]
            mode = value["mode"]
            values = get_data_from_notification(incoming_data, attrs)
            thresholds = discriminate_thresholds(lowers, uppers, values)

            # One or two values. If two values, the condition == 0 on second threshold is checked.
            # If condition is met, then delete last attribute (condition attr) and send alarm.
            if len(thresholds) == 2:
                thresholds = merge_thresholds([thresholds[0]], [thresholds[1]], mode)
                attrs.pop()
                lowers.pop()
                uppers.pop()
                values.pop()

            alarms = create_alarm_threshold("Solution 1", alarm_type, attrs, thresholds,
                                            values, lowers, uppers)

            payloads = create_alarm_payloads(alarms, context)

            output_entity = get_data(update_url)

            if output_entity == {}:
                out_entity = create_output_entity(service_config['output_entity'], context)
                patch_orion(update_url, out_entity)

            produce_orion_multi_message(update_url, payloads)

    # Sub Solution for AI Retraining on second window
    if incoming_data['id'] != service_config["small_laboratory"]:
        alarm_type = service_config[solution]["alarm_type_AI"]
        attrs = service_config[solution]["inputs_AI"]
        uppers = service_config[solution]["upper_thresholds_AI"]
        lowers = service_config[solution]["lower_thresholds_AI"]
        context = incoming_data["@context"]
        update_url = service_config['base_url'] + service_config['output_entity']

        values = get_data_from_notification(incoming_data, attrs)
        thresholds = discriminate_thresholds(lowers, uppers, values)
        alarms = create_alarm_threshold("Solution 1", alarm_type, attrs, thresholds,
                                        values, lowers, uppers)

        payloads = create_alarm_payloads(alarms, context)

        output_entity = get_data(update_url)
        if output_entity == {}:
            out_entity = create_output_entity(service_config['output_entity'], context)
            patch_orion(update_url, out_entity)
        produce_orion_multi_message(update_url, payloads)


@op
def elaborate_solution2(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    if incoming_data['id'] != service_config["small_window"]:
        return

    solution = "solution_2"
    alarm_type = service_config[solution]["alarm_type"]
    attrs = service_config[solution]["inputs"]
    uppers = service_config[solution]["upper_thresholds"]
    lowers = service_config[solution]["lower_thresholds"]
    context = incoming_data["@context"]
    update_url = service_config['base_url'] + service_config['output_entity']

    values = get_data_from_notification(incoming_data, attrs)
    thresholds = discriminate_thresholds(lowers, uppers, values)
    alarms = create_alarm_threshold("Solution 2", alarm_type, attrs, thresholds,
                                    values, lowers, uppers)

    payloads = create_alarm_payloads(alarms, context)

    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)
    produce_orion_multi_message(update_url, payloads)




@op
def elaborate_solution4(incoming_data: dict, producer: KafkaProducer, service_config: dict):

    if incoming_data['id'] != service_config["small_laboratory"]:
        return

    solution = "solution_4"
    alarm_type = service_config[solution]["alarm_type"]
    attrs = service_config[solution]["inputs"]
    uppers = service_config[solution]["upper_thresholds"]
    lowers = service_config[solution]["lower_thresholds"]
    context = incoming_data["@context"]
    update_url = service_config['base_url'] + service_config['output_entity']

    values = get_data_from_notification(incoming_data, attrs)
    thresholds = discriminate_thresholds(lowers, uppers, values)
    alarms = create_alarm_threshold("Solution 4", alarm_type, attrs, thresholds,
                                    values, lowers, uppers)

    payloads = create_alarm_payloads(alarms, context)

    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)
    produce_orion_multi_message(update_url, payloads)


@job
def process_asphalt(incoming_data, producer, service_config):
    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)
