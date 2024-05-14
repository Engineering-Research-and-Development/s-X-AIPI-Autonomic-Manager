import numpy as np
from kafka import KafkaProducer

from commons import (monitor_operations,
                     analysis_operations,
                     transform_operations,
                     plan_operations,
                     execute_operations)
from dagster import job, multi_asset, AssetOut, Output, op


def clean_names(names: [str]):
    new_names = [name.split("_zero")[0] if "_zero" in name else name for name in names]
    return new_names

def adjust_alarm_type(alarms: [str]):
    new_names = ["Material Introduction Detection" if "Good" in alarm else "Material Removal Detection" for alarm in alarms]
    return new_names


@op
def sub_solution_check_zero_nans(incoming_data: dict,
                                 producer: KafkaProducer,
                                 service_config: dict,
                                 attrs: list[str],
                                 solution: str,
                                 lower_threshold: str,
                                 upper_threshold: str,
                                 alarm_type: str,
                                 kafka_topic: str):
    values = monitor_operations.get_data_from_notification(incoming_data, attrs)
    upper_thresholds = transform_operations.expand_threshold(service_config[solution][upper_threshold], len(values))
    lower_thresholds = transform_operations.expand_threshold(service_config[solution][lower_threshold], len(values))
    results = analysis_operations.discriminate_thresholds(lower_thresholds, upper_thresholds, values)
    payloads_zeros = plan_operations.create_alarm_threshold("Solution 1", alarm_type, attrs, results, values,
                                                            lower_thresholds, upper_thresholds)
    execute_operations.produce_kafka(producer, kafka_topic, payloads_zeros)


@op
def sub_solution_material_used(incoming_data: dict,
                               producer: KafkaProducer,
                               service_config: dict,
                               historical_data_url: str,
                               attrs_max: list[str],
                               attrs_zeros: list[str],
                               nr_heats: str,
                               patience: int,
                               solution: str,
                               alarm_type: str,
                               kafka_topic: str
                               ):
    # Setting useful values
    LOWER_THRESHOLD_MAX = service_config[solution]['scapmax_lower']
    UPPER_THRESHOLD_MAX = np.inf
    context = incoming_data["@context"]

    # Checking rules for max content values
    values_max = monitor_operations.get_data_from_notification(incoming_data, attrs_max)
    lower_threshold_max = transform_operations.expand_threshold(LOWER_THRESHOLD_MAX, len(values_max))
    upper_threshold_max = transform_operations.expand_threshold(UPPER_THRESHOLD_MAX, len(values_max))
    results_max = analysis_operations.discriminate_thresholds(lower_threshold_max, upper_threshold_max, values_max)

    # Checking rules for number of zeros
    values_zeros = monitor_operations.get_data_from_notification(incoming_data, attrs_zeros)
    values_nrheats = monitor_operations.get_data_from_notification(incoming_data, nr_heats)
    upper_threshold_nrheats = transform_operations.expand_threshold(values_nrheats, len(values_zeros))
    lower_threshold_nrheats = transform_operations.expand_threshold(-1, len(values_zeros))
    results_nrheats = analysis_operations.discriminate_thresholds(
        lower_threshold_nrheats, upper_threshold_nrheats, values_zeros)

    # Merging rules from two sources
    results_threshold = analysis_operations.merge_thresholds_and(results_max, results_nrheats)

    # Retrieving the data from historical storage
    historical_data = monitor_operations.get_data(historical_data_url)
    attrs_clean = clean_names(attrs_zeros)
    periods_list, ack_list, previous_list, old_values, historical_context = (
        transform_operations.retrieve_values_from_historical_data(historical_data, attrs_clean))

    # Analyze Historical Data
    historical_alarms_analysis, historical_current_status = analysis_operations.analyze_historical_data(
        periods_list, ack_list, results_threshold, patience
    )

    # Update Historical Data
    mock_values = transform_operations.expand_threshold(0.0, len(values_zeros))
    update_payload = plan_operations.update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        mock_values, attrs_clean, historical_context
    )
    execute_operations.patch_orion(historical_data_url, update_payload)

    # Send Alarm To Kafka
    historical_alarms_analysis = adjust_alarm_type(historical_alarms_analysis)
    historical_alarms = plan_operations.create_alarm_history(
        "Solution 1", alarm_type, attrs_clean, historical_alarms_analysis, periods_list, ack_list
    )
    historical_alarms = transform_operations.create_alarm_payloads(historical_alarms, context)
    execute_operations.produce_kafka(producer, kafka_topic, historical_alarms)



