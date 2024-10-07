from dagster import job, op
from kafka import KafkaProducer

from commons.analysis_operations import discriminate_thresholds, merge_thresholds, analyze_historical_data
from commons.execute_operations import produce_orion_multi_message, patch_orion, post_orion
from commons.monitor_operations import get_data_from_notification, get_data
from commons.plan_operations import create_alarm_threshold, create_output_entity, create_historical_entity, \
    update_historical_data
from commons.transform_operations import create_alarm_payloads, expand_threshold, retrieve_values_from_historical_data, \
    get_threshold_from_pct_range
from commons.utils import THRESHOLD_OK


def analyze_full_input(item: dict, incoming_data: dict):
    """
    Merges threshold from
    @param item:
    @param incoming_data:
    @return:
    """
    attrs = item["attrs"]
    lowers = item["lowers"]
    uppers = item["uppers"]
    mode = item["mode"]
    values, _ = get_data_from_notification(incoming_data, attrs)
    thresholds = discriminate_thresholds(lowers, uppers, values)

    # One or two values. If two values, the condition == 0 on second threshold is checked.
    # If condition is met, then delete last attribute (condition attr) and send alarm.
    if len(thresholds) == 2:
        thresholds = merge_thresholds([thresholds[0]], [thresholds[1]], mode)
        attrs.pop()
        lowers.pop()
        uppers.pop()
        values.pop()

    return thresholds, attrs, lowers, uppers, values


@op
def elaborate_solution1(incoming_data: dict, producer: KafkaProducer, service_config: dict):
    solution = "solution_1"

    # Sub Solution Sensor Alarms on first window
    if incoming_data['id'] != service_config["small_window"]:
        alarm_type = service_config[solution]["alarm_type"]
        inputs = service_config[solution]["inputs"]
        update_url = service_config['base_url'] + service_config['output_entity']
        context = incoming_data["@context"]

        output_entity = get_data(update_url)
        if output_entity == {}:
            out_entity = create_output_entity(service_config['output_entity'], context)
            patch_orion(update_url, out_entity)

        # Solution to check for thresholds with met conditions
        for _, item in inputs.items():
            thresholds, attrs, lowers, uppers, values = analyze_full_input(item, incoming_data)

            alarms = create_alarm_threshold("Solution 1", alarm_type, attrs, thresholds,
                                            values, lowers, uppers)

            payloads = create_alarm_payloads(alarms, context)
            produce_orion_multi_message(update_url, payloads)

    # Sub Solution for AI Retraining on second window
    if incoming_data['id'] != service_config["small_laboratory"]:
        alarm_type = service_config[solution]["alarm_type_AI"]
        attrs = service_config[solution]["inputs_AI"]
        uppers = service_config[solution]["upper_thresholds_AI"]
        lowers = service_config[solution]["lower_thresholds_AI"]
        context = incoming_data["@context"]
        update_url = service_config['base_url'] + service_config['output_entity']

        values, _ = get_data_from_notification(incoming_data, attrs)
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

    values, _ = get_data_from_notification(incoming_data, attrs)
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

    values, _ = get_data_from_notification(incoming_data, attrs)
    thresholds = discriminate_thresholds(lowers, uppers, values)
    alarms = create_alarm_threshold("Solution 4", alarm_type, attrs, thresholds,
                                    values, lowers, uppers)

    payloads = create_alarm_payloads(alarms, context)

    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)
    produce_orion_multi_message(update_url, payloads)

    # Coefficient Analysis
    alarm_type = service_config[solution]["alarm_type_coeff"]
    attrs_coeff = service_config[solution]["inputs_coeff"]
    pct_change = service_config[solution]["pct_change_coeff"]
    context = incoming_data["@context"]
    values_coeff, _ = get_data_from_notification(incoming_data, attrs_coeff)

    historical_data_url = service_config["base_url"] + service_config[solution]["historical_entity"]
    historical_data = get_data(historical_data_url)
    if historical_data == {}:
        new_entity = create_historical_entity(service_config[solution]["historical_entity"], attrs_coeff, context)
        post_orion(service_config["base_url"], new_entity)
        return

    periods_list, ack_list, previous_list, old_values, historical_context = (
        retrieve_values_from_historical_data(historical_data, attrs_coeff))

    pct_expand = expand_threshold(pct_change, len(attrs_coeff))
    lower_thresholds, upper_thresholds = get_threshold_from_pct_range(old_values, pct_expand)
    results_threshold = discriminate_thresholds(lower_thresholds, upper_thresholds, values_coeff)

    # Alarm Creation
    alarms = create_alarm_threshold("Solution 4", alarm_type, attrs_coeff, thresholds,
                                    values_coeff, lowers, uppers)
    payloads = create_alarm_payloads(alarms, context)
    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)
    produce_orion_multi_message(update_url, payloads)

    # Update Historical Data
    _, historical_current_status = analyze_historical_data(
        periods_list, ack_list, results_threshold, 0
    )
    update_payload = update_historical_data(
        historical_current_status, periods_list, ack_list, previous_list,
        values_coeff, attrs_coeff, historical_context
    )
    patch_orion(historical_data_url, update_payload)




    # AI Analysis
    alarm_type = service_config[solution]["alarm_type_AI"]
    attrs_ai = service_config[solution]["inputs_AI"]
    uppers_ai = service_config[solution]["upper_thresholds_AI"]
    lowers_ai = service_config[solution]["lower_thresholds_AI"]

    values_ai, _ = get_data_from_notification(incoming_data, attrs_ai)
    thresholds_ai = discriminate_thresholds(lowers_ai, uppers_ai, values_ai)
    alarms_ai = create_alarm_threshold("Solution 1", alarm_type, attrs_ai, thresholds_ai,
                                       values_ai, lowers_ai, uppers_ai)

    payloads_ai = create_alarm_payloads(alarms_ai, context)

    output_entity = get_data(update_url)
    if output_entity == {}:
        out_entity = create_output_entity(service_config['output_entity'], context)
        patch_orion(update_url, out_entity)
    produce_orion_multi_message(update_url, payloads_ai)


@job
def process_asphalt(incoming_data, producer, service_config):
    # SOLUTION 1
    elaborate_solution1(incoming_data, producer, service_config)

    # SOLUTION 2
    elaborate_solution2(incoming_data, producer, service_config)

    # SOLUTION 4
    elaborate_solution4(incoming_data, producer, service_config)
