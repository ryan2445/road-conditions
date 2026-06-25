import json
import os
from datetime import datetime, timezone
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import boto3

from models import CameraResult, RoadConditionAlert
from reporting import format_group_name, generate_email

AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
SES_SENDER = os.environ.get("SES_SENDER", "ryanhoffman2445@gmail.com")
SES_RECIPIENT = os.environ.get("SES_RECIPIENT", "ryanhoffman2445@gmail.com")

GroupedResults = dict[str, list[CameraResult]]


# Currently unused
def send_ses_email(grouped_results: GroupedResults) -> None:
    ses = boto3.client("ses", region_name=AWS_REGION)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Road Analysis"
    msg["From"] = SES_SENDER
    msg["To"] = SES_RECIPIENT

    html_body = generate_email(grouped_results)
    msg.attach(MIMEText(html_body, "html"))

    for results in grouped_results.values():
        for result in results:
            image_bytes = result.get("image_bytes")
            if result["error"] or image_bytes is None:
                continue

            img = MIMEImage(image_bytes)
            img.add_header("Content-ID", f"<camera_{result['id']}>")
            img.add_header(
                "Content-Disposition",
                "inline",
                filename=f"camera_{result['id']}.jpg",
            )
            msg.attach(img)

    ses.send_raw_email(
        Source=SES_SENDER,
        Destinations=[SES_RECIPIENT],
        RawMessage={"Data": msg.as_string()},
    )


def upload_data_to_s3(
    grouped_results: GroupedResults,
    road_conditions: dict[str, list[RoadConditionAlert]] | None = None,
) -> None:
    """Upload JSON data and images to S3 for the Svelte frontend."""
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        return

    s3 = boto3.client("s3", region_name=AWS_REGION)
    cloudfront = boto3.client("cloudfront", region_name=AWS_REGION)
    timestamp = datetime.now(timezone.utc).isoformat()

    groups_data = []
    for group_name, results in grouped_results.items():
        cameras_data = []
        for result in results:
            cameras_data.append(
                {
                    "id": result["id"],
                    "name": result["name"],
                    "error": result["error"],
                    "error_message": result.get("error_message"),
                    "image_url": (
                        f"images/{result['id']}.jpg" if not result["error"] else None
                    ),
                }
            )

            image_bytes = result.get("image_bytes")
            if result["error"] or image_bytes is None:
                continue

            s3.put_object(
                Bucket=bucket,
                Key=f"images/{result['id']}.jpg",
                Body=image_bytes,
                ContentType="image/jpeg",
                CacheControl="public, max-age=0, s-maxage=3600, must-revalidate",
            )

        group_entry: dict[str, Any] = {
            "name": format_group_name(group_name),
            "cameras": cameras_data,
        }
        alerts = (road_conditions or {}).get(group_name, [])
        if alerts:
            group_entry["alerts"] = alerts
        groups_data.append(group_entry)

    s3.put_object(
        Bucket=bucket,
        Key="data.json",
        Body=json.dumps({"timestamp": timestamp, "groups": groups_data}).encode(
            "utf-8"
        ),
        ContentType="application/json",
        CacheControl="public, max-age=0, s-maxage=3600, must-revalidate",
    )

    distribution_id = os.environ.get("CLOUDFRONT_DISTRIBUTION_ID")
    if distribution_id:
        cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                "Paths": {"Quantity": 1, "Items": ["/*"]},
                "CallerReference": timestamp,
            },
        )


def serialize_results(grouped_results: GroupedResults) -> dict[str, Any]:
    return {
        group_name: [
            {key: value for key, value in result.items() if key != "image_bytes"}
            for result in results
        ]
        for group_name, results in grouped_results.items()
    }
