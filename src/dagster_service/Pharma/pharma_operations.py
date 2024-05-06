from dagster import op, OpExecutionContext
from commons.utils import *


@op
def compute_OCT_probe_status(context: OpExecutionContext, status_list: list[str]) -> int:
    status = 1
    for status in status_list:
        if status != THRESHOLD_OK:
            status = 0
            break

    return status


@op
def create_probe_status_payload(context: OpExecutionContext,
                                values: list[float],
                                names: list[str],
                                payload_context: str) -> dict:

    return update_data(values, names, payload_context)
