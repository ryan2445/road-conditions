import json
import os
from typing import Any
import logging
import sys

from publishing import serialize_results, upload_data_to_s3
from reporting import format_report
from road_conditions import fetch_road_conditions
from service import run_camera_analysis


def handler(_event: Any, _context: Any) -> dict[str, Any]:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
    )
    logging.info("lambda handler invoked")
    grouped_results = run_camera_analysis()
    road_conditions = fetch_road_conditions()

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        upload_data_to_s3(grouped_results, road_conditions)
    else:
        print(format_report(grouped_results))

    return {"statusCode": 200, "body": json.dumps(serialize_results(grouped_results))}
