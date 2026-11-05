import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3

from models import CameraResult, RoadConditionAlert
from reporting import format_group_name

logger = logging.getLogger(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")

GroupedResults = dict[str, list[CameraResult]]


def delete_stale_s3_images(s3_client: Any, bucket: str, active_keys: set[str]) -> None:
    """Removes any images under the images/ prefix in S3 that are not in active_keys."""
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        stale_objects: list[dict[str, str]] = []

        for page in paginator.paginate(Bucket=bucket, Prefix="images/"):
            for obj in page.get("Contents", []):
                key = obj.get("Key")
                if key and not key.endswith("/") and key not in active_keys:
                    stale_objects.append({"Key": key})

        if not stale_objects:
            logger.info("No stale images found in S3 to delete.")
            return

        for i in range(0, len(stale_objects), 1000):
            chunk = stale_objects[i : i + 1000]
            s3_client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": chunk},
            )
        logger.info("Deleted %d stale image(s) from S3.", len(stale_objects))
    except Exception as err:
        logger.warning("Failed to clean up stale images from S3: %s", err)


def upload_data_to_s3(
    grouped_results: GroupedResults,
    road_conditions: dict[str, list[RoadConditionAlert]] | None = None,
) -> None:
    """Upload JSON data and images to S3 for the Svelte frontend, removing stale images."""
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        return

    s3 = boto3.client("s3", region_name=AWS_REGION)
    cloudfront = boto3.client("cloudfront", region_name=AWS_REGION)
    timestamp = datetime.now(timezone.utc).isoformat()

    uploaded_keys: set[str] = set()
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

            image_key = f"images/{result['id']}.jpg"
            s3.put_object(
                Bucket=bucket,
                Key=image_key,
                Body=image_bytes,
                ContentType="image/jpeg",
            )
            uploaded_keys.add(image_key)

        group_entry: dict[str, Any] = {
            "name": format_group_name(group_name),
            "cameras": cameras_data,
        }
        alerts = (road_conditions or {}).get(group_name, [])
        if alerts:
            group_entry["alerts"] = alerts
        groups_data.append(group_entry)

    delete_stale_s3_images(s3, bucket, uploaded_keys)

    s3.put_object(
        Bucket=bucket,
        Key="data.json",
        Body=json.dumps({"timestamp": timestamp, "groups": groups_data}).encode(
            "utf-8"
        ),
        ContentType="application/json",
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
