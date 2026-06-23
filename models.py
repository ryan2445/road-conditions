from typing import NotRequired, Protocol, TypedDict


class CameraConfig(TypedDict):
    id: str
    name: str
    stream: NotRequired[str]


class CameraResult(TypedDict):
    id: str
    name: str
    error: bool
    clearness_score: float | None
    summary: NotRequired[str | None]
    error_message: NotRequired[str | None]
    image_bytes: NotRequired[bytes]


class AnalysisResult(TypedDict):
    clearness_score: float  # 0.0 (dangerous) to 1.0 (clear/dry)
    summary: str  # Brief text description


class RoadConditionAlert(TypedDict):
    roadway: str
    description: str
    condition: str
    secondaryConditions: list[str]
    lastUpdated: str


class VisionProvider(Protocol):
    def analyze_image(self, image_bytes: bytes) -> AnalysisResult: ...


ANALYSIS_PROMPT = """Analyze this traffic camera image and assess road conditions.

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
