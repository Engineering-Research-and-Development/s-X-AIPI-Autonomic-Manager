import numpy as np
from kafka import KafkaProducer
from dagster import job, op

from commons.analysis_operations import discriminate_thresholds, merge_thresholds, \
    analyze_historical_data
from commons.execute_operations import produce_kafka, patch_orion
from commons.monitor_operations import get_data_from_notification, get_data
from commons.plan_operations import create_alarm_threshold, update_historical_data, \
    create_alarm_history, \
    create_historical_entity
from commons.transform_operations import expand_threshold, retrieve_values_from_historical_data, \
    create_alarm_payloads, get_threshold_values_from_entity, get_threshold_from_pct_range

from commons.execute_operations import post_orion


def clean_names(names: [str]):
    new_names = [name.split("_zero")[0] if "_zero" in name else name for name in names]
    return new_names


def adjust_alarm_type(alarms: [str]):
    new_names = ["Material Introduction Detection" if "Good" in alarm else "Material Removal Detection" for alarm in
                 alarms]
    return new_names


@op
def sub_solution_check_zero_nans(incoming_data: dict,
                                 producer: KafkaProducer,
                                 service_config: dict,
                                 attrs_name: str,
                                 solution: str,
                                 lower_threshold: str,
                                 upper_threshold: str,
                                 alarm_type_name: str,
                                 kafka_topic: str):
    """
    Check for zero or NaN values in the incoming data and trigger alarms accordingly for the specified solution.

    @param incoming_data: Dictionary containing incoming data.
    @param producer: KafkaProducer instance used for producing messages.
    @param service_config: Dictionary containing configuration for the service.
    @param attrs_name: Name of the attribute list in the service configuration.
    @param solution: Name of the solution to be checked.
    @param lower_threshold: Name of the lower threshold in the service configuration.
    @param upper_threshold: Name of the upper threshold in the service configuration.
    @param alarm_type_name: Name of the alarm type in the service configuration.
    @param kafka_topic: Kafka topic to produce messages to.

    @return: None
    """

    attrs = service_config[solution][attrs_name]
    alarm_type = alarm_type_name
    context = incoming_data["@context"]

    values, metadata = get_data_from_notification(incoming_data, attrs)
    upper_thresholds = expand_threshold(service_config[solution][upper_threshold], len(values))
    lower_thresholds = expand_threshold(service_config[solution][lower_threshold], len(values))
    results = discriminate_thresholds(lower_thresholds, upper_thresholds, values)
    payloads_zeros = create_alarm_threshold("Solution 1", alarm_type, attrs, results, values,
                                            lower_thresholds, upper_thresholds)
    payloadas_alarms = create_alarm_payloads(payloads_zeros, context, metadata)
    produce_kafka(producer, kafka_topic, payloadas_alarms)


