import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict
from urllib.parse import urljoin
from PIL import Image

import av
import jinja2
import requests


class CameraConfig(TypedDict):
    id: str
    name: str
    stream: NotRequired[str]


class CameraResult(TypedDict):
    id: str
    name: str
    error: bool
    clearness_score: float | None
    image_bytes: NotRequired[bytes]


class AnalysisResult(TypedDict):
    clearness_score: float  # 0.0 (dangerous) to 1.0 (clear/dry)
    summary: str  # Brief text description


class VisionProvider(Protocol):
    def analyze_image(self, image_bytes: bytes) -> AnalysisResult: ...


ANALYSIS_PROMPT = """\
Analyze this traffic camera image and assess road conditions.

Return ONLY valid JSON with these fields:
- "clearness_score": a float from 0.0 to 1.0 where:
    1.0 = completely clear, dry pavement, perfect driving conditions
    0.8 = mostly clear with minor wet spots or light haze
    0.6 = somewhat clear but noticeably wet, light rain, or thin snow on shoulders
    0.4 = partially covered with snow/ice, moderate rain, or reduced visibility
    0.2 = mostly snow/ice-covered, heavy precipitation, or very low visibility
    0.0 = fully impassable, whiteout conditions, or completely snow/ice-covered
- "summary": a brief one-sentence description of the road conditions

Example response:
{"clearness_score": 0.85, "summary": "Dry pavement with clear skies and good visibility."}
"""


def load_provider() -> "VisionProvider":
    """Instantiate a vision provider based on the VISION_PROVIDER env var."""
    name = os.environ.get("VISION_PROVIDER", "gemini").lower()
    if name == "claude":
        from providers import ClaudeProvider

        return ClaudeProvider()
    elif name == "openai":
        from providers import OpenAIProvider

        return OpenAIProvider()
    elif name == "gemini":
        from providers import GeminiProvider

        return GeminiProvider()
    else:
        raise ValueError(f"Unknown vision provider: {name}")


def load_cameras(path: str = "cameras.json") -> dict[str, list[CameraConfig]]:
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]


def fetch_hls_frame(master_playlist_url: str) -> bytes:
    """Fetch a single frame from an HLS stream as JPEG bytes."""
    # 1. Fetch master playlist and find chunklist URL
    master_response = requests.get(master_playlist_url)
    master_response.raise_for_status()

    chunklist_match = re.search(
        r"^(chunklist[^\s]+\.m3u8)", master_response.text, re.MULTILINE
    )
    if not chunklist_match:
        raise ValueError("Could not find chunklist in master playlist")
    chunklist_url = urljoin(master_playlist_url, chunklist_match.group(1))

    # 2. Fetch chunklist and find first .ts segment
    chunklist_response = requests.get(chunklist_url)
    chunklist_response.raise_for_status()

    segment_match = re.search(
        r"^(media[^\s]+\.ts)", chunklist_response.text, re.MULTILINE
    )
    if not segment_match:
        raise ValueError("Could not find media segment in chunklist")
    segment_url = urljoin(chunklist_url, segment_match.group(1))

    # 3. Fetch .ts segment and decode first frame with PyAV
    segment_response = requests.get(segment_url)
    segment_response.raise_for_status()

    output = BytesIO()
    container = av.open(BytesIO(segment_response.content), format="mpegts")
    for frame in container.decode(video=0):  # type: ignore
        image = frame.to_image()  # type: Image.Image
        image.save(output, format="JPEG", quality=75)
        break
    container.close()

    return output.getvalue()


def check_cameras(
    provider: VisionProvider,
    cameras: list[CameraConfig],
) -> list[CameraResult]:
    results: list[CameraResult] = []

    for camera in cameras:
        camera_id = camera["id"]
        camera_name = camera["name"]
        stream_url = camera.get("stream")

        # Fetch image
        try:
            if stream_url:
                image_bytes = fetch_hls_frame(stream_url)
            else:
                url = f"https://nvroads.com/map/Cctv/{camera_id}"
                response = requests.get(url)
                response.raise_for_status()
                image_bytes = response.content
        except Exception as e:
            print(f"Error fetching image for camera {camera_id} ({camera_name}): {e}")
            results.append(
                {
                    "id": camera_id,
                    "name": camera_name,
                    "error": True,
                    "clearness_score": None,
                }
            )
            continue

        # Analyze image
        try:
            # analysis = provider.analyze_image(image_bytes)
            # print(
            #     f"  {camera_name}: {analysis['clearness_score']:.0%} - {analysis['summary']}"
            # )
            results.append(
                {
                    "id": camera_id,
                    "name": camera_name,
                    "error": False,
                    "clearness_score": None,
                    "image_bytes": image_bytes,
                }
            )
        except Exception as e:
            print(f"Error analyzing image for camera {camera_id} ({camera_name}): {e}")
            results.append(
                {
                    "id": camera_id,
                    "name": camera_name,
                    "error": True,
                    "clearness_score": None,
                }
            )

    return results


def format_report(results: list[CameraResult]) -> str:
    lines: list[str] = []
    header = f"{'ID':<8} {'Name':<30} {'Road Clear':<12}"
    lines.append(header)
    lines.append("-" * len(header))

    for result in results:
        if result["error"]:
            lines.append(f"{result['id']:<8} {result['name']:<30} {'Error':<12}")
        else:
            score = result["clearness_score"]
            lines.append(
                f"{result['id']:<8} {result['name']:<30} {score:.0% if score else 'N/A':<12}"
            )

    return "\n".join(lines)


def get_template(name: str) -> jinja2.Template:
    """Load a Jinja2 template from the templates directory."""
    template_dir = Path(__file__).parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        autoescape=True,
    )
    return env.get_template(name)


def generate_email(results: list[CameraResult]) -> str:
    """Format report as HTML with embedded images for email."""
    template = get_template("email.html.jinja")
    return template.render(results=results)
