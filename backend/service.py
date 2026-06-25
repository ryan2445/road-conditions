import logging

from config import load_cameras
from camera_sources import fetch_camera_image
from models import CameraConfig, CameraResult


def collect_camera_results(
    cameras: list[CameraConfig],
) -> list[CameraResult]:
    results: list[CameraResult] = []

    for camera in cameras:
        logging.info("Fetching camera: %s (id=%s)", camera["name"], camera["id"])
        image_result = _fetch_camera_result(camera)
        if image_result["error"]:
            results.append(image_result)
            continue

        image_bytes = image_result.get("image_bytes")
        if not image_bytes:
            results.append(_error_result(camera, "no image data"))
            continue

        results.append(
            {
                "id": camera["id"],
                "name": camera["name"],
                "error": False,
                "image_bytes": image_bytes,
            }
        )

    return results


GroupedResults = dict[str, list[CameraResult]]


def run_camera_analysis(group: str | None = None) -> GroupedResults:
    logging.info("Loading camera configurations...")
    cameras_by_group = load_cameras()
    if group:
        return {group: collect_camera_results(cameras_by_group[group])}
    return {
        name: collect_camera_results(cameras)
        for name, cameras in cameras_by_group.items()
    }


def _fetch_camera_result(camera: CameraConfig) -> CameraResult:
    try:
        image_bytes = fetch_camera_image(camera)
    except Exception as error:
        return _error_result(camera, f"image fetch failed: {error}")

    return {
        "id": camera["id"],
        "name": camera["name"],
        "error": False,
        "image_bytes": image_bytes,
    }


def _error_result(camera: CameraConfig, message: str) -> CameraResult:
    return {
        "id": camera["id"],
        "name": camera["name"],
        "error": True,
        "error_message": message,
    }

