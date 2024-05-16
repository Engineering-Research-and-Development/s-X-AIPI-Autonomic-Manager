from dagster import op

from commons.utils import THRESHOLD_OK, update_data


@op
def compute_OCT_probe_status(status_list: list[str]) -> float:
    status = 1
    for status in status_list:
        if status != THRESHOLD_OK:
            status = 0
            break

    return float(status)


@op
def create_probe_status_payload(values: list[float],
                                names: list[str],
                                payload_context: str) -> dict:

    return update_data(values, names, payload_context)
