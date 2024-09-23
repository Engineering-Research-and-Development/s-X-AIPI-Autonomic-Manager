import numpy as np

from commons.execute_operations import produce_orion_multi_message, patch_orion
from commons.monitor_operations import get_data_from_notification, get_data
from commons.plan_operations import create_alarm_threshold, create_output_entity
from commons.transform_operations import (
    expand_threshold, create_alarm_payloads, get_threshold_values_from_entity, get_threshold_from_pct_range)
from commons.analysis_operations import (
    discriminate_thresholds)

from dagster import job, op
from kafka import KafkaProducer


@op
def elaborate_solution2(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    if incoming_data['id'] != service_config["small_window"]:
        return
    solution = "solution_2"
    alarm_type_heats = service_config[solution]["alarm_type_heats"]
    alarm_type_materials = service_config[solution]["alarm_type_materials"]
    context = incoming_data["@context"]
    update_url = service_config['base_url'] + service_config['output_entity']

    attrs_heats = service_config[solution]["inputs_heats"]
    upper_threshold_heats = service_config[solution]["upper_threshold_heats"]
    lower_threshold_heats = service_config[solution]["lower_threshold_heats"]
    values_heats = get_data_from_notification(incoming_data, attrs_heats)
    threshold_heats_results = discriminate_thresholds(lower_threshold_heats,
                                                      upper_threshold_heats, values_heats)
    alarms_heats = create_alarm_threshold("Solution 2", alarm_type_heats, attrs_heats,
                                          threshold_heats_results, values_heats, lower_threshold_heats,
                                          upper_threshold_heats)
    payloads_heats = create_alarm_payloads(alarms_heats, context)


    large_window_url = service_config['base_url'] + service_config['large_window']
    large_window = get_data(large_window_url)
    attrs_materials = service_config[solution]["inputs_materials"]
    pct_change_materials = service_config[solution]["pct_change_materials"]
    pct_changes = expand_threshold([pct_change_materials], len(attrs_materials))
    values_materials = get_data_from_notification(incoming_data, attrs_materials)
    _, threshold_base_materials = get_threshold_values_from_entity(large_window,
                                                                   attrs_materials,
                                                                   attrs_materials)
    lower_thresholds_materials, upper_thresholds_materials = (
        get_threshold_from_pct_range(threshold_base_materials, pct_changes))
    threshold_materials_results = discriminate_thresholds(lower_thresholds_materials,
                                                          upper_thresholds_materials,
                                                          values_materials)
    alarms_materials = create_alarm_threshold("Solution 2", alarm_type_materials, attrs_materials,
                                              threshold_materials_results, values_materials,
                                              lower_thresholds_materials, upper_thresholds_materials)
    payloads_materials = create_alarm_payloads(alarms_materials, context)

    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)

    produce_orion_multi_message(update_url, payloads_heats)
    produce_orion_multi_message(update_url, payloads_materials)


@op
def elaborate_solution3(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    if incoming_data['id'] != service_config["large_window"]:
        return
    solution = "solution_3"
    alarm_type = service_config[solution]["alarm_type"]
    attrs = service_config[solution]["inputs"]
    uppers = service_config[solution]["upper_thresholds"]
    lowers = service_config[solution]["lower_thresholds"]
    context = incoming_data["@context"]
    update_url = service_config['base_url'] + service_config['output_entity']

    values = get_data_from_notification(incoming_data, attrs)
    thresholds = discriminate_thresholds(lowers, uppers, values)
    alarms = create_alarm_threshold("Solution 3", alarm_type, attrs, thresholds,
                                    values, lowers, uppers)
    payloads = create_alarm_payloads(alarms, context)

    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)
    produce_orion_multi_message(update_url, payloads)


@job
def process_aluminium(incoming_data, producer, service_config):
    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    elaborate_solution3(incoming_data, producer, service_config)
