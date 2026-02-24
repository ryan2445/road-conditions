import json
import os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any
from datetime import datetime, timezone

import boto3

from road_analysis import (
    CameraResult,
    check_cameras,
    generate_email,
    format_report,
    load_cameras,
    load_provider,
)

SES_SENDER = "ryanhoffman2445@gmail.com"
SES_RECIPIENT = "ryanhoffman2445@gmail.com"
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")


def send_ses_email(results: list[CameraResult]) -> None:
    ses = boto3.client("ses", region_name=AWS_REGION)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Road Analysis"
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


def upload_data_to_s3(results: list[CameraResult]):
    """Upload JSON data and images to S3 for the Svelte frontend."""
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        return

    s3 = boto3.client("s3", region_name=AWS_REGION)
    cloudfront = boto3.client("cloudfront", region_name=AWS_REGION)
    timestamp = datetime.now(timezone.utc).isoformat()

    cameras_data = []
    for result in results:
        camera_data = {
            "id": result["id"],
            "name": result["name"],
            "error": result["error"],
            "clearness_score": result.get("clearness_score"),
            "image_url": f"images/{result['id']}.jpg" if not result["error"] else None,
        }
        cameras_data.append(camera_data)

        # Upload image if available
        image_bytes = result.get("image_bytes")
        if not result["error"] and image_bytes:
            s3.put_object(
                Bucket=bucket,
                Key=f"images/{result['id']}.jpg",
                Body=image_bytes,
                ContentType="image/jpeg",
                CacheControl="public, max-age=0, s-maxage=3600, must-revalidate",
            )

    data = {
        "timestamp": timestamp,
        "cameras": cameras_data,
    }
    s3.put_object(
        Bucket=bucket,
        Key="data.json",
        Body=json.dumps(data).encode("utf-8"),
        ContentType="application/json",
        CacheControl="public, max-age=0, s-maxage=3600, must-revalidate",
    )

    distribution_id = os.environ.get("CLOUDFRONT_DISTRIBUTION_ID")
    if distribution_id:
        cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                "Paths": {
                    "Quantity": 1,
                    "Items": ["/*"],
                },
                "CallerReference": timestamp,
            },
        )


def handler(_event: Any, _context: Any) -> dict[str, Any]:
    provider = load_provider()
    cameras = load_cameras()
    results = check_cameras(provider, cameras["mt_rose"])

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        # Upload data.json and images for Svelte frontend
        upload_data_to_s3(results)

        # Only send email if it's 9am PST = 5pm UTC = 17 hour
        # utc_now = datetime.now(timezone.utc)
        # if utc_now.hour == 17:
        #     send_ses_email(results)
    else:
        print(format_report(results))

    # Strip image_bytes before returning JSON (not serializable and large)
    results_json: list[dict[str, Any]] = [
        {k: v for k, v in r.items() if k != "image_bytes"} for r in results
    ]
    return {"statusCode": 200, "body": json.dumps(results_json)}
