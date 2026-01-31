import json
import requests
import torch
import clip
from PIL import Image
from io import BytesIO

LABELS = ["a plowed road", "a clear road", "a dry road"]


def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    text = clip.tokenize(LABELS).to(device)
    return model, preprocess, text, device


def load_cameras(path="cameras.json"):
    with open(path) as f:
        return json.load(f)


def check_cameras(model, preprocess, text, device, cameras):
    results = []

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

        image = Image.open(BytesIO(response.content))
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
            }
        )

    return results


def format_report(results):
    label_widths = [max(len(label), 8) + 2 for label in LABELS]

    lines = []
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
            prob_cols = " ".join(
                f"{probs[label]:.2%}".ljust(w) for label, w in zip(LABELS, label_widths)
            )
            lines.append(f"{result['id']:<8} {result['name']:<30} {prob_cols}")

    return "\n".join(lines)
