import json
import logging
import re
from pathlib import Path
import requests

from models import CameraConfig

logger = logging.getLogger(__name__)

DEFAULT_CAMERA_PATH = Path(__file__).with_name("cameras.json")
NVROADS_CAMERAS_URL = "https://www.nvroads.com/List/GetData/Cameras"


def load_cameras_from_json(
    path: str | Path = DEFAULT_CAMERA_PATH,
) -> dict[str, list[CameraConfig]]:
    """Loads the hardcoded cameras from cameras.json file."""
    with Path(path).open() as file:
        return json.load(file)  # type: ignore[no-any-return]


def load_cameras(
    path: str | Path = DEFAULT_CAMERA_PATH,
) -> dict[str, list[CameraConfig]]:
    # try:
    #     logger.info("Dynamically fetching cameras from NV Roads API...")
    #     cameras = fetch_live_cameras()
    #     grouped = group_cameras(cameras)

    #     # Ensure we got some cameras in our main groups
    #     if any(grouped.values()):
    #         logger.info(
    #             "Successfully fetched and grouped cameras dynamically: mt_rose=%d, washoe_lake=%d, south_reno=%d",
    #             len(grouped["mt_rose"]), len(grouped["washoe_lake"]), len(grouped["south_reno"])
    #         )
    #         return grouped
    #     else:
    #         logger.warning("Dynamic fetching returned 0 categorized cameras, falling back to cameras.json")
    # except Exception as err:
    #     logger.warning("Failed to dynamically fetch cameras (error: %s), falling back to cameras.json", err)

    return load_cameras_from_json(path)


def fetch_live_cameras() -> list[dict]:
    """Fetches all cameras from the NV Roads List endpoint using pagination."""
    cameras = []
    start = 0
    length = 100

    while True:
        payload = {
            "draw": "1",
            "start": str(start),
            "length": str(length),
            "columns[0][data]": "Id",
            "columns[0][name]": "Id",
            "columns[0][searchable]": "true",
            "order[0][column]": "0",
            "order[0][dir]": "asc",
        }

        resp = requests.post(NVROADS_CAMERAS_URL, data=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        records = data.get("data", [])
        if not records:
            break

        cameras.extend(records)
        if len(records) < length:
            break

        start += length

    return cameras


def group_cameras(cameras: list[dict]) -> dict[str, list[CameraConfig]]:
    """Filters, deduplicates, and groups live NV Roads cameras into our target routes."""
    groups: dict[str, list[CameraConfig]] = {
        "mt_rose": [],
        "washoe_lake": [],
        "south_reno": [],
    }

    # Tracking to prevent duplicates (by stream URL)
    stream_to_best_camera: dict[str, dict] = {}

    for cam in cameras:
        # Get roadway name
        roadway = cam.get("roadway") or ""

        # Get HLS stream url from images
        images = cam.get("images") or []
        if not images:
            continue
        stream_url = images[0].get("videoUrl") or ""
        if not stream_url or not stream_url.endswith(".m3u8"):
            continue

        # Parse coordinates to determine geography
        wkt = cam.get("latLng", {}).get("geography", {}).get("wellKnownText") or ""
        m = re.search(r"POINT \(([^ ]+) ([^ ]+)\)", wkt)
        if not m:
            continue
        try:
            lat = float(m.group(2))
        except ValueError:
            continue

        # Classify which group this camera belongs to
        road_upper = roadway.upper()
        group_key = None

        if "I580" in road_upper or "I-580" in road_upper:
            if lat >= 39.39:
                group_key = "south_reno"
            else:
                group_key = "washoe_lake"
        elif "SR431" in road_upper or "SR-431" in road_upper:
            group_key = "mt_rose"
        elif "MCCARRAN" in road_upper:
            group_key = "south_reno"
        elif "SR341" in road_upper or "SR-341" in road_upper:
            group_key = "south_reno"

        if not group_key:
            continue

        # Keep track of the camera configuration
        source_id = str(cam.get("sourceId") or "")

        cam_info = {
            "id": source_id,
            "name": roadway,
            "stream": stream_url,
            "group": group_key,
        }

        # Deduplication logic: if we see the same stream URL twice,
        # prefer the numeric sourceId over the alphanumeric hash string.
        existing = stream_to_best_camera.get(stream_url)
        if existing:
            # If the current one is numeric but the existing is alphanumeric, replace it.
            if source_id.isdigit() and not existing["id"].isdigit():
                stream_to_best_camera[stream_url] = cam_info
        else:
            stream_to_best_camera[stream_url] = cam_info

    # Place the chosen deduplicated cameras into their respective groups
    for cam_info in stream_to_best_camera.values():
        group_key = cam_info["group"]
        groups[group_key].append(
            {
                "id": cam_info["id"],
                "name": cam_info["name"],
                "stream": cam_info["stream"],
            }
        )

    # Sort cameras within each group by name or ID to maintain stable ordering
    for group_key in groups:
        groups[group_key].sort(key=lambda c: c["name"])

    return groups