@op
def sub_solution_material_used(incoming_data: dict,
                               producer: KafkaProducer,
                               service_config: dict,
                               historical_data_key: str,
                               attrs_max_name: str,
                               attrs_zeros_name: str,
                               nr_heats_name: str,
                               patience: int,
                               solution: str,
                               alarm_type: str,
                               kafka_topic: str
                               ):
    """
    Check material usage for a sub-solution, analyze historical data, and send alarms to Kafka.

    @param incoming_data: Dictionary containing incoming data.
    @param producer: KafkaProducer instance used for producing messages.
    @param service_config: Dictionary containing configuration for the service.
    @param historical_data_url: URL for retrieving historical data.
    @param attrs_max_name: Name of the attributes representing maximum value for a material in current period.
    @param attrs_zeros_name: Name of the attributes representing number of zero values for a material in current period.
    @param nr_heats_name: Name of the attribute representing number of heats in the analyzed period.
    @param patience: Number of periods to wait before raising an alarm.
    @param solution: Name of the solution.
    @param alarm_type: Type of the alarm to be sent.
    @param kafka_topic: Kafka topic to produce messages to.

    @return: None
    """

    historical_data_url = service_config["base_url"] + service_config["solution_1"][historical_data_key]

    attrs_zeros = service_config[solution][attrs_zeros_name]
    attrs_max = service_config[solution][attrs_max_name]
    nr_heats = service_config[solution][nr_heats_name]

    # Setting useful values
    lower_threshold_max = [-999999.9]
    upper_threshold_max = service_config[solution]['scapmax_lower']
    context = incoming_data["@context"]

    # Checking rules for max content values
    values_max, _ = get_data_from_notification(incoming_data, attrs_max)
    lower_threshold_max = expand_threshold(lower_threshold_max, len(values_max))
    upper_threshold_max = expand_threshold(upper_threshold_max, len(values_max))
    results_max = discriminate_thresholds(lower_threshold_max, upper_threshold_max, values_max)

    # Checking rules for number of zeros
    values_zeros, metadata = get_data_from_notification(incoming_data, attrs_zeros)
    values_nrheats, _ = get_data_from_notification(incoming_data, nr_heats)
    upper_threshold_nrheats = expand_threshold([999999.9], len(values_zeros))
    lower_threshold_nrheats = expand_threshold(values_nrheats, len(values_zeros))
    results_nrheats = discriminate_thresholds(
        lower_threshold_nrheats, upper_threshold_nrheats, values_zeros)

    # Merging rules from two sources
    results_threshold = merge_thresholds(results_max, results_nrheats, "X_AND_Y")

    # Retrieving the data from historical storage
    attrs_clean = clean_names(attrs_zeros)
    historical_data = get_data(historical_data_url)
    if historical_data == {}:
        new_entity = create_historical_entity(service_config[solution][historical_data_key], attrs_clean, context)
        post_orion(service_config["base_url"], new_entity)
        historical_data = get_data(historical_data_url)

    periods_list, ack_list, previous_list, old_values, historical_context = (
        retrieve_values_from_historical_data(historical_data, attrs_clean))

    # Analyze Historical Data
    historical_alarms_analysis, historical_current_status = analyze_historical_data(
        periods_list, ack_list, results_threshold, patience
    )

    # Update Historical Data
    mock_values = expand_threshold([0.0], len(values_zeros))

    update_payload = update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        mock_values, attrs_clean, historical_context
    )
    patch_orion(historical_data_url, update_payload)

    # Send Alarm To Kafka
    historical_alarms_analysis = adjust_alarm_type(historical_alarms_analysis)
    historical_alarms = create_alarm_history(
        "Solution 1", alarm_type, attrs_clean, historical_alarms_analysis, periods_list, ack_list
    )

    historical_alarms = create_alarm_payloads(historical_alarms, context, metadata)
    produce_kafka(producer, kafka_topic, historical_alarms)


@op
def elaborate_solution1(incoming_data, producer, service_config):
    if incoming_data['id'] != service_config["small_window"]:
        return

    solution = "solution_1"
    kafka_topic = service_config["kafka_topic"]
    alarm_type_materials = service_config[solution]["alarm_type_materials"]
    patience = service_config[solution]["historical_patience"]

    # Checking for zeros
    sub_solution_check_zero_nans(incoming_data, producer, service_config, "zeros_inputs", "solution_1",
                                 "zero_inputs_lower_threshold", "zero_inputs_upper_threshold", "alarm_type_zeros",
                                 kafka_topic)

    # Checking for NaNs
    sub_solution_check_zero_nans(incoming_data, producer, service_config, "nan_inputs", "solution_1",
                                 "nan_inputs_lower_threshold", "nan_inputs_upper_threshold", "alarm_type_nan",
                                 kafka_topic)

    # Checking first scrap group
    sub_solution_material_used(incoming_data, producer, service_config, "historical_entity_0",
                               "scrapmax_inputs_0", "scrapzeros_inputs_0", "nrheats_scrap", patience, "solution_1",
                               alarm_type_materials, kafka_topic)

    # Checking second scrap group
    sub_solution_material_used(incoming_data, producer, service_config, "historical_entity_1",
                               "scrapmax_inputs_1", "scrapzeros_inputs_1", "nrheats_scrap", patience, "solution_1",
                               alarm_type_materials, kafka_topic)

    # Checking lime content
    sub_solution_material_used(incoming_data, producer, service_config, "historical_entity_2",
                               "scrapmax_inputs_2", "scrapzeros_inputs_2", "nrheats_lime", patience, "solution_1",
                               alarm_type_materials, kafka_topic)

    # Checking lime content
    sub_solution_material_used(incoming_data, producer, service_config, "historical_entity_3",
                               "scrapmax_inputs_3", "scrapzeros_inputs_3", "nrheats_limecoke", patience, "solution_1",
                               alarm_type_materials, kafka_topic)


