from config import get_vision_provider_name, load_cameras
from camera_sources import fetch_camera_image
from models import CameraConfig, CameraResult, VisionProvider
from providers import ClaudeProvider, GeminiProvider, OpenAIProvider

ProviderFactory = type[VisionProvider]

PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def load_provider() -> VisionProvider:
    """Instantiate a vision provider based on the VISION_PROVIDER env var."""
    name = get_vision_provider_name()
    try:
        provider_factory = PROVIDER_FACTORIES[name]
    except KeyError as error:
        raise ValueError(f"Unknown vision provider: {name}") from error
    return provider_factory()


def collect_camera_results(
    provider: VisionProvider,
    cameras: list[CameraConfig],
) -> list[CameraResult]:
    results: list[CameraResult] = []

    for camera in cameras:
        image_result = _fetch_camera_result(camera)
        if image_result["error"]:
            results.append(image_result)
            continue

        image_bytes = image_result.get("image_bytes")
        if not image_bytes:
            results.append(_error_result(camera, "no image data"))
            continue
        # try:
        #     analysis = provider.analyze_image(image_bytes)
        # except Exception as error:
        #     results.append(_error_result(camera, f"analysis failed: {error}"))
        #     continue

        results.append(
            {
                "id": camera["id"],
                "name": camera["name"],
                "error": False,
                "clearness_score": None,
                "summary": None,
                "image_bytes": image_bytes,
            }
        )

    return results


def run_camera_analysis(group: str = "mt_rose") -> list[CameraResult]:
    provider = load_provider()
    cameras_by_group = load_cameras()
    return collect_camera_results(provider, cameras_by_group[group])


def _fetch_camera_result(camera: CameraConfig) -> CameraResult:
    try:
        image_bytes = fetch_camera_image(camera)
    except Exception as error:
        return _error_result(camera, f"image fetch failed: {error}")

    return {
        "id": camera["id"],
        "name": camera["name"],
        "error": False,
        "clearness_score": None,
        "summary": None,
        "image_bytes": image_bytes,
    }


def _error_result(camera: CameraConfig, message: str) -> CameraResult:
    return {
        "id": camera["id"],
        "name": camera["name"],
        "error": True,
        "clearness_score": None,
        "summary": None,
        "error_message": message,
    }
