import json
from collections.abc import Callable
from io import BytesIO
from typing import Any, NotRequired, TypedDict

import clip
import requests
import torch
from PIL import Image


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
    html_parts: list[str] = [
        "<html><body>",
        "<h2>Snow on Road Report</h2>",
        "<table border='1' cellpadding='8' cellspacing='0'>",
        "<tr><th>ID</th><th>Name</th><th>Image</th>",
    ]
    for label in LABELS:
        html_parts.append(f"<th>{label}</th>")
    html_parts.append("</tr>")

    for result in results:
        html_parts.append("<tr>")
        html_parts.append(f"<td>{result['id']}</td>")
        html_parts.append(f"<td>{result['name']}</td>")

        if result["error"]:
            html_parts.append("<td>Error</td>")
            for _ in LABELS:
                html_parts.append("<td>Error</td>")
        else:
            cid = f"camera_{result['id']}"
            html_parts.append(f"<td><img src='cid:{cid}' width='320'></td>")
            probs = result["probabilities"]
            assert probs is not None
            for label in LABELS:
                prob = probs[label]
                html_parts.append(f"<td>{prob:.2%}</td>")

        html_parts.append("</tr>")

    html_parts.append("</table></body></html>")
    return "".join(html_parts)


def generate_web_page(results: list[CameraResult]) -> str:
    import base64
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html_parts: list[str] = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Snow on Road Report</title>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }",
        "h1 { color: #333; }",
        ".timestamp { color: #666; margin-bottom: 20px; }",
        "table { border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }",
        "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
        "th { background: #4a90d9; color: white; }",
        "tr:nth-child(even) { background: #f9f9f9; }",
        "img { max-width: 320px; height: auto; }",
        ".high-prob { background: #c8e6c9 !important; font-weight: bold; }",
        ".error { color: #d32f2f; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Snow on Road Report</h1>",
        f"<p class='timestamp'>Generated: {timestamp}</p>",
        "<table>",
        "<tr><th>ID</th><th>Name</th><th>Image</th>",
    ]
    for label in LABELS:
        html_parts.append(f"<th>{label}</th>")
    html_parts.append("</tr>")

    for result in results:
        html_parts.append("<tr>")
        html_parts.append(f"<td>{result['id']}</td>")
        html_parts.append(f"<td>{result['name']}</td>")

        if result["error"]:
            html_parts.append("<td class='error'>Error</td>")
            for _ in LABELS:
                html_parts.append("<td class='error'>Error</td>")
        else:
            image_bytes = result.get("image_bytes")
            if image_bytes:
                b64 = base64.b64encode(image_bytes).decode("utf-8")
                html_parts.append(f"<td><img src='data:image/jpeg;base64,{b64}'></td>")
            else:
                html_parts.append("<td>No image</td>")

            probs = result["probabilities"]
            assert probs is not None
            for label in LABELS:
                prob = probs[label]
                cell_class = "high-prob" if prob >= 0.7 else ""
                html_parts.append(f"<td class='{cell_class}'>{prob:.2%}</td>")

        html_parts.append("</tr>")

    html_parts.append("</table>")
    html_parts.append("</body></html>")
    return "".join(html_parts)
