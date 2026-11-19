import logging

import requests

from models import RoadConditionAlert

logger = logging.getLogger(__name__)

NVROADS_URL = "https://www.nvroads.com/List/GetData/RoadConditions"
PAGE_SIZE = 100
TARGET_AREAS = {"Reno"}

# Map NV Roads roadway names to camera group keys
ROADWAY_TO_GROUPS: dict[str, list[str]] = {
    "SR-431 (Mt. Rose Hwy)": ["mt_rose"],
    "I-580": ["washoe_lake", "south_reno"],
    "SR-341": ["south_reno"],
    "SR-341 (Greiger Grade Rd)": ["south_reno"],
    "SR-659 (McCarran Blvd)": ["south_reno"],
    "I-80": ["i80"],
}


def _fetch_all_records() -> list[dict]:
    """Fetch all road condition records from NV Roads using pagination."""
    records: list[dict] = []
    start = 0

    while True:
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
                "start": start,
                "length": PAGE_SIZE,
                "search": {"value": ""},
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        page = data.get("data", [])
        if not page:
            break

        records.extend(page)
        start += len(page)

        total = data.get("recordsTotal")
        if len(page) < PAGE_SIZE or (isinstance(total, int) and start >= total):
            break

    return records


def fetch_road_conditions() -> dict[str, list[RoadConditionAlert]]:
    """Fetch road conditions from NV Roads and group by camera group key."""
    try:
        records = _fetch_all_records()
    except Exception:
        logger.exception("Failed to fetch road conditions from NV Roads")
        return {}

    results: dict[str, list[RoadConditionAlert]] = {}

    for record in records:
        if record.get("area") not in TARGET_AREAS:
            continue

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
