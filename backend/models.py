from typing import NotRequired, TypedDict


class CameraConfig(TypedDict):
    id: str
    name: str
    stream: NotRequired[str]


class CameraResult(TypedDict):
    id: str
    name: str
    error: bool
    error_message: NotRequired[str | None]
    image_bytes: NotRequired[bytes]


class RoadConditionAlert(TypedDict):
    roadway: str
    description: str
    condition: str
    secondaryConditions: list[str]
    lastUpdated: str