@op
def elaborate_solution2(incoming_data, producer, service_config):
    if incoming_data['id'] != service_config["small_window"]:
        return

    solution = "solution_2"
    attrs = service_config[solution]["inputs"]
    alarm_type = service_config[solution]["alarm_type"]
    kafka_topic = service_config["kafka_topic"]

    context = incoming_data["@context"]
    values, metadata = get_data_from_notification(incoming_data, attrs)
    upper_thresholds = service_config[solution]["thresholds"]
    lower_thresholds = expand_threshold([-999999.9], len(upper_thresholds))
    results_threshold = discriminate_thresholds(lower_thresholds, upper_thresholds, values)

    alarms = create_alarm_threshold(
        "Solution 2", alarm_type, attrs, results_threshold, values, lower_thresholds, upper_thresholds)
    payloads = create_alarm_payloads(alarms, context, metadata)
    produce_kafka(producer, kafka_topic, payloads)


@op
def elaborate_solution3(incoming_data, producer, service_config):
    if incoming_data['id'] != service_config["small_window"]:
        return

    solution = "solution_3"
    attrs = service_config[solution]["inputs"]
    pct_change = service_config[solution]["pct_change"]
    patience = service_config[solution]["historical_patience"]
    alarm_type = service_config[solution]["alarm_type"]
    kafka_topic = service_config["kafka_topic"]

    context = incoming_data["@context"]
    values, metadata = get_data_from_notification(incoming_data, attrs)
    threshold_names = service_config[solution]["thresholds"]
    pct_expand = expand_threshold(pct_change, len(attrs))
    _, threshold_high = get_threshold_values_from_entity(
        incoming_data, threshold_names, threshold_names)
    _, threshold_high = get_threshold_from_pct_range(threshold_high, pct_expand)
    results_threshold = discriminate_thresholds([-999999.9]*len(attrs), threshold_high, values)

    historical_data_url = service_config["base_url"] + service_config[solution]["historical_entity"]
    historical_data = get_data(historical_data_url)
    if historical_data == {}:
        new_entity = create_historical_entity(service_config[solution]["historical_entity"], attrs, context)
        post_orion(service_config["base_url"], new_entity)
        historical_data = get_data(historical_data_url)

    periods_list, ack_list, previous_list, old_values, historical_context = (
        retrieve_values_from_historical_data(historical_data, attrs))

    historical_alarms_analysis, historical_current_status = analyze_historical_data(
        periods_list, ack_list, results_threshold, patience
    )

    # Update Historical Data
    update_payload = update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        values, attrs, historical_context
    )
    patch_orion(historical_data_url, update_payload)

    # Send Alarm To Kafka
    historical_alarms = create_alarm_history(
        "Solution 3", alarm_type, attrs, historical_alarms_analysis, periods_list, ack_list
    )
    historical_alarms = create_alarm_payloads(historical_alarms, context, metadata)
    produce_kafka(producer, kafka_topic, historical_alarms)


