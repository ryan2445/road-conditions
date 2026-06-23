import re
import time
from io import BytesIO
from urllib.parse import urljoin

import av
import requests
from PIL import Image

from models import CameraConfig

REQUEST_TIMEOUT_SECONDS = 30
MAX_REQUESTS_PER_MINUTE = 60

_request_timestamps: list[float] = []


def _rate_limit() -> None:
    """Block until we can make a request within the rate limit."""
    now = time.monotonic()
    # Remove timestamps older than 60 seconds
    while _request_timestamps and now - _request_timestamps[0] >= 60:
        _request_timestamps.pop(0)
    if len(_request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        sleep_time = 60 - (now - _request_timestamps[0])
        if sleep_time > 0:
            time.sleep(sleep_time)
        _request_timestamps.pop(0)
    _request_timestamps.append(time.monotonic())


def fetch_camera_image(camera: CameraConfig) -> bytes:
    stream_url = camera.get("stream")
    if stream_url:
        return fetch_hls_frame(stream_url)

    return fetch_url_bytes(build_camera_image_url(camera["id"]))


def build_camera_image_url(camera_id: str) -> str:
    return f"https://nvroads.com/map/Cctv/{camera_id}"


def fetch_hls_frame(master_playlist_url: str) -> bytes:
    """Fetch a single frame from an HLS stream as JPEG bytes."""
    master_playlist = fetch_url_text(master_playlist_url)
    chunklist_path = _match_playlist_entry(
        master_playlist,
        r"^(chunklist[^\s]+\.m3u8)",
        "chunklist",
    )
    chunklist_url = urljoin(master_playlist_url, chunklist_path)

    chunklist = fetch_url_text(chunklist_url)
    segment_path = _match_playlist_entry(
        chunklist,
        r"^(media[^\s]+\.ts)",
        "media segment",
    )
    segment_url = urljoin(chunklist_url, segment_path)
    return decode_ts_segment_to_jpeg(fetch_url_bytes(segment_url))


def fetch_url_text(url: str) -> str:
    _rate_limit()
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def fetch_url_bytes(url: str) -> bytes:
    _rate_limit()
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.content


def decode_ts_segment_to_jpeg(segment_bytes: bytes) -> bytes:
    output = BytesIO()
    container = av.open(BytesIO(segment_bytes), format="mpegts")
    try:
        for frame in container.decode(video=0):  # type: ignore[misc]
            image = frame.to_image()
            if not isinstance(image, Image.Image):
                raise ValueError("Decoded frame is not a PIL image")
            image.save(output, format="JPEG", quality=75)
            return output.getvalue()
    finally:
        container.close()

    raise ValueError("Could not decode any frames from HLS segment")


def _match_playlist_entry(playlist_text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, playlist_text, re.MULTILINE)
    if match is None:
        raise ValueError(f"Could not find {label} in playlist")
    return match.group(1)
