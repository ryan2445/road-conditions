import logging
import re
import time
from io import BytesIO
from urllib.parse import urljoin

import av
import requests
from PIL import Image

from models import CameraConfig

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 30
MAX_REQUESTS_PER_MINUTE = 60
HLS_MAX_ATTEMPTS = 3
HLS_RETRY_DELAY_SECONDS = 1.0
JPEG_MAGIC_BYTES = b"\xff\xd8\xff"

_request_timestamps: list[float] = []
_session = requests.Session()


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
    """Fetch JPEG bytes for a camera from its HLS stream, falling back to a snapshot URL."""
    stream_url = camera.get("stream")
    fallback_url = camera.get("image")

    if stream_url:
        try:
            return fetch_hls_frame(stream_url, warn_on_final_error=bool(fallback_url))
        except (requests.RequestException, ValueError, av.FFmpegError) as error:
            if not fallback_url:
                raise
            logger.warning(
                "HLS fetch failed for camera %s (id=%s): %s; falling back to %s",
                camera["name"],
                camera["id"],
                error,
                fallback_url,
            )
            return fetch_snapshot_jpeg(fallback_url)

    snapshot_url = fallback_url or build_camera_image_url(camera["id"])
    logger.warning(
        "No stream URL configured for camera %s (id=%s); falling back to %s",
        camera["name"],
        camera["id"],
        snapshot_url,
    )
    return fetch_snapshot_jpeg(snapshot_url)


def build_camera_image_url(camera_id: str) -> str:
    return f"https://nvroads.com/map/Cctv/{camera_id}"


def fetch_hls_frame(master_playlist_url: str, *, warn_on_final_error: bool = False) -> bytes:
    """Fetch a single frame from an HLS stream as JPEG bytes."""
    for attempt in range(1, HLS_MAX_ATTEMPTS):
        try:
            return _fetch_hls_frame_once(master_playlist_url, warn_on_error=True)
        except requests.RequestException as error:
            if not _is_retryable_hls_error(error):
                raise
            logger.warning(
                "HLS request failed for %s (attempt %d/%d): %s; retrying in %.1fs",
                master_playlist_url,
                attempt,
                HLS_MAX_ATTEMPTS,
                error,
                HLS_RETRY_DELAY_SECONDS,
            )
            time.sleep(HLS_RETRY_DELAY_SECONDS)

    return _fetch_hls_frame_once(master_playlist_url, warn_on_error=warn_on_final_error)


def _fetch_hls_frame_once(master_playlist_url: str, *, warn_on_error: bool = False) -> bytes:
    master_playlist = fetch_url_text(master_playlist_url, warn_on_error=warn_on_error)
    chunklist_path = _match_playlist_entries(
        master_playlist,
        r"^(chunklist[^\s]+\.m3u8)",
        "chunklist",
    )[0]
    chunklist_url = urljoin(master_playlist_url, chunklist_path)

    chunklist = fetch_url_text(chunklist_url, warn_on_error=warn_on_error)
    # Pick the newest segment in the sliding window so it is least likely to expire mid-fetch.
    segment_path = _match_playlist_entries(
        chunklist,
        r"^(media[^\s]+\.ts)",
        "media segment",
    )[-1]
    segment_url = urljoin(chunklist_url, segment_path)
    return decode_ts_segment_to_jpeg(fetch_url_bytes(segment_url, warn_on_error=warn_on_error))


def _is_retryable_hls_error(error: requests.RequestException) -> bool:
    if isinstance(error, requests.HTTPError):
        status_code = error.response.status_code if error.response is not None else None
        return status_code == 404 or (status_code is not None and status_code >= 500)
    return True


def _fetch_response(url: str, *, warn_on_error: bool = False) -> requests.Response:
    _rate_limit()
    try:
        response = _session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        if warn_on_error:
            logger.warning("NV Roads API request failed for %s: %s", url, error)
        else:
            logger.error("NV Roads API request failed for %s: %s", url, error)
        raise


def fetch_url_text(url: str, *, warn_on_error: bool = False) -> str:
    return _fetch_response(url, warn_on_error=warn_on_error).text


def fetch_url_bytes(url: str, *, warn_on_error: bool = False) -> bytes:
    return _fetch_response(url, warn_on_error=warn_on_error).content


def fetch_snapshot_jpeg(url: str) -> bytes:
    """Fetch a static camera snapshot and reject non-JPEG error placeholders."""
    response = _fetch_response(url)
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if content_type not in {"image/jpeg", "image/jpg"} or not response.content.startswith(
        JPEG_MAGIC_BYTES
    ):
        raise ValueError(f"Snapshot at {url} is not a valid JPEG (Content-Type={content_type!r})")
    return response.content


def decode_ts_segment_to_jpeg(segment_bytes: bytes) -> bytes:
    output = BytesIO()
    container = av.open(BytesIO(segment_bytes), format="mpegts", mode="r")
    try:
        for frame in container.decode(video=0):
            image = frame.to_image()
            if not isinstance(image, Image.Image):
                raise ValueError("Decoded frame is not a PIL image")
            image.save(output, format="JPEG", quality=75)
            return output.getvalue()
    finally:
        container.close()

    raise ValueError("Could not decode any frames from HLS segment")


def _match_playlist_entries(playlist_text: str, pattern: str, label: str) -> list[str]:
    matches = re.findall(pattern, playlist_text, re.MULTILINE)
    if not matches:
        raise ValueError(f"Could not find {label} in playlist")
    return matches
