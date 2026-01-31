import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import boto3
from snow_checker import load_model, load_cameras, check_cameras, format_report, format_html_report

SES_SENDER = "ryanhoffman2445@gmail.com"
SES_RECIPIENT = "ryanhoffman2445@gmail.com"
AWS_REGION = "us-west-2"


def send_ses_email(results):
    ses = boto3.client("ses", region_name=AWS_REGION)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Snow on Road Report"
    msg["From"] = SES_SENDER
    msg["To"] = SES_RECIPIENT

    html_body = format_html_report(results)
    msg.attach(MIMEText(html_body, "html"))

    for result in results:
        if not result["error"] and result.get("image_bytes"):
            img = MIMEImage(result["image_bytes"])
            img.add_header("Content-ID", f"<camera_{result['id']}>")
            img.add_header("Content-Disposition", "inline", filename=f"camera_{result['id']}.jpg")
            msg.attach(img)

    ses.send_raw_email(
        Source=SES_SENDER,
        Destinations=[SES_RECIPIENT],
        RawMessage={"Data": msg.as_string()},
    )


def handler(event, context):
    model, preprocess, text, device = load_model()
    cameras = load_cameras()
    results = check_cameras(model, preprocess, text, device, cameras["mt_rose"])

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        send_ses_email(results)
    else:
        print(format_report(results))

    # Strip image_bytes before returning JSON (not serializable and large)
    results_json = [
        {k: v for k, v in r.items() if k != "image_bytes"} for r in results
    ]
    return {"statusCode": 200, "body": json.dumps(results_json)}
