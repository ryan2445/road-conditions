import json
import re
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import NotRequired, TypedDict
from urllib.parse import urljoin

import av
import clip
import jinja2
import requests
import torch
from PIL import Image
from clip.model import CLIP


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


SAFE_PROMPTS: list[str] = [
    "a photo of a clear dry road",
    "a photo of a dry highway with good visibility",
    "a photo of clear driving conditions",
    "a traffic camera view of a clear road",
]

UNSAFE_PROMPTS: list[str] = [
    "a photo of a snow-covered road",
    "a photo of an icy road",
    "a photo of a foggy road with low visibility",
    "a photo of a wet road in heavy rain",
    "a photo of a flooded road",
    "a photo of dangerous winter driving conditions",
    "a photo of poor visibility on a highway",
]


def load_model() -> (
    tuple[CLIP, Callable[[Image.Image], torch.Tensor], torch.Tensor, torch.Tensor, str]
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device, download_root="/tmp")

    with torch.no_grad():
        safe_text = clip.tokenize(SAFE_PROMPTS).to(device)
        unsafe_text = clip.tokenize(UNSAFE_PROMPTS).to(device)
        safe_features = model.encode_text(safe_text)
        safe_features /= safe_features.norm(dim=-1, keepdim=True)
        unsafe_features = model.encode_text(unsafe_text)
        unsafe_features /= unsafe_features.norm(dim=-1, keepdim=True)

    return model, preprocess, safe_features, unsafe_features, device


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
        image.save(output, format="JPEG", quality=85)
        break
    container.close()

    return output.getvalue()


def check_cameras(
    model: CLIP,
    preprocess: Callable[[Image.Image], torch.Tensor],
    safe_features: torch.Tensor,
    unsafe_features: torch.Tensor,
    device: str,
    cameras: list[CameraConfig],
) -> list[CameraResult]:
    results: list[CameraResult] = []
    preprocessed: list[tuple[int, CameraConfig, bytes, torch.Tensor]] = []

    # Phase 1: Fetch and preprocess all images
    for idx, camera in enumerate(cameras):
        camera_id = camera["id"]
        camera_name = camera["name"]
        stream_url = camera.get("stream")

        try:
            if stream_url:
                image_bytes = fetch_hls_frame(stream_url)
            else:
                # Fallback to CCTV endpoint
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

        try:
            image = Image.open(BytesIO(image_bytes))
            image_tensor = preprocess(image).unsqueeze(0).to(device)
        except Exception as e:
            print(f"Error processing image for camera {camera_id} ({camera_name}): {e}")
            results.append(
                {
                    "id": camera_id,
                    "name": camera_name,
                    "error": True,
                    "clearness_score": None,
                }
            )
            continue

        preprocessed.append((idx, camera, image_bytes, image_tensor))

    # Phase 2: Batch encode all images
    if preprocessed:
        batch = torch.cat([t for _, _, _, t in preprocessed], dim=0)
        with torch.no_grad():
            image_features = model.encode_image(batch)
            image_features /= image_features.norm(dim=-1, keepdim=True)

        # Phase 3: Compute scores per image using pre-computed text features
        for i, (idx, camera, image_bytes, _) in enumerate(preprocessed):
            try:
                with torch.no_grad():
                    # Get this image's features (1xD)
                    img_feat = image_features[i : i + 1]

                    # Compute similarities (img_feat: 1xD, text_features: NxD)
                    safe_similarities = (img_feat @ safe_features.T).squeeze(0)
                    unsafe_similarities = (img_feat @ unsafe_features.T).squeeze(0)

                    # Average within each category
                    avg_safe = safe_similarities.mean()
                    avg_unsafe = unsafe_similarities.mean()

                    # Scale by CLIP's logit_scale (~100)
                    scores = torch.stack([avg_safe, avg_unsafe]) * 100.0
                    # Apply softmax to get probability
                    probs = torch.softmax(scores, dim=0)
                    clearness_score = probs[0].cpu().item()

                results.append(
                    {
                        "id": camera["id"],
                        "name": camera["name"],
                        "error": False,
                        "clearness_score": float(clearness_score),
                        "image_bytes": image_bytes,
                    }
                )
            except Exception as e:
                print(
                    f"Error computing score for camera {camera['id']} ({camera['name']}): {e}"
                )
                results.append(
                    {
                        "id": camera["id"],
                        "name": camera["name"],
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
            assert score is not None
            lines.append(f"{result['id']:<8} {result['name']:<30} {score:.0%}")

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
