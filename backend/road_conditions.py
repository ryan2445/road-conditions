import logging

import requests

from models import RoadConditionAlert

logger = logging.getLogger(__name__)

NVROADS_URL = "https://www.nvroads.com/List/GetData/RoadConditions"

# Map NV Roads roadway names to camera group keys
ROADWAY_TO_GROUPS: dict[str, list[str]] = {
    "SR-431 (Mt. Rose Hwy)": ["mt_rose"],
    "I-580": ["washoe_lake", "south_reno"],
    "SR-341": ["south_reno"],
    "SR-659 (McCarran Blvd)": ["south_reno"],
}


def fetch_road_conditions() -> dict[str, list[RoadConditionAlert]]:
    """Fetch road conditions from NV Roads and group by camera group key."""
    try:
        resp = requests.post(
            NVROADS_URL,
            json={
                "columns": [
                    {"data": "roadway"},
                    {"data": "description"},
                    {"data": "primaryCondition"},
                    {"data": "secondaryConditions"},
                    {"data": "lastUpdated"},
                ],
                "order": [],
                "start": 0,
                "length": 500,
                "search": {"value": ""},
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception("Failed to fetch road conditions from NV Roads")
        return {}

    results: dict[str, list[RoadConditionAlert]] = {}

    for record in data.get("data", []):
        roadway = record.get("roadway", "")
        groups = ROADWAY_TO_GROUPS.get(roadway)
        if not groups:
            continue

        condition = record.get("primaryCondition", "No Report")
        if condition == "No Report":
            continue

        secondary = record.get("secondaryConditions") or []
        if isinstance(secondary, str):
            secondary = [s.strip() for s in secondary.split(",") if s.strip()]

        alert: RoadConditionAlert = {
            "roadway": roadway,
            "description": record.get("description", ""),
            "condition": condition,
            "secondaryConditions": secondary,
            "lastUpdated": record.get("lastUpdated", ""),
        }

        for group in groups:
            results.setdefault(group, []).append(alert)

    return results
