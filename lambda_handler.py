import json
import os
from typing import Any

from publishing import serialize_results, upload_data_to_s3
from reporting import format_report
from service import run_camera_analysis


def handler(_event: Any, _context: Any) -> dict[str, Any]:
    results = run_camera_analysis()

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        upload_data_to_s3(results)
    else:
        print(format_report(results))

    return {"statusCode": 200, "body": json.dumps(serialize_results(results))}