@op
def elaborate_solution4_1(incoming_data, producer, service_config):
    if incoming_data['id'] != service_config["small_window"]:
        return

    solution = "solution_4"
    attrs = service_config[solution]["inputs"]
    pct_change = service_config[solution]["pct_change"]
    patience = service_config[solution]["historical_patience"]
    alarm_type = service_config[solution]["alarm_type"]
    kafka_topic = service_config["kafka_topic"]

    context = incoming_data["@context"]
    values, metadata = get_data_from_notification(incoming_data, attrs)

    historical_data_url = service_config["base_url"] + service_config[solution]["historical_entity"]
    historical_data = get_data(historical_data_url)
    attrs_clean = clean_names(attrs)
    if historical_data == {}:
        new_entity = create_historical_entity(service_config[solution]["historical_entity"], attrs_clean, context)
        post_orion(service_config["base_url"], new_entity)
        historical_data = get_data(historical_data_url)

    periods_list, ack_list, previous_list, old_values, historical_context = (
        retrieve_values_from_historical_data(historical_data, attrs_clean))

    pct_expand = expand_threshold(pct_change, len(attrs))
    lower_thresholds, upper_thresholds = get_threshold_from_pct_range(old_values, pct_expand)
    results_threshold = discriminate_thresholds(lower_thresholds, upper_thresholds, values)

    # Analyze Historical Data
    historical_alarms_analysis, historical_current_status = analyze_historical_data(
        periods_list, ack_list, results_threshold, patience
    )

    # Update Historical Data
    update_payload = update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        values, attrs_clean, historical_context
    )
    patch_orion(historical_data_url, update_payload)

    # Send Alarm To Kafka
    historical_alarms = create_alarm_history(
        "Solution 4", alarm_type, attrs_clean, historical_alarms_analysis, periods_list, ack_list
    )
    historical_alarms = create_alarm_payloads(historical_alarms, context, metadata)
    produce_kafka(producer, kafka_topic, historical_alarms)


@op
def elaborate_solution4_2(incoming_data, producer, service_config):
    if incoming_data['id'] != service_config["small_window"]:
        return

    solution = "solution_4"
    attrs = service_config[solution]["inputs_2"]
    pct_change = service_config[solution]["pct_change_2"]
    patience = service_config[solution]["historical_patience"]
    alarm_type = service_config[solution]["alarm_type_2"]
    kafka_topic = service_config["kafka_topic"]

    context = incoming_data["@context"]
    values, metadata = get_data_from_notification(incoming_data, attrs)
    threshold_names = service_config[solution]["thresholds_2"]
    pct_expand = expand_threshold(pct_change, len(attrs))
    _, threshold_high = get_threshold_values_from_entity(
        incoming_data, threshold_names, threshold_names)
    _, threshold_high = get_threshold_from_pct_range(threshold_high, pct_expand)
    results_threshold = discriminate_thresholds([-999999.9]*len(attrs), threshold_high, values)

    historical_data_url = service_config["base_url"] + service_config[solution]["historical_entity_2"]
    historical_data = get_data(historical_data_url)
    if historical_data == {}:
        new_entity = create_historical_entity(service_config[solution]["historical_entity_2"], attrs, context)
        post_orion(service_config["base_url"], new_entity)
        historical_data = get_data(historical_data_url)

    periods_list, ack_list, previous_list, old_values, historical_context = (
        retrieve_values_from_historical_data(historical_data, attrs))

    historical_alarms_analysis, historical_current_status = analyze_historical_data(
        periods_list, ack_list, results_threshold, patience
    )

    # Update Historical Data
    update_payload = update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        values, attrs, historical_context
    )
    patch_orion(historical_data_url, update_payload)

    # Send Alarm To Kafka
    historical_alarms = create_alarm_history(
        "Solution 4", alarm_type, attrs, historical_alarms_analysis, periods_list, ack_list
    )
    historical_alarms = create_alarm_payloads(historical_alarms, context, metadata)
    produce_kafka(producer, kafka_topic, historical_alarms)


@op
def alarm_redirection_wp3(incoming_data, producer, service_config):
    if incoming_data["id"] != service_config["wp3_alarms"]:
        return

    kafka_topic = service_config["kafka_wp3"]
    produce_kafka(producer, kafka_topic, [incoming_data])


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
    elaborate_solution4_1(incoming_data, producer, service_config)
    elaborate_solution4_2(incoming_data, producer, service_config)


    # Alarm redirection
    alarm_redirection_wp3(incoming_data, producer, service_config)
