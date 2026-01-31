import json
import os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import boto3

from snow_checker import (
    CameraResult,
    check_cameras,
    generate_email,
    generate_web_page,
    format_report,
    load_cameras,
    load_model,
)

SES_SENDER = "ryanhoffman2445@gmail.com"
SES_RECIPIENT = "ryanhoffman2445@gmail.com"
AWS_REGION = "us-west-2"


def send_ses_email(results: list[CameraResult]) -> None:
    ses = boto3.client("ses", region_name=AWS_REGION)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Snow on Road Report"
    msg["From"] = SES_SENDER
    msg["To"] = SES_RECIPIENT

    html_body = generate_email(results)
    msg.attach(MIMEText(html_body, "html"))

    for result in results:
        image_bytes = result.get("image_bytes")
        if not result["error"] and image_bytes:
            img = MIMEImage(image_bytes)
            img.add_header("Content-ID", f"<camera_{result['id']}>")
            img.add_header(
                "Content-Disposition", "inline", filename=f"camera_{result['id']}.jpg"
            )
            msg.attach(img)

    ses.send_raw_email(
        Source=SES_SENDER,
        Destinations=[SES_RECIPIENT],
        RawMessage={"Data": msg.as_string()},
    )


def upload_html_to_s3(results: list[CameraResult]) -> str | None:
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        return None

    s3 = boto3.client("s3", region_name=AWS_REGION)
    html = generate_web_page(results)

    s3.put_object(
        Bucket=bucket,
        Key="index.html",
        Body=html.encode("utf-8"),
        ContentType="text/html",
    )

    return f"http://{bucket}.s3-website-{AWS_REGION}.amazonaws.com"


def handler(event: Any, _context: Any) -> dict[str, Any]:
    model, preprocess, text, device = load_model()
    cameras = load_cameras()
    results = check_cameras(model, preprocess, text, device, cameras["mt_rose"])

    s3_url = None
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        # Always upload HTML to S3
        s3_url = upload_html_to_s3(results)

        # Only send email if action is "email" (9am trigger)
        if event.get("action") == "email":
            send_ses_email(results)
    else:
        print(format_report(results))

    # Strip image_bytes before returning JSON (not serializable and large)
    results_json: list[dict[str, Any]] = [
        {k: v for k, v in r.items() if k != "image_bytes"} for r in results
    ]
    return {"statusCode": 200, "body": json.dumps(results_json), "s3_url": s3_url}
