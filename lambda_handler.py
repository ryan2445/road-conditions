import json
import os
import boto3
from snow_checker import load_model, load_cameras, check_cameras, format_report

SES_SENDER = "ryanhoffman2445@gmail.com"
SES_RECIPIENT = "ryanhoffman2445@gmail.com"
AWS_REGION = "us-west-2"


def send_ses_email(report):
    ses = boto3.client("ses", region_name=AWS_REGION)
    ses.send_email(
        Source=SES_SENDER,
        Destination={"ToAddresses": [SES_RECIPIENT]},
        Message={
            "Subject": {"Data": "Snow on Road Report"},
            "Body": {"Text": {"Data": report}},
        },
    )


def handler(event, context):
    model, preprocess, text, device = load_model()
    cameras = load_cameras()
    results = check_cameras(model, preprocess, text, device, cameras["mt_rose"])
    report = format_report(results)

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        send_ses_email(report)
    else:
        print(report)

    return {"statusCode": 200, "body": json.dumps(results)}
