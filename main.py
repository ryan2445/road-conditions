import torch
import clip
from PIL import Image


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    image = (
        preprocess(Image.open("/Users/ryan/Downloads/5108.jpg")).unsqueeze(0).to(device)
    )
    text = clip.tokenize(["dry road", "snowy road"]).to(device)

    with torch.no_grad():
        logits_per_image, _ = model(image, text)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()

    print("Label probs:", probs)


if __name__ == "__main__":
    main()