@op
def elaborate_solution1(incoming_data, producer, service_config):
    kafka_topic = service_config["kafka_topic"]
    alarm_type_materials = service_config["solution_1"]["alarm_type_materials"]
    historical_data_url = service_config["base_url"] + service_config["solution_1"]["historical_entity"]
    patience = service_config["solution_1"]["historical_patience"]

    # Checking for zeros
    attr_zeros = service_config["solution_1"]["zeros_inputs"]
    alarm_type_zeros = service_config["solution_1"]["alarm_type_zeros"]
    sub_solution_check_zero_nans(incoming_data, producer, service_config, attr_zeros, "solution_1",
                                 "zero_inputs_lower_threshold", "zero_inputs_upper_threshold", alarm_type_zeros,
                                 kafka_topic)

    # Checking for NaNs
    attr_nan = service_config["solution_1"]["nan_inputs"]
    alarm_type_nan = service_config["solution_1"]["alarm_type_nan"]
    sub_solution_check_zero_nans(incoming_data, producer, service_config, attr_nan, "solution_1",
                                 "nan_inputs_lower_threshold", "nan_inputs_upper_threshold", alarm_type_nan,
                                 kafka_topic)

    # Checking first scrap group
    attr_group_0_zeros = service_config["solution_1"]["scrapzeros_inputs_0"]
    attr_group_0_max = service_config["solution_1"]["scrapmax_inputs_0"]
    attr_heats_0 = service_config["solution_1"]["nrheats_scrap"]
    sub_solution_material_used(incoming_data, producer, service_config, service_config, historical_data_url,
                               attr_group_0_max, attr_group_0_zeros, attr_heats_0, patience, "solution_1",
                               alarm_type_materials, kafka_topic)

    # Checking second scrap group
    attr_group_1_zeros = service_config["solution_1"]["scrapzeros_inputs_1"]
    attr_group_1_max = service_config["solution_1"]["scrapmax_inputs_1"]
    attr_heats_1 = service_config["solution_1"]["nrheats_scrap"]
    sub_solution_material_used(incoming_data, producer, service_config, service_config, historical_data_url,
                               attr_group_1_max, attr_group_1_zeros, attr_heats_1, patience, "solution_1",
                               alarm_type_materials, kafka_topic)

    # Checking lime content
    attr_group_2_zeros = service_config["solution_1"]["scrapzeros_inputs_2"]
    attr_group_2_max = service_config["solution_1"]["scrapmax_inputs_2"]
    attr_heats_2 = service_config["solution_1"]["nrheats_lime"]
    sub_solution_material_used(incoming_data, producer, service_config, service_config, historical_data_url,
                               attr_group_2_max, attr_group_2_zeros, attr_heats_2, patience, "solution_1",
                               alarm_type_materials, kafka_topic)

    # Checking lime content
    attr_group_3_zeros = service_config["solution_1"]["scrapzeros_inputs_3"]
    attr_group_3_max = service_config["solution_1"]["scrapmax_inputs_3"]
    attr_heats_3 = service_config["solution_1"]["nrheats_limecoke"]
    sub_solution_material_used(incoming_data, producer, service_config, service_config, historical_data_url,
                               attr_group_3_max, attr_group_3_zeros, attr_heats_3, patience, "solution_1",
                               alarm_type_materials, kafka_topic)


def elaborate_solution2(incoming_data, producer, service_config):
    # Check if inputs overcome thresholds. If yes, send alarm. No wait
    pass


def elaborate_solution3(incoming_data, producer, service_config):
    # Check the threshold attribute in data, check value and see if error is higher then 15% threshold.
    # If yes, send alarm, wait 1 period
    pass


def elaborate_solution4(incoming_data, producer, service_config):

    #Test
    solution = "solution_4"
    attrs = service_config[solution]["inputs"]
    pct_change = service_config[solution]["pct_change"]
    patience = service_config[solution]["historical_patience"]
    alarm_type = service_config[solution]["alarm_type"]
    kafka_topic = service_config["kafka_topic"]

    historical_data_url = service_config["base_url"] + service_config["solution_4"]["historical_entity"]
    historical_data = monitor_operations.get_data(historical_data_url)

    context = incoming_data["@context"]
    values = monitor_operations.get_data_from_notification(incoming_data, attrs)

    attrs_clean = clean_names(attrs)
    periods_list, ack_list, previous_list, old_values, historical_context = (
        transform_operations.retrieve_values_from_historical_data(historical_data, attrs_clean))

    pct_expand = transform_operations.expand_threshold(pct_change, len(attrs))
    lower_thresholds, upper_thresholds = transform_operations.get_threshold_from_pct_range(old_values, pct_expand)
    results_threshold = analysis_operations.discriminate_thresholds(lower_thresholds, upper_thresholds, values)

    # Analyze Historical Data
    historical_alarms_analysis, historical_current_status = analysis_operations.analyze_historical_data(
        periods_list, ack_list, results_threshold, patience
    )

    # Update Historical Data
    update_payload = plan_operations.update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        values, attrs_clean, historical_context
    )
    execute_operations.patch_orion(historical_data_url, update_payload)

    # Send Alarm To Kafka
    historical_alarms_analysis = adjust_alarm_type(historical_alarms_analysis)
    historical_alarms = plan_operations.create_alarm_history(
        "Solution 1", alarm_type, attrs_clean, historical_alarms_analysis, periods_list, ack_list
    )
    historical_alarms = transform_operations.create_alarm_payloads(historical_alarms, context)
    execute_operations.produce_kafka(producer, kafka_topic, historical_alarms)

    # Get same old value from historical entity, apply pct_change in absolute and check threshold


@job
def process_steel(incoming_data, producer, service_config):
    # incoming_data, producer, service_config = unpack_data()

    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    elaborate_solution3(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)
