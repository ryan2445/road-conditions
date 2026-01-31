import base64
import json
from collections.abc import Callable
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import clip
import jinja2
import requests
import torch
from PIL import Image


def _b64encode(data: bytes) -> str:
    """Jinja2 filter to base64 encode bytes."""
    return base64.b64encode(data).decode("utf-8")


def get_template(name: str) -> jinja2.Template:
    """Load a Jinja2 template from the templates directory."""
    template_dir = Path(__file__).parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        autoescape=True,
    )
    env.filters["b64encode"] = _b64encode
    return env.get_template(name)


class CameraConfig(TypedDict):
    id: str
    name: str


class CameraResult(TypedDict):
    id: str
    name: str
    error: bool
    probabilities: dict[str, float] | None
    image_bytes: NotRequired[bytes]


LABELS: list[str] = ["a plowed road", "a clear road", "a dry road"]


def load_model() -> (
    tuple[Any, Callable[[Image.Image], torch.Tensor], torch.Tensor, str]
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device, download_root="/tmp")
    text = clip.tokenize(LABELS).to(device)
    return model, preprocess, text, device


def load_cameras(path: str = "cameras.json") -> dict[str, list[CameraConfig]]:
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]


def check_cameras(
    model: Any,
    preprocess: Callable[[Image.Image], torch.Tensor],
    text: torch.Tensor,
    device: str,
    cameras: list[CameraConfig],
) -> list[CameraResult]:
    results: list[CameraResult] = []

    for camera in cameras:
        camera_id = camera["id"]
        camera_name = camera["name"]

        url = f"https://nvroads.com/map/Cctv/{camera_id}"
        response = requests.get(url)

        if response.status_code != 200:
            results.append(
                {
                    "id": camera_id,
                    "name": camera_name,
                    "error": True,
                    "probabilities": None,
                }
            )
            continue

        image_bytes = response.content
        image = Image.open(BytesIO(image_bytes))
        image_tensor = preprocess(image).unsqueeze(0).to(device)

        with torch.no_grad():
            logits_per_image, _ = model(image_tensor, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        results.append(
            {
                "id": camera_id,
                "name": camera_name,
                "error": False,
                "probabilities": {
                    label: float(prob) for label, prob in zip(LABELS, probs)
                },
                "image_bytes": image_bytes,
            }
        )

    return results


def format_report(results: list[CameraResult]) -> str:
    label_widths = [max(len(label), 8) + 2 for label in LABELS]

    lines: list[str] = []
    header = f"{'ID':<8} {'Name':<30} " + " ".join(
        f"{label:<{w}}" for label, w in zip(LABELS, label_widths)
    )
    lines.append(header)
    lines.append("-" * len(header))

    for result in results:
        if result["error"]:
            error_cols = " ".join(f"{'Error':<{w}}" for w in label_widths)
            lines.append(f"{result['id']:<8} {result['name']:<30} {error_cols}")
        else:
            probs = result["probabilities"]
            assert probs is not None
            prob_cols = " ".join(
                f"{probs[label]:.2%}".ljust(w) for label, w in zip(LABELS, label_widths)
            )
            lines.append(f"{result['id']:<8} {result['name']:<30} {prob_cols}")

    return "\n".join(lines)


def generate_email(results: list[CameraResult]) -> str:
    """Format report as HTML with embedded images for email."""
    template = get_template("email.html.jinja")
    return template.render(results=results, labels=LABELS)


def generate_web_page(results: list[CameraResult]) -> str:
    """Format report as standalone HTML page with base64 images."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    template = get_template("web_page.html.jinja")
    return template.render(results=results, labels=LABELS, timestamp=timestamp)
