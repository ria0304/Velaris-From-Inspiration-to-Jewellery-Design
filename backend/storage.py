"""In-memory saved-designs cache. POST to upsert, GET to list.

Lives only for the lifetime of the running process — there's no database
here, just a session-scoped cache, matching the original behaviour."""

import random
from typing import List

from fastapi import APIRouter, Body

router = APIRouter()

_local_saved: List[dict] = []


@router.post("/api/save-design")
def save_design(design: dict = Body(...)) -> dict:
    if "id" not in design or not design["id"]:
        design["id"] = f"vel-{random.randint(100000, 999999)}"

    for i, item in enumerate(_local_saved):
        if item.get("id") == design["id"]:
            _local_saved[i] = design
            return {"success": True, "id": design["id"], "totalCount": len(_local_saved)}

    _local_saved.append(design)
    return {"success": True, "id": design["id"], "totalCount": len(_local_saved)}


@router.get("/api/saved-designs")
def get_saved_designs() -> List[dict]:
    return _local_saved
