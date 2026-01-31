import json
import requests
import torch
import clip
from PIL import Image
from io import BytesIO


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    labels = ["a snow-covered road", "a snowy road"]
    text = clip.tokenize(labels).to(device)

    with open("cameras.json") as f:
        cameras = json.load(f)

    label_widths = [max(len(label), 8) + 2 for label in labels]
    header = f"{'ID':<8} {'Name':<30} " + " ".join(
        f"{label:<{w}}" for label, w in zip(labels, label_widths)
    )
    print(header)
    print("-" * len(header))

    for camera in cameras["mt_rose"]:
        camera_id = camera["id"]
        camera_name = camera["name"]

        url = f"https://nvroads.com/map/Cctv/{camera_id}"
        response = requests.get(url)

        if response.status_code != 200:
            error_cols = " ".join(f"{'Error':<{w}}" for w in label_widths)
            print(f"{camera_id:<8} {camera_name:<30} {error_cols}")
            continue

        image = Image.open(BytesIO(response.content))
        image_tensor = preprocess(image).unsqueeze(0).to(device)

        with torch.no_grad():
            logits_per_image, _ = model(image_tensor, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        prob_cols = " ".join(
            f"{prob:.2%}".ljust(w) for prob, w in zip(probs, label_widths)
        )
        print(f"{camera_id:<8} {camera_name:<30} {prob_cols}")


if __name__ == "__main__":
    main()
