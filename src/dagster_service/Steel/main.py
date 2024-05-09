import numpy as np
from kafka import KafkaProducer

from commons import (monitor_operations,
                     analysis_operations,
                     transform_operations,
                     plan_operations,
                     execute_operations)
from dagster import job, multi_asset, AssetOut, Output, op

from commons.utils import update_data


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
                               solution: str,
                               alarm_type: str,
                               kafka_topic: str
                               ):

    LOWER_THRESHOLD_MAX = 0.0
    UPPER_THRESHOLD_MAX = np.inf
    values_max = monitor_operations.get_data_from_notification(incoming_data, attrs_max)
    lower_threshold_max = transform_operations.expand_threshold(LOWER_THRESHOLD_MAX, len(values_max))
    upper_threshold_max = transform_operations.expand_threshold(UPPER_THRESHOLD_MAX, len(values_max))
    results_max = analysis_operations.discriminate_thresholds(lower_threshold_max, upper_threshold_max, values_max)

    values_zeros = monitor_operations.get_data_from_notification(incoming_data, attrs_zeros)
    values_nrheats = monitor_operations.get_data_from_notification(incoming_data, nr_heats)
    upper_threshold_nrheats = transform_operations.expand_threshold(values_nrheats, len(values_zeros))
    lower_threshold_nrheats = transform_operations.expand_threshold(-1, len(values_zeros))
    results_nrheats = analysis_operations.discriminate_thresholds(
        lower_threshold_nrheats, upper_threshold_nrheats, values_zeros)

    results_threshold = analysis_operations.merge_thresholds_and(results_max, results_nrheats)

    historical_data = monitor_operations.get_data(historical_data_url)
    periods_list, ack_list, previous_list, historical_context = (
        transform_operations.retrieve_values_from_historical_data(historical_data))
    #TODO CONTINUA


    pass


@op
def elaborate_solution1(incoming_data, producer, service_config):

    kafka_topic = service_config["kafka_topic"]

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




def elaborate_solution2(incoming_data, producer, service_config):
    pass


def elaborate_solution3(incoming_data, producer, service_config):
    pass


def elaborate_solution4(incoming_data, producer, service_config):
    pass


@job
def process_steel(incoming_data, producer, service_config):
    #incoming_data, producer, service_config = unpack_data()

    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 3
    elaborate_solution3(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)
