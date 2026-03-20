import json
import os
from pathlib import Path

from models import CameraConfig

DEFAULT_CAMERA_PATH = Path(__file__).with_name("cameras.json")


def load_cameras(path: str | Path = DEFAULT_CAMERA_PATH) -> dict[str, list[CameraConfig]]:
    with Path(path).open() as file:
        return json.load(file)  # type: ignore[no-any-return]


def get_vision_provider_name() -> str:
    return os.environ.get("VISION_PROVIDER", "gemini").lower()
