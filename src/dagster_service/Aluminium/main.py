import numpy as np

from commons import (monitor_operations,
                     analysis_operations,
                     transform_operations,
                     plan_operations,
                     execute_operations)
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
    values_heats = monitor_operations.get_data_from_notification(incoming_data, attrs_heats)
    threshold_heats_results = analysis_operations.discriminate_thresholds(lower_threshold_heats,
                                                                          upper_threshold_heats, values_heats)
    alarms_heats = plan_operations.create_alarm_threshold("Solution 2", alarm_type_heats, attrs_heats,
                                                          threshold_heats_results, values_heats, lower_threshold_heats,
                                                          upper_threshold_heats)
    payloads_heats = transform_operations.create_alarm_payloads(alarms_heats, context)
    execute_operations.produce_orion_multi_message(update_url, payloads_heats)

    large_window_url = service_config['base_url'] + service_config['large_window']
    large_window = monitor_operations.get_data(large_window_url)
    attrs_materials = service_config[solution]["inputs_materials"]
    pct_change_materials = service_config[solution]["pct_change_materials"]
    pct_changes = transform_operations.expand_threshold([pct_change_materials], len(attrs_materials))
    values_materials = monitor_operations.get_data_from_notification(incoming_data, attrs_materials)
    _, threshold_base_materials = transform_operations.get_threshold_values_from_entity(large_window,
                                                                                        attrs_materials,
                                                                                        attrs_materials)
    lower_thresholds_materials, upper_thresholds_materials = (
        transform_operations.get_threshold_from_pct_range(threshold_base_materials, pct_changes))
    threshold_materials_results = analysis_operations.discriminate_thresholds(lower_thresholds_materials,
                                                                              upper_thresholds_materials,
                                                                              values_materials)
    alarms_materials = plan_operations.create_alarm_threshold("Solution 2", alarm_type_materials, attrs_materials,
                                                              threshold_materials_results, values_materials,
                                                              lower_thresholds_materials, upper_thresholds_materials)
    payloads_materials = transform_operations.create_alarm_payloads(alarms_materials, context)
    execute_operations.produce_orion_multi_message(update_url, payloads_materials)



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

    values = monitor_operations.get_data_from_notification(incoming_data, attrs)
    thresholds = analysis_operations.discriminate_thresholds(lowers, uppers, values)
    alarms = plan_operations.create_alarm_threshold("Solution 3", alarm_type, attrs, thresholds,
                                                    values, lowers, uppers)
    payloads = transform_operations.create_alarm_payloads(alarms, context)
    execute_operations.produce_orion_multi_message(update_url, payloads)




@job
def process_aluminium(incoming_data, producer, service_config):
    # incoming_data, producer, service_config = unpack_data()

    # SOLUTION 1
    #elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    elaborate_solution3(incoming_data, producer, service_config)

    # SOLUTION 4
    #elaborate_solution4(incoming_data, producer, service_config)
